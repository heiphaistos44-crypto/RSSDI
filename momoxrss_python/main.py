"""
RSSDI - RSS Discord Integration v4.0.0
Application FastAPI refactorisée pour une meilleure maintenabilité.

Architecture modulaire:
- app/core: Configuration, sécurité, dépendances
- app/routers: Endpoints API organisés par domaine
- app/services: Logique métier (RSS, Scheduler)
- app/utils: Utilitaires réutilisables
"""
import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path

# Configuration
from app.core.config import get_settings
from app.core.dependencies import init_mongodb, close_mongodb, get_database

# Services
from app.services.scheduler_service import scheduler_service

# Routers
from app.routers import fluxes, discord, stats

# Utilitaires
from db import init_db, cleanup_old_entries
from discord_utils import initialize_discord_client, close_discord_client

# Configuration du logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Gestion du cycle de vie de l'application.
    S'exécute au démarrage et à l'arrêt.
    """
    # ===== DÉMARRAGE =====
    logger.info(f"🚀 Démarrage de {settings.app_name} v{settings.app_version}")

    # 1. Initialiser MongoDB
    try:
        await init_mongodb()
    except Exception as e:
        logger.error(f"❌ Erreur connexion MongoDB: {e}")
        raise

    # 2. Initialiser la base SQLite (déduplication)
    try:
        init_db()
        logger.info("✅ Base SQLite initialisée")
    except Exception as e:
        logger.warning(f"⚠️  Erreur init SQLite: {e}")

    # 3. Initialiser le client Discord
    try:
        await initialize_discord_client()
    except Exception as e:
        logger.error(f"❌ Erreur init Discord: {e}")

    # 4. Initialiser le scheduler
    try:
        db = get_database()
        collection = db.fluxes
        scheduler_service.init(collection)
        scheduler_service.start()

        # Charger et planifier tous les flux actifs
        await scheduler_service.reload_all_schedules()
    except Exception as e:
        logger.error(f"❌ Erreur init scheduler: {e}")
        raise

    # 5. Nettoyer les anciennes entrées de déduplication
    try:
        deleted = cleanup_old_entries(settings.sent_items_retention_days)
        logger.info(f"🗑️  {deleted} anciennes entrées nettoyées")
    except Exception as e:
        logger.warning(f"⚠️  Erreur nettoyage DB: {e}")

    logger.info("✅ Application démarrée avec succès!")

    yield  # L'application tourne ici

    # ===== ARRÊT =====
    logger.info("🛑 Arrêt de l'application...")

    # 1. Arrêter le scheduler
    try:
        scheduler_service.shutdown()
    except Exception as e:
        logger.warning(f"⚠️  Erreur arrêt scheduler: {e}")

    # 2. Fermer Discord
    try:
        await close_discord_client()
    except Exception as e:
        logger.warning(f"⚠️  Erreur fermeture Discord: {e}")

    # 3. Fermer MongoDB
    try:
        await close_mongodb()
    except Exception as e:
        logger.warning(f"⚠️  Erreur fermeture MongoDB: {e}")

    logger.info("👋 Application arrêtée proprement")


# Créer l'application FastAPI
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="""
    RSSDI - Système de surveillance RSS avec notifications Discord.

    ## Fonctionnalités

    - **Flux RSS**: Gestion complète des flux RSS/Atom
    - **Discord**: Envoi automatique vers Discord
    - **Filtrage**: Mots-clés, regex, domaines, langue
    - **Planification**: Vérifications périodiques configurables
    - **Statistiques**: Monitoring complet de l'application

    ## Architecture v4.0

    - Architecture modulaire et maintenable
    - Performances optimisées
    - Sécurité renforcée (rate limiting, API key)
    - Code moderne avec type hints complets
    """,
    lifespan=lifespan,
    docs_url="/api/docs",
    redoc_url="/api/redoc"
)

# CORS
origins = ["*"] if settings.allowed_origin == "*" else [settings.allowed_origin]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclure les routers
app.include_router(fluxes.router, prefix="/api/v1")
app.include_router(discord.router, prefix="/api/v1")
app.include_router(stats.router, prefix="/api/v1")

# Servir les fichiers statiques
static_path = Path(__file__).parent / "static"
if static_path.exists():
    app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

# Routes de base
@app.get("/", include_in_schema=False)
async def root():
    """Redirige vers le dashboard."""
    return RedirectResponse(url="/dashboard")


@app.get("/dashboard", include_in_schema=False)
async def dashboard():
    """Affiche le dashboard web."""
    static_file = Path(__file__).parent / "static" / "index.html"
    if static_file.exists():
        return FileResponse(static_file)
    return {"message": "Dashboard non disponible"}


@app.get("/health")
async def health_check():
    """Endpoint de santé pour les health checks."""
    return {
        "status": "healthy",
        "app": settings.app_name,
        "version": settings.app_version
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=settings.port,
        reload=settings.debug,
        log_level="info"
    )
