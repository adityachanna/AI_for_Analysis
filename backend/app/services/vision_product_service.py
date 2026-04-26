from ..config import settings


VISION_AI_OFFERINGS = [
    {
        "product": "Cloud Vision API",
        "role": "keyframe_labels_ocr_logo_detection",
        "best_for": "Quick prebuilt labels, OCR, logos, safe-search style metadata on extracted keyframes.",
        "used_in_sentinelai": True,
        "why": "Low-latency frame evidence for graph nodes and confidence explanations.",
    },
    {
        "product": "Video Intelligence API",
        "role": "video_shots_labels_text_speech",
        "best_for": "Video-level shot detection, labels, text recognition, logo recognition, and speech transcription.",
        "used_in_sentinelai": True,
        "why": "Source transcript and video context that survive re-encoding or screen recording.",
    },
    {
        "product": "Gemini on Vertex AI / Gemini API",
        "role": "multimodal_content_passport_and_reasoning",
        "best_for": "Semantic reasoning across visual, text, and audio-derived evidence.",
        "used_in_sentinelai": True,
        "why": "Creates the Content Passport and explains Stage C mutations.",
    },
    {
        "product": "Vertex AI Vision",
        "role": "streaming_video_pipeline_future_upgrade",
        "best_for": "Managed stream ingestion, live analytics, and Vision Warehouse search.",
        "used_in_sentinelai": False,
        "why": "Roadmap path for continuous platform monitoring after the MVP URL/demo scan flow.",
    },
    {
        "product": "Imagen on Vertex AI",
        "role": "visual_captioning_optional_upgrade",
        "best_for": "Image captions, image descriptions, image generation/editing.",
        "used_in_sentinelai": False,
        "why": "Gemini already covers content-passport reasoning for this MVP.",
    },
    {
        "product": "Document AI",
        "role": "document_rights_metadata_future_upgrade",
        "best_for": "Contracts, takedown notices, invoices, and scanned rights documents.",
        "used_in_sentinelai": False,
        "why": "Useful for future rights-management paperwork, not core video matching.",
    },
]


def registration_vision_plan(keyframe_count: int, demo_clip_count: int) -> dict:
    cloud_vision_features_per_frame = 4
    cloud_vision_units = keyframe_count * cloud_vision_features_per_frame
    video_intelligence_jobs = 1
    gemini_passport_calls = 1
    gemini_demo_clip_calls = demo_clip_count
    return {
        "selected_products": [item for item in VISION_AI_OFFERINGS if item["used_in_sentinelai"]],
        "roadmap_products": [item for item in VISION_AI_OFFERINGS if not item["used_in_sentinelai"]],
        "enabled": {
            "cloud_vision_api": settings.vision_ai_enabled,
            "video_intelligence_api": settings.video_intelligence_enabled,
            "gemini": bool(settings.gemini_api_key),
            "gcs": settings.use_gcs,
            "firebase_auth_required": settings.firebase_auth_required,
        },
        "billable_unit_estimate": {
            "cloud_vision_feature_units": cloud_vision_units,
            "video_intelligence_jobs": video_intelligence_jobs,
            "gemini_passport_calls": gemini_passport_calls,
            "gemini_demo_clip_enrichment_calls": gemini_demo_clip_calls,
        },
        "estimated_cost_usd": _estimate_registration_cost(cloud_vision_units, video_intelligence_jobs, gemini_passport_calls, gemini_demo_clip_calls),
        "note": "Cloud Vision has a monthly free tier for feature units; exact production cost depends on enabled APIs, region, model, and current Google Cloud pricing.",
    }


def capabilities() -> dict:
    return {
        "system": "SentinelAI",
        "vision_ai_strategy": "Use fast, ready-to-use Vision AI for evidence extraction and Gemini for semantic reasoning.",
        "offerings": VISION_AI_OFFERINGS,
        "current_backend_flags": {
            "VISION_AI_ENABLED": settings.vision_ai_enabled,
            "VIDEO_INTELLIGENCE_ENABLED": settings.video_intelligence_enabled,
            "USE_GCS": settings.use_gcs,
            "FIREBASE_AUTH_REQUIRED": settings.firebase_auth_required,
            "FIREBASE_PROJECT_ID": settings.firebase_project_id,
            "FIREBASE_STORAGE_BUCKET": settings.firebase_storage_bucket,
        },
    }


def _estimate_registration_cost(cloud_vision_units: int, video_jobs: int, gemini_passport_calls: int, demo_calls: int) -> float:
    cloud_vision = cloud_vision_units * 0.0015
    video_intelligence = video_jobs * 0.01
    gemini = (gemini_passport_calls * 0.01) + (demo_calls * 0.004)
    return round(cloud_vision + video_intelligence + gemini, 4)
