from pathlib import Path
from typing import Any

from ..config import settings


def analyze_video_evidence(path: Path, gcs_uri: str | None, keyframes: list[dict], title: str, sport: str | None) -> dict:
    vision = _analyze_keyframes_with_vision_api(keyframes)
    video = _analyze_video_with_video_intelligence(gcs_uri, title, sport)
    fallback = vision["provider"] == "deterministic-fallback" and video["provider"] == "deterministic-fallback"
    return {
        "provider": "deterministic-fallback" if fallback else "google-cloud",
        "source": str(path),
        "gcs_uri": gcs_uri,
        "vision": vision,
        "video_intelligence": video,
        "graph_hints": _graph_hints(vision, video),
    }


def enrich_keyframes_with_vision_metadata(keyframes: list[dict], evidence: dict) -> list[dict]:
    frame_insights = evidence.get("vision", {}).get("keyframe_insights", [])
    by_index = {item["frame_index"]: item for item in frame_insights}
    enriched = []
    for frame in keyframes:
        metadata = dict(frame.get("semantic_metadata", {}))
        metadata["vision_ai"] = by_index.get(frame["frame_index"], {})
        enriched.append({**frame, "semantic_metadata": metadata})
    return enriched


def _analyze_keyframes_with_vision_api(keyframes: list[dict]) -> dict:
    if settings.vision_ai_enabled:
        try:
            from google.cloud import vision

            client = vision.ImageAnnotatorClient()
            insights = []
            for frame in keyframes[:8]:
                path = frame.get("evidence_path")
                if not path or not Path(path).suffix.lower() in {".jpg", ".jpeg", ".png"}:
                    insights.append(_fallback_frame_insight(frame))
                    continue
                content = Path(path).read_bytes()
                image = vision.Image(content=content)
                response = client.annotate_image(
                    {
                        "image": image,
                        "features": [
                            {"type_": vision.Feature.Type.LABEL_DETECTION, "max_results": 6},
                            {"type_": vision.Feature.Type.TEXT_DETECTION, "max_results": 3},
                            {"type_": vision.Feature.Type.LOGO_DETECTION, "max_results": 3},
                            {"type_": vision.Feature.Type.OBJECT_LOCALIZATION, "max_results": 5},
                        ],
                    }
                )
                insights.append(
                    {
                        "frame_index": frame["frame_index"],
                        "timestamp_ms": frame["timestamp_ms"],
                        "labels": [item.description for item in response.label_annotations],
                        "text": [item.description for item in response.text_annotations[:1]],
                        "logos": [item.description for item in response.logo_annotations],
                        "objects": [item.name for item in response.localized_object_annotations],
                        "provider": "cloud-vision",
                    }
                )
            return {"provider": "cloud-vision", "keyframe_insights": insights}
        except Exception as exc:
            return {
                "provider": "deterministic-fallback",
                "error": str(exc),
                "keyframe_insights": [_fallback_frame_insight(frame) for frame in keyframes[:8]],
            }
    return {
        "provider": "deterministic-fallback",
        "keyframe_insights": [_fallback_frame_insight(frame) for frame in keyframes[:8]],
    }


def _analyze_video_with_video_intelligence(gcs_uri: str | None, title: str, sport: str | None) -> dict:
    if settings.video_intelligence_enabled and gcs_uri and gcs_uri.startswith("gs://"):
        try:
            from google.cloud import videointelligence

            client = videointelligence.VideoIntelligenceServiceClient()
            features = [
                videointelligence.Feature.SHOT_CHANGE_DETECTION,
                videointelligence.Feature.LABEL_DETECTION,
                videointelligence.Feature.TEXT_DETECTION,
                videointelligence.Feature.LOGO_RECOGNITION,
                videointelligence.Feature.SPEECH_TRANSCRIPTION,
            ]
            context = videointelligence.VideoContext(
                speech_transcription_config=videointelligence.SpeechTranscriptionConfig(
                    language_code="en-US",
                    enable_automatic_punctuation=True,
                )
            )
            operation = client.annotate_video(request={"features": features, "input_uri": gcs_uri, "video_context": context})
            result = operation.result(timeout=90)
            annotation = result.annotation_results[0]
            labels = [item.entity.description for item in annotation.segment_label_annotations[:12]]
            text = [item.text for item in annotation.text_annotations[:8]]
            logos = [item.entity.description for item in annotation.logo_recognition_annotations[:8]]
            transcript = " ".join(
                alt.transcript
                for item in annotation.speech_transcriptions[:4]
                for alt in item.alternatives[:1]
            )
            return {
                "provider": "video-intelligence",
                "shot_count": len(annotation.shot_annotations),
                "labels": labels,
                "text": text,
                "logos": logos,
                "transcript": transcript,
            }
        except Exception as exc:
            fallback = _fallback_video_insight(title, sport)
            fallback["error"] = str(exc)
            return fallback
    return _fallback_video_insight(title, sport)


def _fallback_frame_insight(frame: dict) -> dict:
    return {
        "frame_index": frame["frame_index"],
        "timestamp_ms": frame["timestamp_ms"],
        "labels": ["sports", "broadcast", "highlight", "scoreboard"],
        "text": ["score bug or broadcast caption candidate"],
        "logos": ["rights-holder or league logo candidate"],
        "objects": ["person", "sports equipment", "field of play"],
        "provider": "deterministic-fallback",
    }


def _fallback_video_insight(title: str, sport: str | None) -> dict:
    sport_label = sport or "sports"
    return {
        "provider": "deterministic-fallback",
        "shot_count": 8,
        "labels": [sport_label, "sports", "broadcast", "highlight", "crowd"],
        "text": ["scoreboard", "timer", "broadcast lower-third"],
        "logos": ["league logo", "channel bug"],
        "transcript": f"Fallback transcript for {title}: crowd noise, commentary callout, and key {sport_label} play.",
    }


def _graph_hints(vision: dict, video: dict) -> dict[str, Any]:
    labels = set(video.get("labels", []))
    texts = set(video.get("text", []))
    logos = set(video.get("logos", []))
    for frame in vision.get("keyframe_insights", []):
        labels.update(frame.get("labels", []))
        texts.update(frame.get("text", []))
        logos.update(frame.get("logos", []))
    return {
        "entity_nodes": sorted(labels)[:12],
        "text_nodes": sorted(texts)[:8],
        "logo_nodes": sorted(logos)[:8],
        "evidence_edges": ["HAS_LABEL", "HAS_OCR_TEXT", "HAS_LOGO", "HAS_TRANSCRIPT"],
    }
