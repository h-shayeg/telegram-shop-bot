import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


@dataclass(frozen=True)
class Settings:
    bot_token: str
    database_url: str
    proxy_url: str | None
    admin_ids: frozenset[int]


def load_settings() -> Settings:
    admin_raw = os.getenv("ADMIN_IDS", "")
    return Settings(
        bot_token=os.environ["BOT_TOKEN"],
        database_url=os.environ["DATABASE_URL"],
        proxy_url=os.getenv("PROXY_URL") or None,
        admin_ids=frozenset(int(x) for x in admin_raw.split(",") if x.strip()),
    )
