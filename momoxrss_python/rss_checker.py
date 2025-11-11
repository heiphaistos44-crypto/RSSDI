import re
import time
import logging
import feedparser
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple

# Configuration du logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

from db import already_sent, mark_as_sent
from discord_utils import send_to_discord
from models import FluxInDB

# -----------------------------
# Helpers de filtre de contenu
# -----------------------------

def normalize_text(s: str) -> str:
    return (s or "").strip()

def match_keywords(text: str, keywords: List[str]) -> bool:
    if not keywords:
        return True
    t = text.lower()
    return any(kw.lower() in t for kw in keywords)

def match_regex(text: str, patterns: List[str], expect=True) -> bool:
    if not patterns:
        return True if expect else False
    try:
        for pat in patterns:
            if re.search(pat, text, flags=re.IGNORECASE):
                return True
        return False
    except re.error:
        return True if expect else False

def extract_domain(url: str) -> str:
    try:
        return re.sub(r"^https?://(www\.)?", "", url).split("/")[0]
    except Exception:
        return ""

def match_domains(url: str, whitelist: List[str], blacklist: List[str]) -> bool:
    domain = extract_domain(url)
    if whitelist and domain not in whitelist:
        return False
    if blacklist and domain in blacklist:
        return False
    return True

def within_quiet_hours(now: datetime, start: Optional[str], end: Optional[str]) -> bool:
    if not start or not end:
        return False
    try:
        st = datetime.strptime(start, "%H:%M").time()
        en = datetime.strptime(end, "%H:%M").time()
    except ValueError:
        return False

    now_t = now.time()
    if st < en:
        return st <= now_t <= en
    else:
        return now_t >= st or now_t <= en

def language_filter(text: str, language: Optional[str]) -> bool:
    if not language:
        return True
    t = text.lower()
    if language == "fr":
        markers = [" le ", " la ", " les ", " de ", " des ", " et ", " à ", " pour ", " sur "]
        score = sum(1 for m in markers if m in t)
        return score >= 1
    elif language == "en":
        markers = [" the ", " and ", " of ", " for ", " on ", " with ", " from "]
        score = sum(1 for m in markers if m in t)
        return score >= 1
    return True

# -----------------------------
# RSS parsing helpers
# -----------------------------

def parse_rss_feed(url: str):
    return feedparser.parse(url)

def getItemLinkOrGuid(entry: dict) -> str:
    return entry.get("link") or entry.get("id") or ""

def getItemDate(entry: dict) -> Optional[int]:
    if "published_parsed" in entry and entry.published_parsed:
        return int(time.mktime(entry.published_parsed))
    if "updated_parsed" in entry and entry.updated_parsed:
        return int(time.mktime(entry.updated_parsed))
    return None

# -----------------------------
# Vérification/envoi pour un flux
# -----------------------------

def _sort_items(entries: List[dict]) -> List[dict]:
    def key(e):
        dt = getItemDate(e)
        return dt or 0
    return sorted(entries, key=key, reverse=True)

async def check_flux(flux: FluxInDB, coll):
    """
    Vérifie un flux RSS et envoie les nouveaux articles vers Discord.
    Gestion améliorée de la déduplication et des erreurs.

    Args:
        flux: Configuration du flux RSS à vérifier
        coll: Collection MongoDB pour la mise à jour des métadonnées

    Returns:
        None

    Raises:
        N'émet pas d'exceptions, les erreurs sont loggées
    """
    try:
        feed = parse_rss_feed(flux.rssUrl)

        # Vérifier les erreurs de parsing
        if hasattr(feed, 'bozo') and feed.bozo:
            if hasattr(feed, 'bozo_exception'):
                logger.warning(f"[Flux {flux.id}] Erreur parsing RSS: {feed.bozo_exception}")

        if not feed.entries:
            logger.debug(f"[Flux {flux.id}] Aucun article trouvé dans le flux")
            return
    except Exception as e:
        logger.error(f"[Flux {flux.id}] Erreur récupération flux RSS: {e}")
        return

    try:
        entries = _sort_items(feed.entries)
    except Exception as e:
        logger.error(f"[Flux {flux.id}] Erreur tri des articles: {e}")
        entries = feed.entries
    now = datetime.now()
    sent_this_run = 0
    max_per_run = flux.maxPerRun or 5
    
    # Garder une trace des articles déjà vus pour ce flux
    seen_items = set()

    for e in entries:
        if sent_this_run >= max_per_run:
            break

        title = normalize_text(e.get("title") or "Sans titre")
        link = normalize_text(getItemLinkOrGuid(e))
        summary = normalize_text(e.get("summary", "") or e.get("description", ""))

        if not link:
            continue

        if within_quiet_hours(now, flux.quietHoursStart, flux.quietHoursEnd):
            continue

        # Vérification de duplication multiple
        if link in seen_items or already_sent(link):
            continue
        seen_items.add(link)

        full_text = f"{title}\n{summary}"
        if not language_filter(full_text, flux.language):
            continue
        if flux.includeKeywords and not match_keywords(full_text, flux.includeKeywords):
            continue
        if flux.excludeKeywords and match_keywords(full_text, flux.excludeKeywords):
            continue
        if flux.regexInclude and not match_regex(full_text, flux.regexInclude, expect=True):
            continue
        if flux.regexExclude and match_regex(full_text, flux.regexExclude, expect=True):
            continue
        if not match_domains(link, flux.domainWhitelist or [], flux.domainBlacklist or []):
            continue

        message = (flux.messageTemplate or "{title}\n{link}") \
            .replace("{title}", title) \
            .replace("{link}", link)

        if flux.mentionUserId:
            message = f"<@{flux.mentionUserId}> {message}"
        if flux.mentionRoleId:
            message = f"<@&{flux.mentionRoleId}> {message}"

        try:
            await send_to_discord(
                discord_client=None,  # Le client est géré ailleurs, ici on envoie via utilitaire
                target_id=flux.discordTarget,
                content=message,
                allow_embeds=bool(flux.allowEmbeds),
                mode=flux.mode or "direct"
            )
            mark_as_sent(flux.id, link)
            sent_this_run += 1

            # Mettre à jour les métadonnées du flux
            try:
                await coll.update_one(
                    {"_id": flux.id} if isinstance(flux.id, dict) else {"_id": flux.id},
                    {"$set": {"lastItem": link, "lastPubDate": getItemDate(e), "totalSent": (flux.totalSent + 1)}}
                )
            except Exception as db_err:
                logger.warning(f"[Flux {flux.id}] Erreur mise à jour métadonnées: {db_err}")
                # Continuer même si la mise à jour échoue

        except ValueError as ve:
            # Erreurs de validation (ID invalide, etc.)
            logger.error(f"[Flux {flux.id}] Erreur validation Discord: {ve} — Article: {link}")
            continue
        except ConnectionError as ce:
            # Erreurs de connexion Discord
            logger.error(f"[Flux {flux.id}] Erreur connexion Discord: {ce} — Article: {link}")
            continue
        except Exception as ex:
            # Autres erreurs non prévues
            logger.error(f"[Flux {flux.id}] Erreur envoi Discord: {ex} — Article: {link}", exc_info=True)
            continue
