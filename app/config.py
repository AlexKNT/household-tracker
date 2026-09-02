from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    """Application settings, resolved once at import time."""

    BASE_DIR: Path
    DB_PATH: Path
    POLL_INTERVAL_S: int
    EAT_SOON_DAYS: int
    PURGE_AFTER_DAYS: int

    @classmethod
    def load(cls) -> "Settings":
        base_dir = Path(__file__).resolve().parent.parent
        return cls(
            BASE_DIR=base_dir,
            DB_PATH=base_dir / "data" / "household.db",
            POLL_INTERVAL_S=10,
            EAT_SOON_DAYS=3,
            PURGE_AFTER_DAYS=7,
        )


settings = Settings.load()
