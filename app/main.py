from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.routers import dashboard


def create_app() -> FastAPI:
    app = FastAPI(title="Household Inventory Tracker")

    # The SQLite file lives here; make sure the directory exists before
    # anything touches the database.
    settings.DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    app.mount(
        "/static",
        StaticFiles(directory=str(settings.BASE_DIR / "app" / "static")),
        name="static",
    )
    app.include_router(dashboard.router)

    return app


app = create_app()
