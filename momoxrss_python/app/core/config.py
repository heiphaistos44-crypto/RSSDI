"""
Configuration centralisée de l'application RSSDI.
Utilise pydantic pour la validation des variables d'environnement.
"""
import os
from typing import Optional
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    """Configuration de l'application avec validation."""

    # Application
    app_name: str = "RSSDI - RSS Discord Integration"
    app_version: str = "4.0.0"
    debug: bool = False

    # API
    api_key: str
    port: int = 3000
    allowed_origin: str = "*"

    # MongoDB
    mongo_url: str = "mongodb://mongodb:27017/momoxrss"
    mongo_db: str = "momoxrss"
    mongo_root_user: Optional[str] = "admin"
    mongo_root_password: Optional[str] = None

    # Discord
    discord_token: str

    # RSSHub
    rsshub_base: str = "https://rsshub.app"

    # Database
    sent_items_retention_days: int = 7

    # Performance
    default_check_interval: int = 300  # 5 minutes
    max_concurrent_checks: int = 10
    cache_ttl: int = 60  # 1 minute

    # Rate Limiting
    rate_limit_enabled: bool = True
    rate_limit_per_minute: int = 100

    model_config = {
        "env_file": ".env",
        "case_sensitive": False,
        "extra": "ignore"
    }


@lru_cache()
def get_settings() -> Settings:
    """
    Retourne une instance singleton des settings.

    Le décorateur lru_cache garantit qu'on ne parse le .env qu'une seule fois.
    """
    return Settings()
