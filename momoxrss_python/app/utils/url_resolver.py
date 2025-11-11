"""
Utilitaire pour résoudre les URLs de différents types de sources (YouTube, Facebook, etc.).
"""
import logging
from app.core.config import get_settings

settings = get_settings()
logger = logging.getLogger(__name__)


class URLResolver:
    """Résout les URLs pour différents types de sources."""

    @staticmethod
    def resolve(url: str, source_type: str) -> str:
        """
        Résout une URL selon son type de source.

        Args:
            url: URL à résoudre
            source_type: Type de source (youtube, facebook, instagram, tiktok, rss)

        Returns:
            str: URL RSS valide
        """
        try:
            if source_type == "youtube":
                return URLResolver._resolve_youtube(url)
            elif source_type == "facebook":
                return URLResolver._resolve_facebook(url)
            elif source_type == "instagram":
                return URLResolver._resolve_instagram(url)
            elif source_type == "tiktok":
                return URLResolver._resolve_tiktok(url)
            else:
                return url

        except Exception as e:
            logger.error(f"Erreur résolution URL {url} (type: {source_type}): {e}")
            return url

    @staticmethod
    def _resolve_youtube(url: str) -> str:
        """Résout une URL YouTube en flux RSS."""
        # Channel ID
        if "youtube.com/channel/" in url:
            channel_id = url.split("youtube.com/channel/")[-1].split("/")[0].split("?")[0]
            return f"https://www.youtube.com/feeds/videos.xml?channel_id={channel_id}"

        # Channel handle (@username)
        elif "youtube.com/@" in url:
            username = url.split("youtube.com/@")[-1].split("/")[0].split("?")[0]
            return f"https://www.youtube.com/feeds/videos.xml?user={username}"

        # Legacy user format
        elif "youtube.com/user/" in url:
            username = url.split("youtube.com/user/")[-1].split("/")[0].split("?")[0]
            return f"https://www.youtube.com/feeds/videos.xml?user={username}"

        # Channel URL with c/ format
        elif "youtube.com/c/" in url:
            username = url.split("youtube.com/c/")[-1].split("/")[0].split("?")[0]
            return f"https://www.youtube.com/feeds/videos.xml?user={username}"

        # Playlist
        elif "list=" in url:
            playlist_id = url.split("list=")[-1].split("&")[0]
            return f"https://www.youtube.com/feeds/videos.xml?playlist_id={playlist_id}"

        return url

    @staticmethod
    def _resolve_facebook(url: str) -> str:
        """Résout une URL Facebook via RSSHub."""
        if "facebook.com/" in url:
            page = url.split("facebook.com/")[-1].split("/")[0].split("?")[0]
            rsshub_base = settings.rsshub_base.rstrip("/")
            return f"{rsshub_base}/facebook/page/{page}"
        return url

    @staticmethod
    def _resolve_instagram(url: str) -> str:
        """Résout une URL Instagram via RSSHub."""
        if "instagram.com/" in url:
            username = url.split("instagram.com/")[-1].split("/")[0].split("?")[0]
            rsshub_base = settings.rsshub_base.rstrip("/")
            return f"{rsshub_base}/instagram/user/{username}"
        return url

    @staticmethod
    def _resolve_tiktok(url: str) -> str:
        """Résout une URL TikTok via RSSHub."""
        if "tiktok.com/@" in url:
            username = url.split("tiktok.com/@")[-1].split("/")[0].split("?")[0]
            rsshub_base = settings.rsshub_base.rstrip("/")
            return f"{rsshub_base}/tiktok/user/{username}"
        return url


# Instance singleton
url_resolver = URLResolver()
