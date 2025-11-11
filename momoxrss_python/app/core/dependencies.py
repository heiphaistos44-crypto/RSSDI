"""
Dépendances partagées pour l'injection de dépendances FastAPI.
"""
from typing import Optional, AsyncGenerator
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase, AsyncIOMotorCollection
from fastapi import Depends
from app.core.config import get_settings

settings = get_settings()

# Instances globales (initialisées au démarrage)
_mongo_client: Optional[AsyncIOMotorClient] = None
_database: Optional[AsyncIOMotorDatabase] = None


def get_mongo_client() -> AsyncIOMotorClient:
    """
    Retourne le client MongoDB global.

    Returns:
        AsyncIOMotorClient: Client MongoDB

    Raises:
        RuntimeError: Si le client n'a pas été initialisé
    """
    if _mongo_client is None:
        raise RuntimeError("MongoDB client not initialized. Call init_db() first.")
    return _mongo_client


def get_database() -> AsyncIOMotorDatabase:
    """
    Retourne la base de données MongoDB.

    Returns:
        AsyncIOMotorDatabase: Base de données MongoDB

    Raises:
        RuntimeError: Si la base n'a pas été initialisée
    """
    if _database is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    return _database


def get_fluxes_collection(
    db: AsyncIOMotorDatabase = Depends(get_database)
) -> AsyncIOMotorCollection:
    """
    Retourne la collection des flux RSS.

    Args:
        db: Base de données MongoDB (injecté)

    Returns:
        AsyncIOMotorCollection: Collection 'fluxes'
    """
    return db.fluxes


async def init_mongodb() -> None:
    """
    Initialise la connexion MongoDB au démarrage de l'application.
    """
    global _mongo_client, _database

    _mongo_client = AsyncIOMotorClient(
        settings.mongo_url,
        serverSelectionTimeoutMS=5000
    )
    _database = _mongo_client[settings.mongo_db]

    # Vérifier la connexion
    await _mongo_client.admin.command('ping')
    print(f"✅ MongoDB connecté: {settings.mongo_db}")


async def close_mongodb() -> None:
    """
    Ferme proprement la connexion MongoDB à l'arrêt de l'application.
    """
    global _mongo_client, _database

    if _mongo_client:
        _mongo_client.close()
        _mongo_client = None
        _database = None
        print("✅ MongoDB déconnecté")
