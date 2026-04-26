from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import ensure_data_dirs, settings
from .db import init_db
from .routes import assets, audit, graph, violations


def create_app() -> FastAPI:
    ensure_data_dirs()
    init_db()
    app = FastAPI(title=settings.app_name, version="0.1.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    def health():
        return {"status": "ok", "service": settings.app_name}

    app.include_router(assets.router)
    app.include_router(violations.router)
    app.include_router(graph.router)
    app.include_router(audit.router)
    return app


app = create_app()
