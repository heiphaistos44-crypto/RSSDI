"""
Router pour la gestion des flux RSS.
"""
import logging
from typing import List, Dict, Any, Optional
from bson.objectid import ObjectId
from fastapi import APIRouter, HTTPException, Depends, status
from motor.motor_asyncio import AsyncIOMotorCollection

from app.core.security import require_api_key
from app.core.dependencies import get_fluxes_collection
from app.services.scheduler_service import scheduler_service
from app.services.rss_service import rss_service
from app.utils.url_resolver import url_resolver
from models import FluxCreate, FluxUpdate, FluxInDB, RssArticle
from discord_utils import isValidDiscordId

router = APIRouter(prefix="/fluxes", tags=["Flux RSS"])
logger = logging.getLogger(__name__)


@router.get("", response_model=List[FluxInDB])
async def list_fluxes(
    active: Optional[bool] = None,
    category: Optional[str] = None,
    collection: AsyncIOMotorCollection = Depends(get_fluxes_collection),
    _key: str = Depends(require_api_key)
):
    """
    Liste tous les flux RSS avec filtres optionnels.

    Args:
        active: Filtrer par statut actif/inactif
        category: Filtrer par catégorie
    """
    query = {}
    if active is not None:
        query["active"] = active
    if category:
        query["category"] = category

    cursor = collection.find(query)
    fluxes = []

    async for doc in cursor:
        flux_id = str(doc["_id"]) if isinstance(doc["_id"], ObjectId) else str(doc["_id"])
        doc_data = {k: v for k, v in doc.items() if k != "_id"}
        doc_data["id"] = flux_id
        fluxes.append(FluxInDB(**doc_data))

    return fluxes


@router.get("/{flux_id}", response_model=FluxInDB)
async def get_flux(
    flux_id: str,
    collection: AsyncIOMotorCollection = Depends(get_fluxes_collection),
    _key: str = Depends(require_api_key)
):
    """Récupère un flux par son ID."""
    try:
        oid = ObjectId(flux_id) if ObjectId.is_valid(flux_id) else flux_id
    except Exception:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "ID invalide")

    doc = await collection.find_one({"_id": oid})
    if not doc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Flux non trouvé")

    doc_data = {k: v for k, v in doc.items() if k != "_id"}
    doc_data["id"] = flux_id
    return FluxInDB(**doc_data)


@router.post("", response_model=Dict[str, str], status_code=status.HTTP_201_CREATED)
async def create_flux(
    flux: FluxCreate,
    collection: AsyncIOMotorCollection = Depends(get_fluxes_collection),
    _key: str = Depends(require_api_key)
):
    """
    Crée un nouveau flux RSS.

    Valide les IDs Discord et résout les URLs selon le type de source.
    """
    # Validation Discord ID
    if not isValidDiscordId(flux.discordTarget):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"ID Discord invalide: {flux.discordTarget}"
        )

    # Résolution de l'URL
    resolved_url = url_resolver.resolve(flux.rssUrl, flux.sourceType or "rss")

    # Préparation du document
    doc = flux.model_dump()
    doc["rssUrl"] = resolved_url
    doc["totalSent"] = 0
    doc["active"] = doc.get("active", True)

    # Insertion
    result = await collection.insert_one(doc)
    flux_id = str(result.inserted_id)

    # Planifier le flux si actif
    if doc.get("active"):
        flux_db = FluxInDB(**{**doc, "id": flux_id})
        await scheduler_service.schedule_flux(flux_db)

    logger.info(f"✅ Flux créé: {flux_id}")
    return {"id": flux_id, "message": "Flux créé avec succès"}


@router.put("/{flux_id}", response_model=Dict[str, str])
async def update_flux(
    flux_id: str,
    flux_update: FluxUpdate,
    collection: AsyncIOMotorCollection = Depends(get_fluxes_collection),
    _key: str = Depends(require_api_key)
):
    """Met à jour un flux existant."""
    try:
        oid = ObjectId(flux_id) if ObjectId.is_valid(flux_id) else flux_id
    except Exception:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "ID invalide")

    # Vérifier que le flux existe
    existing = await collection.find_one({"_id": oid})
    if not existing:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Flux non trouvé")

    # Préparer les mises à jour (exclure les None)
    update_data = flux_update.model_dump(exclude_unset=True)

    # Résoudre l'URL si elle change
    if "rssUrl" in update_data and "sourceType" in update_data:
        update_data["rssUrl"] = url_resolver.resolve(
            update_data["rssUrl"],
            update_data["sourceType"]
        )

    # Valider le Discord ID si modifié
    if "discordTarget" in update_data:
        if not isValidDiscordId(update_data["discordTarget"]):
            raise HTTPException(
                status.HTTP_400_BAD_REQUEST,
                f"ID Discord invalide: {update_data['discordTarget']}"
            )

    # Mettre à jour
    await collection.update_one(
        {"_id": oid},
        {"$set": update_data}
    )

    # Replanifier le flux
    updated_doc = await collection.find_one({"_id": oid})
    if updated_doc:
        flux_db = FluxInDB(
            **{k: v for k, v in updated_doc.items() if k != "_id"},
            id=flux_id
        )

        if flux_db.active:
            await scheduler_service.schedule_flux(flux_db)
        else:
            await scheduler_service.unschedule_flux(flux_id)

    logger.info(f"✅ Flux mis à jour: {flux_id}")
    return {"id": flux_id, "message": "Flux mis à jour avec succès"}


