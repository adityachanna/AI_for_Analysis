import json
import os
from typing import Any


def analyze_registered_media(title: str, sport: str | None, keyframes: list[dict]) -> dict[str, Any]:
    if os.getenv("GEMINI_API_KEY"):
        # The MVP keeps network calls optional. This structure mirrors the Gemini output contract.
        provider = "gemini-configured"
    else:
        provider = "deterministic-fallback"

    sport_label = sport or "sports"
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
    passport_text = (
        f"This official {sport_label} video titled '{title}' contains scene-by-scene sports highlight action. "
        "Key events are represented by extracted keyframes, commentary placeholders, scoreboard/on-screen text cues, "
        "and stable semantic tags designed to survive re-encoding, cropping, color changes, and screen recapture."
    )
    return {
        "provider": provider,
        "summary": f"{title} appears to be an official {sport_label} highlight with reusable visual fingerprints.",
        "content_passport": shot_descriptions,
        "passport_text": passport_text,
        "passport_embedding": deterministic_embedding(passport_text),
        "entities": [sport_label, "official rights holder footage", "highlight sequence"],
        "visual_description": f"Official {sport_label} clip with stable scene, player, scoreboard, and motion cues.",
        "transcript": "Transcript placeholder: crowd noise, commentary, and short highlight callout.",
        "semantic_tags": [sport_label.lower(), "highlight", "broadcast", "rights-managed"],
    }


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
