from fastapi import APIRouter

from ..db import get_db
from ..models import GraphResponse
from ..services.graph_service import read_graph

router = APIRouter(prefix="/api/graph", tags=["graph"])


@router.get("/{asset_id}", response_model=GraphResponse)
def get_graph(asset_id: str):
    with get_db() as db:
        return read_graph(db, asset_id)
