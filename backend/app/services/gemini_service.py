import json
from typing import Any

from ..config import settings


def analyze_registered_media(
    title: str,
    sport: str | None,
    keyframes: list[dict],
    vision_evidence: dict | None = None,
) -> dict[str, Any]:
    sport_label = sport or "sports"
    vision_evidence = vision_evidence or {}
    gemini_text = _try_gemini_passport(title, sport_label, keyframes, vision_evidence)
    provider = "gemini" if gemini_text else "deterministic-fallback"
    shot_descriptions = [
        {
            "shot": frame["frame_index"] + 1,
            "timestamp_ms": frame["timestamp_ms"],
            "description": (
                f"This {sport_label} highlight segment shows observable broadcast action, scoreboard context, "
                f"crowd audio, and rights-managed visual cues around timestamp {frame['timestamp_ms']}ms."
            ),
        }
        for frame in keyframes[:12]
    ]
    passport_text = gemini_text or (
        f"This official {sport_label} video titled '{title}' contains scene-by-scene sports highlight action. "
        "Key events are represented by extracted keyframes, commentary placeholders, scoreboard/on-screen text cues, "
        "and stable semantic tags designed to survive re-encoding, cropping, color changes, and screen recapture."
    )
    return {
        "provider": provider,
        "summary": f"{title} appears to be an official {sport_label} highlight with reusable visual fingerprints.",
        "content_passport": shot_descriptions,
        "passport_text": passport_text,
        "passport_embedding": embed_text(passport_text),
        "entities": [sport_label, "official rights holder footage", "highlight sequence"],
        "visual_description": f"Official {sport_label} clip with stable scene, player, scoreboard, and motion cues.",
        "transcript": vision_evidence.get("video_intelligence", {}).get(
            "transcript",
            "Transcript placeholder: crowd noise, commentary, and short highlight callout.",
        ),
        "semantic_tags": sorted(
            set(
                [sport_label.lower(), "highlight", "broadcast", "rights-managed"]
                + [label.lower() for label in vision_evidence.get("video_intelligence", {}).get("labels", [])[:8]]
            )
        ),
        "vision_ai": vision_evidence,
        "graph_enrichment": {
            "content_type": "registered_asset",
            "scene_count": len(shot_descriptions),
            "stable_signals": [
                "dhash",
                "synthid",
                "vision_labels",
                "ocr_text",
                "logos",
                "content_passport",
                "speech_transcript",
                "semantic_embedding",
            ],
            "recommended_nodes": [
                "registered_asset",
                "rights_holder",
                "semantic_passport",
                "broadcast_context",
                "vision_label",
                "ocr_text",
                "logo",
            ],
            "vision_graph_hints": vision_evidence.get("graph_hints", {}),
        },
    }


def analyze_demo_clip(asset_analysis: dict, mutation_type: str, platform: str, transform_manifest: dict) -> dict[str, Any]:
    source_tags = asset_analysis.get("semantic_tags", ["highlight", "broadcast"])
    mutation_details = {
        "exact_repost": "same broadcast sequence and near-identical visual identity",
        "cropped_or_reencoded": "vertical crop, bitrate loss, and color remap while preserving action",
        "overlay_or_meme_edit": "caption overlays and stickers covering parts of the frame",
        "screen_recorded_recapture": "display recapture with glare, frame judder, and room audio bleed",
        "audio_or_semantic_reuse": "different pixels but reused commentary and event sequence",
    }.get(mutation_type, "unrelated media")
    prompt_text = (
        f"Suspect clip on {platform}: {mutation_details}. "
        f"Reference passport: {asset_analysis.get('passport_text', asset_analysis.get('summary', 'sports highlight'))}"
    )
    generated = _try_gemini_text(
        "Create compact JSON-like graph enrichment for a suspected copied sports clip. "
        "Include observable_entities, mutation_evidence, distribution_context, and graph_edges. "
        f"Input: {prompt_text}"
    )
    description = generated or (
        f"AI graph enrichment: {platform} candidate shows {mutation_details}. "
        "The clip keeps semantic event order, commentary cues, and broadcast context from the source."
    )
    return {
        "provider": "gemini" if generated else "deterministic-fallback",
        "description": description,
        "semantic_tags": sorted(set(source_tags + [mutation_type, platform.lower().replace(' ', '-')])),
        "embedding": embed_text(description),
        "graph_metadata": {
            "observable_entities": ["players", "scoreboard", "crowd audio", "broadcast overlay"],
            "mutation_evidence": transform_manifest,
            "distribution_context": {"platform": platform, "risk": "demo_seeded"},
            "ai_summary": description,
        },
    }


def embed_text(text: str, dimensions: int = 16) -> list[float]:
    if settings.gemini_api_key:
        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=settings.gemini_api_key)
            result = client.models.embed_content(
                model="gemini-embedding-001",
                contents=text,
                config=types.EmbedContentConfig(output_dimensionality=dimensions),
            )
            embedding = result.embeddings[0].values
            return [round(float(value), 4) for value in embedding]
        except Exception:
            pass
    return deterministic_embedding(text, dimensions)


def _try_gemini_passport(title: str, sport_label: str, keyframes: list[dict], vision_evidence: dict) -> str | None:
    prompt = (
        "Describe only observable actions, named entities, locations, on-screen text, and significant audio events. "
        "Do not speculate. Return a concise content passport that survives cropping, re-encoding, morphing, and recapture. "
        f"Title: {title}. Sport: {sport_label}. Keyframe timestamps: "
        f"{[frame['timestamp_ms'] for frame in keyframes[:12]]}. "
        f"Vision AI evidence: {json.dumps(vision_evidence.get('graph_hints', {}), sort_keys=True)}."
    )
    return _try_gemini_text(prompt)


def _try_gemini_text(prompt: str) -> str | None:
    if not settings.gemini_api_key:
        return None
    try:
        from google import genai

        client = genai.Client(api_key=settings.gemini_api_key)
        response = client.models.generate_content(model="gemini-2.5-flash", contents=prompt)
        text = getattr(response, "text", "") or ""
        return text.strip() or None
    except Exception:
        return None


def deterministic_embedding(text: str, dimensions: int = 16) -> list[float]:
    values = [0.0] * dimensions
    for index, char in enumerate(text.lower()):
        values[index % dimensions] += (ord(char) % 31) / 31
    total = sum(values) or 1.0
    return [round(value / total, 4) for value in values]


def semantic_match(asset_analysis: dict, suspect: dict, visual_confidence: float) -> dict[str, Any]:
    tags = set(asset_analysis.get("semantic_tags", []))
    suspect_tags = set(suspect.get("semantic_tags", []))
    overlap = len(tags & suspect_tags) / max(len(tags | suspect_tags), 1)
    mutation_boost = {
        "cropped_or_reencoded": 0.18,
        "overlay_or_meme_edit": 0.14,
        "screen_recorded_recapture": 0.12,
        "audio_or_semantic_reuse": 0.22,
        "unrelated": -0.25,
        "exact_repost": 0.2,
    }.get(suspect.get("mutation_type"), 0.0)
    score = max(0.0, min(1.0, (overlap * 0.55) + visual_confidence + mutation_boost))
    return {
        "confidence": round(score, 3),
        "explanation": (
            f"Semantic comparison found {len(tags & suspect_tags)} overlapping media tags. "
            f"Classified as {suspect.get('mutation_type')} with visual confidence {visual_confidence:.2f}."
        ),
    }


def dumps_analysis(analysis: dict) -> str:
    return json.dumps(analysis, sort_keys=True)
