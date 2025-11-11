"""
Service RSS - Logique métier pour la gestion des flux RSS.
Refactorisé pour être plus maintenable et performant.
"""
import asyncio
import feedparser
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime
import time
from functools import lru_cache

from app.core.config import get_settings
from models import FluxInDB, RssArticle
from db import already_sent, mark_as_sent
from discord_utils import send_to_discord

settings = get_settings()
logger = logging.getLogger(__name__)


class RSSService:
    """Service pour la gestion des flux RSS."""

    @staticmethod
    def parse_feed(url: str) -> feedparser.FeedParserDict:
        """
        Parse un flux RSS/Atom.

        Args:
            url: URL du flux RSS

        Returns:
            feedparser.FeedParserDict: Flux parsé
        """
        try:
            feed = feedparser.parse(url)

            # Vérifier les erreurs de parsing
            if hasattr(feed, 'bozo') and feed.bozo:
                if hasattr(feed, 'bozo_exception'):
                    logger.warning(f"Erreur parsing RSS {url}: {feed.bozo_exception}")

            return feed
        except Exception as e:
            logger.error(f"Erreur parsing flux {url}: {e}")
            raise

    @staticmethod
    def extract_item_link(entry: dict) -> str:
        """Extrait le lien d'un article RSS."""
        return entry.get("link") or entry.get("id") or ""

    @staticmethod
    def extract_item_date(entry: dict) -> Optional[int]:
        """Extrait la date de publication d'un article."""
        if "published_parsed" in entry and entry.published_parsed:
            return int(time.mktime(entry.published_parsed))
        if "updated_parsed" in entry and entry.updated_parsed:
            return int(time.mktime(entry.updated_parsed))
        return None

    @staticmethod
    def sort_entries_by_date(entries: List[dict]) -> List[dict]:
        """
        Trie les articles par date (plus récent en premier).

        Args:
            entries: Liste d'articles

        Returns:
            List[dict]: Articles triés
        """
        def get_date(entry):
            date = RSSService.extract_item_date(entry)
            return date or 0

        return sorted(entries, key=get_date, reverse=True)

    @staticmethod
    def filter_by_language(text: str, language: Optional[str]) -> bool:
        """
        Filtre par langue (détection simple).

        Args:
            text: Texte à analyser
            language: Code langue ('fr', 'en', None)

        Returns:
            bool: True si le texte correspond à la langue
        """
        if not language:
            return True

        text_lower = text.lower()

        if language == "fr":
            markers = [" le ", " la ", " les ", " de ", " des ", " et ", " à ", " pour ", " sur "]
            score = sum(1 for m in markers if m in text_lower)
            return score >= 1
        elif language == "en":
            markers = [" the ", " and ", " of ", " for ", " on ", " with ", " from "]
            score = sum(1 for m in markers if m in text_lower)
            return score >= 1

        return True

    @staticmethod
    def match_keywords(text: str, keywords: List[str]) -> bool:
        """Vérifie si le texte contient au moins un mot-clé."""
        if not keywords:
            return True

        text_lower = text.lower()
        return any(kw.lower() in text_lower for kw in keywords)

    @staticmethod
    def match_regex(text: str, patterns: List[str]) -> bool:
        """Vérifie si le texte correspond à au moins un pattern regex."""
        if not patterns:
            return True

        import re
        try:
            for pattern in patterns:
                if re.search(pattern, text, flags=re.IGNORECASE):
                    return True
            return False
        except re.error as e:
            logger.warning(f"Pattern regex invalide: {e}")
            return True

    @staticmethod
    def extract_domain(url: str) -> str:
        """Extrait le domaine d'une URL."""
        import re
        try:
            return re.sub(r"^https?://(www\.)?", "", url).split("/")[0]
        except Exception:
            return ""

    @staticmethod
    def match_domains(url: str, whitelist: List[str], blacklist: List[str]) -> bool:
        """Vérifie si le domaine est autorisé."""
        domain = RSSService.extract_domain(url)

        if whitelist and domain not in whitelist:
            return False
        if blacklist and domain in blacklist:
            return False

        return True

    @staticmethod
    def is_in_quiet_hours(now: datetime, start: Optional[str], end: Optional[str]) -> bool:
        """Vérifie si on est dans les heures silencieuses."""
        if not start or not end:
            return False

        try:
            start_time = datetime.strptime(start, "%H:%M").time()
            end_time = datetime.strptime(end, "%H:%M").time()
        except ValueError:
            return False

        now_time = now.time()

        if start_time < end_time:
            return start_time <= now_time <= end_time
        else:
            # Plage qui traverse minuit
            return now_time >= start_time or now_time <= end_time

    async def check_and_send_flux(
        self,
        flux: FluxInDB,
        collection: Any
    ) -> Dict[str, Any]:
        """
        Vérifie un flux RSS et envoie les nouveaux articles.

        Args:
            flux: Configuration du flux
            collection: Collection MongoDB pour mise à jour

        Returns:
            Dict avec statistiques (sent_count, error)
        """
        result = {"sent_count": 0, "error": None}

        try:
            # Parser le flux
            feed = self.parse_feed(flux.rssUrl)

            if not feed.entries:
                logger.debug(f"[Flux {flux.id}] Aucun article trouvé")
                return result

            # Trier les articles par date
            entries = self.sort_entries_by_date(feed.entries)
            now = datetime.now()
            max_per_run = flux.maxPerRun or 5
            seen_items = set()

            for entry in entries:
                if result["sent_count"] >= max_per_run:
                    break

                # Extraire les informations
                title = (entry.get("title") or "Sans titre").strip()
                link = self.extract_item_link(entry).strip()
                summary = (entry.get("summary", "") or entry.get("description", "")).strip()

                if not link:
                    continue

                # Vérifier les heures silencieuses
                if self.is_in_quiet_hours(now, flux.quietHoursStart, flux.quietHoursEnd):
                    continue

                # Déduplication
                if link in seen_items or already_sent(link):
                    continue
                seen_items.add(link)

                # Filtres
                full_text = f"{title}\n{summary}"

                if not self.filter_by_language(full_text, flux.language):
                    continue
                if flux.includeKeywords and not self.match_keywords(full_text, flux.includeKeywords):
                    continue
                if flux.excludeKeywords and self.match_keywords(full_text, flux.excludeKeywords):
                    continue
                if flux.regexInclude and not self.match_regex(full_text, flux.regexInclude):
                    continue
                if flux.regexExclude and self.match_regex(full_text, flux.regexExclude):
                    continue
                if not self.match_domains(link, flux.domainWhitelist or [], flux.domainBlacklist or []):
                    continue

                # Construire le message
                message = (flux.messageTemplate or "{title}\n{link}") \
                    .replace("{title}", title) \
                    .replace("{link}", link)

                if flux.mentionUserId:
                    message = f"<@{flux.mentionUserId}> {message}"
                if flux.mentionRoleId:
                    message = f"<@&{flux.mentionRoleId}> {message}"

                # Envoyer vers Discord
                try:
                    await send_to_discord(
                        discord_client=None,
                        target_id=flux.discordTarget,
                        content=message,
                        allow_embeds=bool(flux.allowEmbeds),
                        mode=flux.mode or "direct"
                    )

                    # Marquer comme envoyé
                    mark_as_sent(flux.id, link)
                    result["sent_count"] += 1

                    # Mettre à jour les métadonnées
                    try:
                        await collection.update_one(
                            {"_id": flux.id},
                            {
                                "$set": {
                                    "lastItem": link,
                                    "lastPubDate": self.extract_item_date(entry),
                                    "totalSent": flux.totalSent + result["sent_count"]
                                }
                            }
                        )
                    except Exception as db_err:
                        logger.warning(f"[Flux {flux.id}] Erreur MAJ métadonnées: {db_err}")

                except Exception as send_err:
                    logger.error(f"[Flux {flux.id}] Erreur envoi Discord: {send_err}")
                    continue

        except Exception as e:
            logger.error(f"[Flux {flux.id}] Erreur vérification flux: {e}")
            result["error"] = str(e)

        return result


# Instance singleton du service
rss_service = RSSService()
