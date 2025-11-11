"""
Module de sécurité - Authentification et autorisation.
"""
from fastapi import Security, HTTPException, status
from fastapi.security import APIKeyHeader
from app.core.config import get_settings

settings = get_settings()

# Header pour la clé API
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def require_api_key(api_key: str = Security(api_key_header)) -> str:
    """
    Vérifie que la clé API fournie est valide.

    Args:
        api_key: Clé API depuis le header X-API-Key

    Returns:
        str: La clé API si elle est valide

    Raises:
        HTTPException: 401 si la clé est invalide ou absente
    """
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Clé API manquante. Ajoutez le header X-API-Key.",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    if api_key != settings.api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Clé API invalide.",
            headers={"WWW-Authenticate": "ApiKey"},
        )

    return api_key


class RateLimiter:
    """
    Rate limiter simple en mémoire.
    Pour la production, utilisez Redis avec slowapi.
    """
    def __init__(self, max_requests: int = 100, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: dict[str, list[float]] = {}

    def is_allowed(self, identifier: str) -> bool:
        """
        Vérifie si une requête est autorisée pour cet identifiant.

        Args:
            identifier: Identifiant unique (IP, user_id, etc.)

        Returns:
            bool: True si la requête est autorisée
        """
        import time

        now = time.time()

        # Nettoyer les anciennes requêtes
        if identifier in self.requests:
            self.requests[identifier] = [
                req_time for req_time in self.requests[identifier]
                if now - req_time < self.window_seconds
            ]
        else:
            self.requests[identifier] = []

        # Vérifier la limite
        if len(self.requests[identifier]) >= self.max_requests:
            return False

        # Ajouter la requête actuelle
        self.requests[identifier].append(now)
        return True


# Instance globale du rate limiter
rate_limiter = RateLimiter(
    max_requests=settings.rate_limit_per_minute,
    window_seconds=60
)
