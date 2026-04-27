import json
import logging
import re
from typing import Any

from ..config import settings

logger = logging.getLogger(__name__)

_MODEL_TEXT = "gemma-4-31b-it"
_MODEL_VIDEO = "gemini-3-flash-preview"
_MODEL_MULTIMODAL = "gemini-3.1-flash-lite-preview"


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
        "passport_embedding": embed_text(
            passport_text,
            vector_id=f"asset-{title.lower().replace(' ', '-')[:40]}",
            metadata={"type": "asset", "title": title, "sport": sport_label or ""},
        ),
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
        "embedding": embed_text(
            description,
            vector_id=f"suspect-{platform.lower().replace(' ', '-')[:20]}-{mutation_type[:20]}",
            metadata={"type": "suspect", "platform": platform, "mutation_type": mutation_type},
        ),
        "graph_metadata": {
            "observable_entities": ["players", "scoreboard", "crowd audio", "broadcast overlay"],
            "mutation_evidence": transform_manifest,
            "distribution_context": {"platform": platform, "risk": "demo_seeded"},
            "ai_summary": description,
        },
    }


def describe_clip_from_keyframes(
    keyframes: list[dict],
    asset_analysis: dict,
    mutation_type: str,
    platform: str,
) -> dict[str, Any]:
    """Generate AI description for a demo clip variant using real extracted keyframes."""
    transform_manifest = {
        "variant_keyframe_count": len(keyframes),
        "timestamps_ms": [kf.get("timestamp_ms", 0) for kf in keyframes[:5]],
        "mutation_type": mutation_type,
        "extraction_method": keyframes[0].get("semantic_metadata", {}).get("extraction", "unknown") if keyframes else "unknown",
    }

    prompt = (
        f"You are a copyright investigator analyzing a {mutation_type.replace('_', ' ')} variant "
        f"of a sports broadcast clip posted on {platform}. "
        f"The clip has {len(keyframes)} keyframes at timestamps: "
        f"{[kf.get('timestamp_ms', 0) for kf in keyframes[:5]]}ms. "
        "In 2 sentences, describe what visual and semantic evidence of the original broadcast persists, "
        "and what specific transformations were applied. Be concrete and realistic."
    )
    gemini_text = _try_gemini_text(prompt)

    base = analyze_demo_clip(asset_analysis, mutation_type, platform, transform_manifest)
    if gemini_text:
        base["provider"] = "gemini"
        base["description"] = gemini_text
        base["graph_metadata"]["ai_summary"] = gemini_text

    return base


def analyze_graph_with_gemini(nodes: list[dict], edges: list[dict]) -> dict[str, Any]:
    """Analyze violation graph topology with Gemini to produce risk assessment and recommended actions."""
    domains = [n["label"] for n in nodes if n.get("type") == "DOMAIN"]
    suspects = [n for n in nodes if n.get("type") == "SUSPECT"]
    platform_count = len(domains)
    suspect_count = len(suspects)

    mutation_types: list[str] = []
    for n in suspects:
        meta = n.get("metadata") or {}
        if isinstance(meta, dict):
            mt = meta.get("mutation_type")
            if mt and mt not in mutation_types:
                mutation_types.append(mt)

    if suspect_count == 0:
        return {
            "patterns": [],
            "risk_level": "LOW",
            "recommended_action": "No violations detected yet. Register media and run a scan.",
            "distribution_fingerprint": "No distribution data available.",
        }

    prompt = (
        f"A copyright violation graph has {suspect_count} suspected pirated clips across "
        f"{platform_count} platform(s) ({', '.join(domains[:5])}). "
        f"Mutation types: {', '.join(mutation_types[:5]) or 'unknown'}. "
        "Respond with a JSON object (no markdown) with exactly these keys: "
        "patterns (array of strings describing distribution patterns), "
        "risk_level (one of: LOW, MEDIUM, HIGH, CRITICAL), "
        "recommended_action (string with specific DMCA/takedown advice), "
        "distribution_fingerprint (string summarising spread)."
    )
    gemini_text = _try_gemini_text(prompt)
    if gemini_text:
        try:
            json_match = re.search(r"\{.*\}", gemini_text, re.DOTALL)
            if json_match:
                parsed = json.loads(json_match.group())
                # Validate required keys are present
                if all(k in parsed for k in ("patterns", "risk_level", "recommended_action", "distribution_fingerprint")):
                    return parsed
        except Exception as e:
            logger.warning(f"Failed to parse Gemini graph analysis JSON: {e}")

    # Deterministic fallback
    risk_level = "CRITICAL" if suspect_count >= 4 else "HIGH" if suspect_count >= 2 else "MEDIUM"
    return {
        "patterns": [
            f"{suspect_count} pirated clip(s) detected across {platform_count} platform(s)",
            f"Dominant mutation types: {', '.join(mutation_types[:3]) or 'unknown'}",
        ],
        "risk_level": risk_level,
        "recommended_action": (
            f"File DMCA takedowns on {platform_count} platform(s): {', '.join(domains[:3])}."
            if domains else "Monitor distribution channels for further spread."
        ),
        "distribution_fingerprint": (
            f"{suspect_count} variant(s) across {platform_count} platform(s) "
            f"using {len(mutation_types)} distinct mutation strategy(ies)."
        ),
    }


