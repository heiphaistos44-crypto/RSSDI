import discord
import re
import os
import asyncio
from typing import Dict, List, Optional, Union
import logging
from dotenv import load_dotenv

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

# -----------------------------
# Initialisation du client Discord
# -----------------------------
# ARCHITECTURE NOTE:
# Ce client utilise une approche REST-only (login sans connect).
# Cela signifie:
#   - Le bot peut ENVOYER des messages (send_message, fetch_channel, etc.)
#   - Le bot ne REÇOIT PAS d'événements (on_message, on_ready, etc.)
#   - Pas de connexion WebSocket maintenue en permanence
#   - Adapté pour un système qui envoie des notifications RSS sans avoir besoin
#     de répondre aux messages Discord
# -----------------------------

intents = discord.Intents.default()
intents.guilds = True
intents.guild_messages = True
intents.message_content = True

discord_client = None
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")

# Instance globale du client Discord
_discord_client: Optional[discord.Client] = None
_client_ready: bool = False
_client_lock = asyncio.Lock()

async def initialize_discord_client() -> Optional[discord.Client]:
    """
    Initialise le client Discord en mode REST-only (login sans connect).

    Returns:
        Optional[discord.Client]: Le client initialisé ou None en cas d'erreur

    Note:
        Cette fonction est thread-safe grâce à l'utilisation d'un verrou asyncio.
    """
    global _discord_client, _client_ready

    async with _client_lock:
        if _discord_client is not None and _client_ready:
            return _discord_client

        if not DISCORD_TOKEN:
            logger.error("Token Discord non configuré - vérifiez DISCORD_TOKEN dans .env")
            return None

        try:
            _discord_client = discord.Client(intents=intents)
            await _discord_client.login(DISCORD_TOKEN)
            _client_ready = True
            logger.info("Client Discord initialisé avec succès (mode REST-only)")
            return _discord_client
        except discord.LoginFailure:
            logger.error("Token Discord invalide - vérifiez votre DISCORD_TOKEN")
            _discord_client = None
            _client_ready = False
            return None
        except Exception as e:
            logger.error(f"Erreur initialisation Discord client: {e}")
            _discord_client = None
            _client_ready = False
            return None

async def get_discord_client() -> Optional[discord.Client]:
    """
    Récupère le client Discord (l'initialise si nécessaire).

    Returns:
        Optional[discord.Client]: Le client Discord ou None si l'initialisation échoue
    """
    global _discord_client, _client_ready
    if _discord_client is None or not _client_ready:
        return await initialize_discord_client()
    return _discord_client

def is_discord_ready() -> bool:
    """
    Vérifie si le client Discord est prêt à être utilisé.

    Returns:
        bool: True si le client est initialisé et prêt
    """
    return _client_ready and _discord_client is not None

async def close_discord_client() -> None:
    """
    Ferme proprement le client Discord.

    Note:
        Cette fonction devrait être appelée lors de l'arrêt de l'application
        pour garantir une fermeture propre des connexions.
    """
    global _discord_client, _client_ready

    if _discord_client:
        try:
            await _discord_client.close()
            logger.info("Client Discord fermé proprement")
        except Exception as e:
            logger.warning(f"Erreur lors de la fermeture du client Discord: {e}")
        finally:
            _discord_client = None
            _client_ready = False

# -----------------------------
# Validation
# -----------------------------

def isValidDiscordId(value: str) -> bool:
    """Vérifie si une chaîne est un ID Discord valide (17 à 20 chiffres)."""
    return bool(re.fullmatch(r"\d{17,20}", str(value)))

def isValidUrl(url: str) -> bool:
    """Vérifie si une chaîne est une URL valide (http/https)."""
    return bool(re.match(r"^https?://", str(url)))

# -----------------------------
# Fonctions utilitaires Discord
# -----------------------------

async def send_to_discord(
    discord_client: Optional[discord.Client],
    target_id: str,
    content: str,
    allow_embeds: bool = False,
    mode: str = "direct"
) -> Optional[int]:
    """
    Envoie un message vers un salon ou un thread Discord.
    
    Args:
        discord_client: Client Discord à utiliser (peut être None)
        target_id: ID du salon ou du thread
        content: Texte du message
        allow_embeds: Si True, Discord pourra générer un embed (preview)
        mode: "direct" ou "thread"
    
    Returns:
        Optional[int]: ID du message créé si mode="thread", None sinon
        
    Raises:
        ValueError: Si le salon/thread n'est pas trouvé
        Exception: Pour les autres erreurs Discord
    """
    try:
        # Récupérer le client Discord si non fourni
        if discord_client is None:
            discord_client = await get_discord_client()
            
        if discord_client is None:
            raise ValueError("Client Discord non disponible")

        channel = discord_client.get_channel(int(target_id))
        if not channel:
            channel = await discord_client.fetch_channel(int(target_id))

        if not channel:
            raise ValueError(f"Salon/Thread introuvable: {target_id}")

        if mode == "thread" and hasattr(channel, "create_thread"):
            msg = await channel.send(content)
            await channel.create_thread(name="Discussion", message=msg)
            return msg.id
        else:
            await channel.send(content)
            return None

    except Exception as e:
        logger.error(f"[DiscordUtils] Erreur envoi vers {target_id}: {e}")
        raise

