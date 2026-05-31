from typing import Any, Dict, List, Optional

import requests

from app.config import load_settings
from app.retry import run_with_retry
from app.utils_logger import setup_logger


logger = setup_logger("meta_client")


class MetaClientError(Exception):
    """Raised when Meta client data is invalid or unavailable."""


class MetaClient:
    """Instagram Graph API client."""

    def __init__(self) -> None:
        settings = load_settings()
        self._base_url = f"https://graph.facebook.com/{settings.meta_graph_version}"
        self._access_token = settings.instagram_access_token
        self._account_id = settings.instagram_account_id

    def get_profile_info(self) -> Dict:
        profile = run_with_retry(
            operation=self._fetch_profile_info,
            operation_name="get_profile_info",
            logger=logger,
        )
        self._validate_profile(profile)
        return profile

    def get_recent_media(self) -> List[Dict]:
        posts = run_with_retry(
            operation=self._fetch_recent_media,
            operation_name="get_recent_media",
            logger=logger,
        )
        if not isinstance(posts, list):
            raise MetaClientError("Recent media response must be a list.")
        return posts

    def get_media_insights(self, media_id: str) -> Dict:
        return run_with_retry(
            operation=lambda: self._fetch_media_insights(media_id),
            operation_name=f"get_media_insights:{media_id}",
            logger=logger,
        )

    def _api_get(self, path: str, params: Optional[Dict[str, Any]] = None) -> Dict:
        url = f"{self._base_url}/{path.lstrip('/')}"
        query = dict(params or {})
        query["access_token"] = self._access_token
        response = requests.get(url, params=query, timeout=30)
        response.raise_for_status()
        data = response.json()
        if "error" in data:
            error = data["error"]
            message = error.get("message", str(error))
            raise MetaClientError(f"Meta API error: {message}")
        return data

    def _profile_api_get(self, fields: str) -> Dict[str, Any]:
        """GET profile fields; returns parsed JSON including error payloads."""
        url = f"{self._base_url}/{self._account_id.lstrip('/')}"
        response = requests.get(
            url,
            params={"fields": fields, "access_token": self._access_token},
            timeout=30,
        )
        try:
            return response.json()
        except ValueError as exc:
            raise MetaClientError(f"Invalid JSON from Meta API: {exc}") from exc

    def _fetch_profile_info(self) -> Dict:
        data = self._profile_api_get("username,followers_count,media_count")
        if "error" in data:
            logger.warning(
                "Profile fetch with media_count failed, retrying minimal fields."
            )
            data = self._profile_api_get("username,followers_count")
        if "error" in data:
            error = data["error"]
            message = error.get("message", str(error))
            raise MetaClientError(f"Meta API error: {message}")

        return {
            "instagram_account_id": data.get("id", self._account_id),
            "username": data.get("username", "unknown"),
            "followers_count": data.get("followers_count", 0),
            "media_count": data.get("media_count", 0),
            "biography": "",
        }

    def _fetch_recent_media(self) -> List[Dict]:
        data = self._api_get(
            f"{self._account_id}/media",
            params={
                "fields": "id,caption,media_type,timestamp,permalink",
                "limit": 20,
            },
        )
        return [
            {
                "post_id": item.get("id", ""),
                "caption": item.get("caption") or "",
                "media_type": item.get("media_type", ""),
                "timestamp": item.get("timestamp", ""),
                "permalink": item.get("permalink", ""),
            }
            for item in data.get("data", [])
        ]

    @staticmethod
    def _zero_insights() -> Dict[str, int]:
        return {
            "likes_count": 0,
            "comments_count": 0,
            "shares": 0,
            "saves": 0,
            "reach": 0,
            "impressions": 0,
        }

    def _fetch_media_insights(self, media_id: str) -> Dict:
        url = f"{self._base_url}/{media_id.lstrip('/')}"
        params = {
            "fields": "like_count,comments_count",
            "access_token": self._access_token,
        }
        response = requests.get(url, params=params, timeout=30)

        if response.status_code == 400:
            logger.warning(
                "Media fields request returned 400 for %s; using zero insights.",
                media_id,
            )
            return self._zero_insights()

        response.raise_for_status()
        data = response.json()
        if "error" in data:
            logger.warning(
                "Meta API error for media %s: %s; using zero insights.",
                media_id,
                data["error"].get("message", data["error"]),
            )
            return self._zero_insights()

        missing = [
            field
            for field in ("like_count", "comments_count")
            if field not in data
        ]
        if missing:
            logger.warning(
                "Missing media fields for %s: %s",
                media_id,
                ", ".join(missing),
            )

        return {
            "likes_count": data.get("like_count") or 0,
            "comments_count": data.get("comments_count") or 0,
            "shares": 0,
            "saves": 0,
            "reach": 0,
            "impressions": 0,
        }

    @staticmethod
    def _validate_profile(profile: Dict) -> None:
        required_fields = {
            "instagram_account_id",
            "username",
            "followers_count",
        }
        if not required_fields.issubset(profile.keys()):
            raise MetaClientError("Profile response is missing required fields.")
        if not profile.get("username"):
            raise MetaClientError("Profile response is missing username.")
