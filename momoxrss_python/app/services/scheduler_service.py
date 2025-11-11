"""
Service de planification - Gestion du scheduler APScheduler.
"""
import logging
from typing import Optional, Dict, Any, List
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from motor.motor_asyncio import AsyncIOMotorCollection

from app.core.config import get_settings
from app.services.rss_service import rss_service
from models import FluxInDB

settings = get_settings()
logger = logging.getLogger(__name__)


class SchedulerService:
    """Service de gestion du scheduler pour les vérifications RSS."""

    def __init__(self):
        self.scheduler: Optional[AsyncIOScheduler] = None
        self.aggressive_mode: bool = False
        self.collection: Optional[AsyncIOMotorCollection] = None

    def init(self, collection: AsyncIOMotorCollection) -> None:
        """
        Initialise le scheduler.

        Args:
            collection: Collection MongoDB des flux
        """
        self.collection = collection
        self.scheduler = AsyncIOScheduler()
        logger.info("✅ Scheduler initialisé")

    def start(self) -> None:
        """Démarre le scheduler."""
        if self.scheduler and not self.scheduler.running:
            self.scheduler.start()
            logger.info("✅ Scheduler démarré")

    def shutdown(self) -> None:
        """Arrête proprement le scheduler."""
        if self.scheduler and self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("✅ Scheduler arrêté")

    async def schedule_flux(self, flux: FluxInDB) -> Dict[str, Any]:
        """
        Planifie ou met à jour un job pour un flux.

        Args:
            flux: Configuration du flux

        Returns:
            Dict avec job_id et next_run
        """
        if not self.scheduler:
            raise RuntimeError("Scheduler not initialized")

        job_id = f"flux_{flux.id}"

        # Déterminer l'intervalle
        if self.aggressive_mode:
            interval_seconds = 10
        else:
            interval_seconds = flux.checkInterval or settings.default_check_interval

        # Supprimer l'ancien job si existe
        existing_job = self.scheduler.get_job(job_id)
        if existing_job:
            existing_job.remove()

        # Créer le nouveau job
        trigger = IntervalTrigger(seconds=interval_seconds)
        job = self.scheduler.add_job(
            self._check_flux_job,
            trigger=trigger,
            id=job_id,
            args=[flux],
            replace_existing=True,
            max_instances=1
        )

        next_run = job.next_run_time.isoformat() if job.next_run_time else None

        logger.info(f"📅 Job planifié: {job_id} (intervalle: {interval_seconds}s)")

        return {
            "job_id": job_id,
            "interval": interval_seconds,
            "next_run": next_run
        }

    async def _check_flux_job(self, flux: FluxInDB) -> None:
        """
        Job exécuté périodiquement pour vérifier un flux.

        Args:
            flux: Configuration du flux
        """
        if not flux.active:
            return

        try:
            result = await rss_service.check_and_send_flux(flux, self.collection)

            if result["sent_count"] > 0:
                logger.info(f"📨 [Flux {flux.id}] {result['sent_count']} article(s) envoyé(s)")

            if result["error"]:
                logger.error(f"❌ [Flux {flux.id}] Erreur: {result['error']}")

        except Exception as e:
            logger.error(f"❌ [Flux {flux.id}] Erreur job: {e}")

    async def unschedule_flux(self, flux_id: str) -> bool:
        """
        Supprime la planification d'un flux.

        Args:
            flux_id: ID du flux

        Returns:
            bool: True si supprimé, False si n'existait pas
        """
        if not self.scheduler:
            raise RuntimeError("Scheduler not initialized")

        job_id = f"flux_{flux_id}"
        job = self.scheduler.get_job(job_id)

        if job:
            job.remove()
            logger.info(f"❌ Job supprimé: {job_id}")
            return True

        return False

    async def reload_all_schedules(self) -> Dict[str, Any]:
        """
        Recharge tous les jobs depuis la base de données.

        Returns:
            Dict avec scheduled_count et erreurs
        """
        if self.collection is None:
            raise RuntimeError("Collection not set")
        
        if not self.scheduler:
            raise RuntimeError("Scheduler not initialized")

        # Supprimer tous les jobs existants
        self.scheduler.remove_all_jobs()
        logger.info("🔄 Rechargement de tous les jobs...")

        scheduled_count = 0
        errors = []

        # Récupérer tous les flux actifs
        cursor = self.collection.find({"active": True})
        async for flux_data in cursor:
            try:
                flux = FluxInDB(**flux_data)
                await self.schedule_flux(flux)
                scheduled_count += 1
            except Exception as e:
                logger.error(f"Erreur planification flux {flux_data.get('_id')}: {e}")
                errors.append({"flux_id": str(flux_data.get("_id")), "error": str(e)})

        logger.info(f"✅ {scheduled_count} flux planifiés")

        return {
            "scheduled_count": scheduled_count,
            "errors": errors
        }

    async def set_aggressive_mode(self, enabled: bool) -> Dict[str, Any]:
        """
        Active/désactive le mode agressif (tous les flux à 10s).

        Args:
            enabled: True pour activer

        Returns:
            Dict avec status et scheduled_count
        """
        self.aggressive_mode = enabled

        if enabled:
            logger.warning("⚡ MODE AGRESSIF ACTIVÉ - Tous les flux à 10s")
        else:
            logger.info("🐢 Mode agressif désactivé")

        # Recharger tous les schedules avec les nouveaux intervalles
        result = await self.reload_all_schedules()

        return {
            "aggressive_mode": self.aggressive_mode,
            "scheduled_count": result["scheduled_count"]
        }

    def get_jobs_info(self) -> List[Dict[str, Any]]:
        """
        Retourne les informations sur tous les jobs planifiés.

        Returns:
            List[Dict]: Liste des jobs avec leurs infos
        """
        if not self.scheduler:
            return []

        jobs_info = []
        for job in self.scheduler.get_jobs():
            jobs_info.append({
                "id": job.id,
                "next_run": job.next_run_time.isoformat() if job.next_run_time else None,
                "trigger": str(job.trigger)
            })

        return jobs_info


# Instance singleton du service
scheduler_service = SchedulerService()
