from fastapi import APIRouter, Depends, HTTPException

from ..db import get_db
from ..models import GraphResponse
from ..services.auth_service import CurrentUser, get_current_user
from ..services.graph_service import read_graph

router = APIRouter(prefix="/api/graph", tags=["graph"])


@router.get("/{asset_id}", response_model=GraphResponse)
def get_graph(asset_id: str, user: CurrentUser = Depends(get_current_user)):
    with get_db() as db:
        asset = db.execute("SELECT owner_uid FROM assets WHERE id = ?", (asset_id,)).fetchone()
        if not asset:
            raise HTTPException(status_code=404, detail="Asset not found")
        if user.uid != "demo-user" and asset["owner_uid"] != user.uid:
            raise HTTPException(status_code=403, detail="Asset belongs to a different Firebase user")
        return read_graph(db, asset_id)