async def get_guild_channels(discord_client, guild_id: str):
    """
    Récupère la liste des salons d'un serveur.
    Renvoie une liste de dicts {id, name, type, typeLabel}.
    """
    try:
        # Récupérer le client Discord si non fourni
        if discord_client is None:
            discord_client = await get_discord_client()
            
        if discord_client is None:
            logger.error("Client Discord non disponible")
            return []

        logger.info(f"Récupération des salons pour le serveur {guild_id}")
        
        # Essayer d'abord get_guild (cache), puis fetch_guild (API)
        guild = None
        try:
            guild = discord_client.get_guild(int(guild_id))
            if guild is None:
                logger.info(f"Serveur {guild_id} non trouvé en cache, tentative fetch...")
                guild = await discord_client.fetch_guild(int(guild_id))
        except discord.Forbidden:
            logger.error(f"Accès refusé au serveur {guild_id} - vérifiez que le bot est invité")
            return []
        except discord.NotFound:
            logger.error(f"Serveur {guild_id} non trouvé")
            return []
        except Exception as e:
            logger.error(f"Erreur lors de la récupération du serveur {guild_id}: {e}")
            return []

        if not guild:
            logger.error(f"Impossible de récupérer le serveur {guild_id}")
            return []

        logger.info(f"Serveur trouvé: {guild.name}")
        channels = []
        
        try:
            # Récupérer tous les salons
            for ch in guild.channels:
                # Filtrer seulement les types de salons utiles
                if hasattr(ch, 'type') and ch.type.value in [0, 5, 15]:  # text, announcement, forum
                    type_label = str(ch.type).replace('ChannelType.', '')
                    channels.append({
                        "id": str(ch.id),
                        "name": ch.name,
                        "type": ch.type.value,
                        "typeLabel": type_label
                    })
            
            logger.info(f"Trouvé {len(channels)} salons utilisables sur {len(guild.channels)} total")
            return sorted(channels, key=lambda x: x['name'])
            
        except Exception as e:
            logger.error(f"Erreur lors de l'énumération des salons: {e}")
            return []
            
    except Exception as e:
        logger.error(f"[DiscordUtils] Erreur get_guild_channels: {e}")
        return []

async def get_channel(discord_client, channel_id: str):
    """
    Récupère les infos d'un salon ou thread.
    """
    try:
        # Récupérer le client Discord si non fourni
        if discord_client is None:
            discord_client = await get_discord_client()
            
        if discord_client is None:
            raise ValueError("Client Discord non disponible")
            
        ch = discord_client.get_channel(int(channel_id))
        if not ch:
            ch = await discord_client.fetch_channel(int(channel_id))
        if not ch:
            return None
        return {
            "id": str(ch.id),
            "name": getattr(ch, "name", f"#{ch.id}"),
            "type": ch.type.value,
            "typeLabel": str(ch.type).replace('ChannelType.', '')
        }
    except Exception as e:
        logger.error(f"[DiscordUtils] Erreur get_channel: {e}")
        return None

# -----------------------------
# Fonctions de diagnostic
# -----------------------------

async def test_discord_connection():
    """
    Teste la connexion Discord et retourne un rapport de diagnostic.
    """
    try:
        if not DISCORD_TOKEN:
            return {
                "status": "error",
                "message": "Token Discord non configuré",
                "details": "Vérifiez votre variable d'environnement DISCORD_TOKEN"
            }
        
        # Tester l'initialisation du client
        client = await get_discord_client()
        if client is None:
            return {
                "status": "error",
                "message": "Échec de connexion Discord",
                "details": "Impossible d'initialiser le client Discord"
            }
        
        # Tester si le client est prêt
        if not is_discord_ready():
            return {
                "status": "warning",
                "message": "Client Discord partiellement initialisé",
                "details": "Le client n'est pas complètement prêt"
            }
        
        return {
            "status": "success",
            "message": "Connexion Discord active",
            "details": "Le client Discord est prêt à envoyer des messages"
        }
        
    except Exception as e:
        logger.error(f"Erreur test Discord: {e}")
        return {
            "status": "error",
            "message": f"Erreur test Discord: {str(e)}",
            "details": "Vérifiez votre token et les permissions du bot"
        }

async def restart_discord_client():
    """
    Redémarre le client Discord en forçant une nouvelle connexion.
    """
    global _discord_client, _client_ready
    
    try:
        # Fermer le client existant si il existe
        if _discord_client:
            try:
                await _discord_client.close()
                logger.info("Client Discord précédent fermé")
            except Exception as e:
                logger.warning(f"Erreur fermeture client: {e}")
        
        # Reset des variables globales
        _discord_client = None
        _client_ready = False
        
        # Réinitialiser
        client = await initialize_discord_client()
        
        if client and _client_ready:
            logger.info("Client Discord redémarré avec succès")
            return {"status": "success", "message": "Client Discord redémarré avec succès"}
        else:
            logger.error("Échec du redémarrage Discord")
            return {"status": "error", "message": "Échec du redémarrage Discord - vérifiez votre token"}
            
    except Exception as e:
        logger.error(f"Erreur redémarrage Discord: {e}")
        return {"status": "error", "message": f"Erreur redémarrage Discord: {str(e)}"}
