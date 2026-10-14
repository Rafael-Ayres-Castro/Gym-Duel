"""Builds the FastAPI app: JSON API under /api and the static frontend at /.

Run with: uvicorn app.main:create_app --factory --app-dir backend
"""

from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

from . import routers
from .config import FRONTEND_DIR, Settings, get_settings
from .db import Base, make_engine, make_session_factory


async def _validation_error(_: Request, exc: RequestValidationError) -> JSONResponse:
    # Same shape as every other API error, keeping pydantic's details for debugging.
    detail = {"code": "invalid_input", "message": "Confira os dados e tente de novo.", "errors": exc.errors()}
    return JSONResponse(status_code=422, content={"detail": jsonable_encoder(detail)})


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or get_settings()
    engine = make_engine(settings.database_url)
    # No migrations in the MVP: tables are created on start up if missing.
    Base.metadata.create_all(engine)

    app = FastAPI(
        title="Gym Duel API",
        version="1.0.0",
        description="Placar semanal do casal. Todas as rotas, exceto login e cadastro, exigem token Bearer.",
    )
    app.state.settings = settings
    app.state.session_factory = make_session_factory(engine)
    app.add_exception_handler(RequestValidationError, _validation_error)

    for router in routers.ALL:
        app.include_router(router, prefix="/api")

    @app.get("/api/health", tags=["health"])
    def health() -> dict:
        """Used by the host (Render) to know the app is up."""
        return {"status": "ok"}

    if FRONTEND_DIR.is_dir():
        # Mounted last so /api and /docs keep priority; html=True serves index.html at "/".
        app.mount("/", StaticFiles(directory=FRONTEND_DIR, html=True), name="frontend")
    return app
