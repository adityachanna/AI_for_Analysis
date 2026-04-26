from pydantic import BaseModel


class AssetCreateResponse(BaseModel):
    id: str
    title: str
    sport: str | None = None
    owner: str | None = None
    filename: str
    synthid_token: str
    ai_summary: str
    structured_analysis: dict
    content_passport: list[dict]
    passport_embedding: list[float]
    keyframes: list[dict]
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
