from dataclasses import dataclass
import os

from dotenv import load_dotenv


@dataclass
class Settings:
    meta_app_id: str
    meta_app_secret: str
    meta_graph_version: str
    instagram_account_id: str
    instagram_access_token: str
    redirect_uri: str
    anthropic_api_key: str
    gmail_address: str
    gmail_app_password: str


def load_settings() -> Settings:
    """
    Loads environment variables from .env and validates required keys.
    """
    load_dotenv()

    settings = Settings(
        meta_app_id=os.getenv("META_APP_ID", "").strip(),
        meta_app_secret=os.getenv("META_APP_SECRET", "").strip(),
        meta_graph_version=os.getenv("META_GRAPH_VERSION", "v18.0").strip(),
        instagram_account_id=os.getenv("INSTAGRAM_ACCOUNT_ID", "").strip(),
        instagram_access_token=os.getenv("INSTAGRAM_ACCESS_TOKEN", "").strip(),
        redirect_uri=os.getenv("REDIRECT_URI", "").strip(),
        anthropic_api_key=os.getenv("ANTHROPIC_API_KEY", "").strip(),
        gmail_address=os.getenv("GMAIL_ADDRESS", "").strip(),
        gmail_app_password=os.getenv("GMAIL_APP_PASSWORD", "").strip(),
    )

    missing = []
    if not settings.meta_app_id:
        missing.append("META_APP_ID")
    if not settings.meta_app_secret:
        missing.append("META_APP_SECRET")
    if not settings.instagram_account_id:
        missing.append("INSTAGRAM_ACCOUNT_ID")
    if not settings.instagram_access_token:
        missing.append("INSTAGRAM_ACCESS_TOKEN")
    if not settings.redirect_uri:
        missing.append("REDIRECT_URI")
    if not settings.anthropic_api_key:
        missing.append("ANTHROPIC_API_KEY")

    if missing:
        missing_values = ", ".join(missing)
        raise ValueError(f"Missing required .env values: {missing_values}")

    return settings