def embed_text(
    text: str,
    dimensions: int | None = None,
    vector_id: str | None = None,
    metadata: dict | None = None,
) -> list[float]:
    """
    Generate a text embedding using gemini-embedding-2.

    If vector_id is provided, the resulting embedding is automatically
    upserted into the Pinecone index (fire-and-forget; failure is logged,
    not raised).
    """
    if dimensions is None:
        dimensions = settings.pinecone_dimension

    embedding: list[float] = []

    if settings.gemini_api_key:
        for model in ("gemini-embedding-2", "text-embedding-004", "gemini-embedding-001"):
            try:
                from google import genai
                from google.genai import types

                client = genai.Client(api_key=settings.gemini_api_key)
                result = client.models.embed_content(
                    model=model,
                    contents=text,
                    config=types.EmbedContentConfig(output_dimensionality=dimensions),
                )
                embedding = [round(float(v), 4) for v in result.embeddings[0].values]
                break
            except Exception as e:
                logger.warning(f"Embedding model {model!r} failed: {e}")
                continue

    if not embedding:
        embedding = deterministic_embedding(text, dimensions)

    # Upsert into Pinecone when a vector_id is provided
    if vector_id:
        try:
            from . import pinecone_service
            idx = pinecone_service.get_index()
            pinecone_service.upsert_vector(idx, vector_id, embedding, metadata or {})
        except Exception as exc:  # noqa: BLE001
            logger.warning("Pinecone upsert skipped for '%s': %s", vector_id, exc)

    return embedding


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
        response = client.models.generate_content(model=_MODEL_TEXT, contents=prompt)
        text = getattr(response, "text", "") or ""
        return text.strip() or None
    except Exception as e:
        logger.warning(f"Text generation failed ({_MODEL_TEXT}): {e}")
        return None


def _try_gemini_video(contents: Any) -> str | None:
    """Send video content (bytes, Part, or mixed list) to the video-understanding model."""
    if not settings.gemini_api_key:
        return None
    try:
        from google import genai

        client = genai.Client(api_key=settings.gemini_api_key)
        response = client.models.generate_content(model=_MODEL_VIDEO, contents=contents)
        text = getattr(response, "text", "") or ""
        return text.strip() or None
    except Exception as e:
        logger.warning(f"Video understanding failed ({_MODEL_VIDEO}): {e}")
        return None


def _try_gemini_multimodal(contents: Any) -> str | None:
    """Send image/multimodal content (not video) to the multimodal model."""
    if not settings.gemini_api_key:
        return None
    try:
        from google import genai

        client = genai.Client(api_key=settings.gemini_api_key)
        response = client.models.generate_content(model=_MODEL_MULTIMODAL, contents=contents)
        text = getattr(response, "text", "") or ""
        return text.strip() or None
    except Exception as e:
        logger.warning(f"Multimodal generation failed ({_MODEL_MULTIMODAL}): {e}")
        return None


def deterministic_embedding(text: str, dimensions: int | None = None) -> list[float]:
    if dimensions is None:
        dimensions = settings.pinecone_dimension
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