@router.delete("/{flux_id}", response_model=Dict[str, str])
async def delete_flux(
    flux_id: str,
    collection: AsyncIOMotorCollection = Depends(get_fluxes_collection),
    _key: str = Depends(require_api_key)
):
    """Supprime un flux."""
    try:
        oid = ObjectId(flux_id) if ObjectId.is_valid(flux_id) else flux_id
    except Exception:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "ID invalide")

    result = await collection.delete_one({"_id": oid})
    if result.deleted_count == 0:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Flux non trouvé")

    # Désactiver le job
    await scheduler_service.unschedule_flux(flux_id)

    logger.info(f"❌ Flux supprimé: {flux_id}")
    return {"id": flux_id, "message": "Flux supprimé avec succès"}


@router.post("/{flux_id}/check", response_model=Dict[str, Any])
async def check_flux_now(
    flux_id: str,
    collection: AsyncIOMotorCollection = Depends(get_fluxes_collection),
    _key: str = Depends(require_api_key)
):
    """Force la vérification immédiate d'un flux."""
    try:
        oid = ObjectId(flux_id) if ObjectId.is_valid(flux_id) else flux_id
    except Exception:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "ID invalide")

    doc = await collection.find_one({"_id": oid})
    if not doc:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Flux non trouvé")

    flux = FluxInDB(**{k: v for k, v in doc.items() if k != "_id"}, id=flux_id)

    result = await rss_service.check_and_send_flux(flux, collection)

    return {
        "flux_id": flux_id,
        "sent_count": result["sent_count"],
        "error": result["error"],
        "message": f"{result['sent_count']} article(s) envoyé(s)"
    }


@router.post("/preview", response_model=List[RssArticle])
async def preview_rss_feed(
    rss_url: str,
    source_type: str = "rss",
    count: int = 5,
    _key: str = Depends(require_api_key)
):
    """
    Prévisualise les articles d'un flux RSS sans créer de flux.

    Args:
        rss_url: URL du flux
        source_type: Type de source (youtube, facebook, instagram, tiktok, rss)
        count: Nombre d'articles à retourner
    """
    # Résoudre l'URL
    resolved_url = url_resolver.resolve(rss_url, source_type)

    # Parser le flux
    feed = rss_service.parse_feed(resolved_url)

    if not feed.entries:
        return []

    # Extraire les articles
    articles = []
    for entry in feed.entries[:count]:
        article = RssArticle(
            title=entry.get("title", "Sans titre"),
            link=rss_service.extract_item_link(entry) or "",
            description=entry.get("summary", "") or entry.get("description", ""),
            pubDate=rss_service.extract_item_date(entry)
        )
        articles.append(article)

    return articles


@router.post("/bulk-actions", response_model=Dict[str, Any])
async def bulk_actions(
    action: str,
    flux_ids: List[str],
    collection: AsyncIOMotorCollection = Depends(get_fluxes_collection),
    _key: str = Depends(require_api_key)
):
    """
    Actions en lot sur plusieurs flux.

    Actions disponibles: activate, deactivate, delete
    """
    valid_actions = ["activate", "deactivate", "delete"]
    if action not in valid_actions:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            f"Action invalide. Utilisez: {', '.join(valid_actions)}"
        )

    results = {"success": [], "errors": []}

    for flux_id in flux_ids:
        try:
            oid = ObjectId(flux_id) if ObjectId.is_valid(flux_id) else flux_id

            if action == "delete":
                result = await collection.delete_one({"_id": oid})
                if result.deleted_count > 0:
                    await scheduler_service.unschedule_flux(flux_id)
                    results["success"].append(flux_id)
                else:
                    results["errors"].append({"id": flux_id, "error": "Non trouvé"})

            else:  # activate or deactivate
                active = action == "activate"
                result = await collection.update_one(
                    {"_id": oid},
                    {"$set": {"active": active}}
                )

                if result.matched_count > 0:
                    # Gérer le scheduling
                    if active:
                        doc = await collection.find_one({"_id": oid})
                        if doc:
                            flux = FluxInDB(
                                **{k: v for k, v in doc.items() if k != "_id"},
                                id=flux_id
                            )
                            await scheduler_service.schedule_flux(flux)
                    else:
                        await scheduler_service.unschedule_flux(flux_id)

                    results["success"].append(flux_id)
                else:
                    results["errors"].append({"id": flux_id, "error": "Non trouvé"})

        except Exception as e:
            results["errors"].append({"id": flux_id, "error": str(e)})

    return {
        "action": action,
        "total": len(flux_ids),
        "success_count": len(results["success"]),
        "error_count": len(results["errors"]),
        "results": results
    }
