"""
Router pour les interactions Discord.
"""
import logging
from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, Depends, status

from app.core.security import require_api_key
from discord_utils import (
    test_discord_connection,
    get_guild_channels,
    get_channel,
    restart_discord_client,
    is_discord_ready,
    isValidDiscordId
)

router = APIRouter(prefix="/discord", tags=["Discord"])
logger = logging.getLogger(__name__)


@router.get("/status", response_model=Dict[str, Any])
async def get_discord_status(_key: str = Depends(require_api_key)):
    """Vérifie le statut de la connexion Discord."""
    connection_result = await test_discord_connection()

    return {
        **connection_result,
        "is_ready": is_discord_ready()
    }


@router.post("/restart", response_model=Dict[str, str])
async def restart_discord(_key: str = Depends(require_api_key)):
    """Redémarre le client Discord."""
    result = await restart_discord_client()
    return result


@router.get("/guilds/{guild_id}/channels", response_model=List[Dict[str, Any]])
async def list_guild_channels(
    guild_id: str,
    _key: str = Depends(require_api_key)
):
    """
    Liste les salons d'un serveur Discord.

    Args:
        guild_id: ID du serveur Discord
    """
    if not isValidDiscordId(guild_id):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"ID serveur invalide: {guild_id}"
        )

    channels = await get_guild_channels(None, guild_id)

    if not channels:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            "Aucun salon trouvé. Vérifiez que le bot est invité sur ce serveur."
        )

    return channels


@router.get("/channels/{channel_id}", response_model=Dict[str, Any])
async def get_channel_info(
    channel_id: str,
    _key: str = Depends(require_api_key)
):
    """
    Récupère les informations d'un salon Discord.

    Args:
        channel_id: ID du salon Discord
    """
    if not isValidDiscordId(channel_id):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"ID salon invalide: {channel_id}"
        )

    channel = await get_channel(None, channel_id)

    if not channel:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            "Salon non trouvé. Vérifiez que le bot a accès à ce salon."
        )

    return channel


@router.post("/test-message", response_model=Dict[str, str])
async def send_test_message(
    channel_id: str,
    message: str = "🧪 Message de test depuis RSSDI",
    _key: str = Depends(require_api_key)
):
    """
    Envoie un message de test vers un salon Discord.

    Args:
        channel_id: ID du salon Discord
        message: Message à envoyer
    """
    if not isValidDiscordId(channel_id):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"ID salon invalide: {channel_id}"
        )

    from discord_utils import send_to_discord

    try:
        await send_to_discord(
            discord_client=None,
            target_id=channel_id,
            content=message,
            allow_embeds=True,
            mode="direct"
        )

        return {
            "status": "success",
            "message": "Message de test envoyé avec succès"
        }

    except Exception as e:
        logger.error(f"Erreur envoi message test: {e}")
        raise HTTPException(
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            f"Erreur lors de l'envoi: {str(e)}"
        )
