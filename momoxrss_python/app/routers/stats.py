"""
Router pour les statistiques et le monitoring.
"""
import logging
import platform
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends
from motor.motor_asyncio import AsyncIOMotorCollection

from app.core.security import require_api_key
from app.core.dependencies import get_fluxes_collection, get_database
from app.services.scheduler_service import scheduler_service

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False

router = APIRouter(prefix="/stats", tags=["Statistiques"])
logger = logging.getLogger(__name__)


@router.get("", response_model=Dict[str, Any])
async def get_global_stats(
    collection: AsyncIOMotorCollection = Depends(get_fluxes_collection),
    _key: str = Depends(require_api_key)
):
    """Statistiques globales de l'application."""
    # Compter les flux
    total_fluxes = await collection.count_documents({})
    active_fluxes = await collection.count_documents({"active": True})
    inactive_fluxes = await collection.count_documents({"active": False})

    # Total d'articles envoyés
    pipeline = [
        {"$group": {"_id": None, "total": {"$sum": "$totalSent"}}}
    ]
    cursor = collection.aggregate(pipeline)
    total_sent = 0
    async for doc in cursor:
        total_sent = doc.get("total", 0)

    # Flux avec erreurs
    flux_with_errors = await collection.count_documents({"lastError": {"$exists": True}})

    # Info scheduler
    jobs_info = scheduler_service.get_jobs_info()

    return {
        "fluxes": {
            "total": total_fluxes,
            "active": active_fluxes,
            "inactive": inactive_fluxes,
            "with_errors": flux_with_errors
        },
        "articles": {
            "total_sent": total_sent
        },
        "scheduler": {
            "running": scheduler_service.scheduler.running if scheduler_service.scheduler else False,
            "jobs_count": len(jobs_info),
            "aggressive_mode": scheduler_service.aggressive_mode
        }
    }


@router.get("/categories", response_model=Dict[str, Any])
async def get_category_stats(
    collection: AsyncIOMotorCollection = Depends(get_fluxes_collection),
    _key: str = Depends(require_api_key)
):
    """Statistiques par catégorie."""
    pipeline = [
        {
            "$group": {
                "_id": "$category",
                "count": {"$sum": 1},
                "active": {"$sum": {"$cond": ["$active", 1, 0]}},
                "total_sent": {"$sum": "$totalSent"}
            }
        },
        {"$sort": {"count": -1}}
    ]

    categories = {}
    cursor = collection.aggregate(pipeline)
    async for doc in cursor:
        cat_name = doc["_id"] or "Sans catégorie"
        categories[cat_name] = {
            "count": doc["count"],
            "active": doc["active"],
            "total_sent": doc["total_sent"]
        }

    return {
        "categories": categories,
        "total_categories": len(categories)
    }


@router.get("/top-fluxes", response_model=List[Dict[str, Any]])
async def get_top_fluxes(
    limit: int = 10,
    collection: AsyncIOMotorCollection = Depends(get_fluxes_collection),
    _key: str = Depends(require_api_key)
):
    """Top flux par nombre d'articles envoyés."""
    cursor = collection.find(
        {},
        {"name": 1, "totalSent": 1, "category": 1, "active": 1}
    ).sort("totalSent", -1).limit(limit)

    top_fluxes = []
    async for doc in cursor:
        top_fluxes.append({
            "id": str(doc["_id"]),
            "name": doc.get("name", "Sans nom"),
            "category": doc.get("category"),
            "total_sent": doc.get("totalSent", 0),
            "active": doc.get("active", False)
        })

    return top_fluxes


@router.get("/system", response_model=Dict[str, Any])
async def get_system_info(_key: str = Depends(require_api_key)):
    """Informations système."""
    info = {
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "python_version": platform.python_version()
        }
    }

    if PSUTIL_AVAILABLE:
        # CPU
        cpu_percent = psutil.cpu_percent(interval=1, percpu=True)
        info["cpu"] = {
            "count": psutil.cpu_count(),
            "percent": sum(cpu_percent) / len(cpu_percent),
            "per_cpu": cpu_percent
        }

        # Mémoire
        mem = psutil.virtual_memory()
        info["memory"] = {
            "total": mem.total,
            "available": mem.available,
            "percent": mem.percent,
            "used": mem.used
        }

        # Disque
        disk = psutil.disk_usage('/')
        info["disk"] = {
            "total": disk.total,
            "used": disk.used,
            "free": disk.free,
            "percent": disk.percent
        }

    else:
        info["psutil"] = "Non disponible - installez psutil pour plus d'infos"

    return info


@router.get("/errors", response_model=List[Dict[str, Any]])
async def get_flux_errors(
    collection: AsyncIOMotorCollection = Depends(get_fluxes_collection),
    _key: str = Depends(require_api_key)
):
    """Liste les flux avec des erreurs."""
    cursor = collection.find(
        {"lastError": {"$exists": True}},
        {"name": 1, "rssUrl": 1, "lastError": 1, "lastCheck": 1, "active": 1}
    )

    errors = []
    async for doc in cursor:
        errors.append({
            "id": str(doc["_id"]),
            "name": doc.get("name", "Sans nom"),
            "rss_url": doc.get("rssUrl"),
            "error": doc.get("lastError"),
            "last_check": doc.get("lastCheck"),
            "active": doc.get("active", False)
        })

    return errors


@router.get("/scheduler/jobs", response_model=List[Dict[str, Any]])
async def get_scheduler_jobs(_key: str = Depends(require_api_key)):
    """Liste les jobs du scheduler."""
    return scheduler_service.get_jobs_info()


@router.post("/scheduler/reload", response_model=Dict[str, Any])
async def reload_scheduler(_key: str = Depends(require_api_key)):
    """Recharge tous les jobs du scheduler."""
    result = await scheduler_service.reload_all_schedules()
    return result


@router.post("/scheduler/aggressive-mode", response_model=Dict[str, Any])
async def toggle_aggressive_mode(
    enabled: bool,
    _key: str = Depends(require_api_key)
):
    """Active/désactive le mode agressif (tous les flux à 10s)."""
    result = await scheduler_service.set_aggressive_mode(enabled)
    return result
