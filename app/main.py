from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app import models  # noqa: F401  # registers Item on Base.metadata
from app.config import settings
from app.db import Base, engine
from app.routers import dashboard


def create_app() -> FastAPI:
    app = FastAPI(title="Household Inventory Tracker")

    # Ensure the data directory exists, then create tables (idempotent).
    settings.DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(bind=engine)

    app.mount(
        "/static",
        StaticFiles(directory=str(settings.BASE_DIR / "app" / "static")),
        name="static",
    )
    app.include_router(dashboard.router)

    return app


app = create_app()
