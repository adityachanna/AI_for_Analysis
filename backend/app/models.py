from pydantic import BaseModel


class AssetCreateResponse(BaseModel):
    id: str
    title: str
    sport: str | None = None
    owner: str | None = None
    owner_uid: str = "demo-user"
    filename: str
    source_hash: str
    gcs_uri: str | None = None
    firebase_doc_path: str | None = None
    synthid_token: str
    ai_summary: str
    structured_analysis: dict
    vision_analysis: dict = {}
    video_intelligence_analysis: dict = {}
    vision_ai_plan: dict = {}
    content_passport: list[dict]
    passport_embedding: list[float]
    keyframes: list[dict]
    demo_clips: list[dict] = []
    created_at: str


class ScanRequest(BaseModel):
    suspect_url: str | None = None


class ScanResponse(BaseModel):
    asset_id: str
    scanned: int
    stages: list[dict]
    violations: list[dict]


class GraphResponse(BaseModel):
    asset_id: str
    nodes: list[dict]
    edges: list[dict]
