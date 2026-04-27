import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import ensure_data_dirs, settings
from .db import init_db
from .routes import assets, audit, graph, violations, vision_ai


def create_app() -> FastAPI:
    ensure_data_dirs()
    init_db()
    app = FastAPI(title=settings.app_name, version="0.1.0")
    _origins_env = os.getenv("ALLOWED_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")
    origins = [o.strip() for o in _origins_env.split(",") if o.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.on_event("startup")
    async def startup_event():
        """Ensure Neo4j indexes exist on first boot (idempotent, non-fatal)."""
        try:
            from .services import neo4j_service
            driver = neo4j_service.get_driver()
            neo4j_service.ensure_indexes(driver)
        except Exception as exc:  # noqa: BLE001
            import logging
            logging.getLogger(__name__).warning("Neo4j startup init skipped: %s", exc)

    @app.get("/health")
    def health():
        return {"status": "ok", "service": settings.app_name}

    app.include_router(assets.router)
    app.include_router(violations.router)
    app.include_router(graph.router)
    app.include_router(audit.router)
    app.include_router(vision_ai.router)
    return app


app = create_app()
