from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import uuid

# -----------------------------
# Modèles Flux
# -----------------------------

class FluxBase(BaseModel):
    name: Optional[str] = Field(None, description="Nom du flux")
    category: Optional[str] = Field("general", description="Catégorie du flux")
    rssUrl: Optional[str] = Field(None, description="URL RSS ou source")
    sourceType: str = Field("web", description="Type de source (web, youtube, facebook, instagram, tiktok)")
    discordTarget: str = Field(..., description="ID du salon ou thread Discord")
    interval: int = Field(300, description="Intervalle en secondes (min 60)")
    mode: str = Field("direct", description="Mode de publication (direct ou thread)")
    active: bool = Field(True, description="Flux actif ou non")
    allowEmbeds: bool = Field(False, description="Autoriser les embeds Discord")

    # Mentions et template
    messageTemplate: Optional[str] = Field(None, description="Template du message")
    mentionUserId: Optional[str] = Field(None, description="ID utilisateur à mentionner")
    mentionRoleId: Optional[str] = Field(None, description="ID rôle à mentionner")

    # Filtres
    includeKeywords: Optional[List[str]] = Field(default_factory=list)
    excludeKeywords: Optional[List[str]] = Field(default_factory=list)
    regexInclude: Optional[List[str]] = Field(default_factory=list)
    regexExclude: Optional[List[str]] = Field(default_factory=list)
    domainWhitelist: Optional[List[str]] = Field(default_factory=list)
    domainBlacklist: Optional[List[str]] = Field(default_factory=list)
    language: Optional[str] = Field(None, description="Langue attendue (fr/en)")

    # Déduplication et limites
    dedupeWindowHours: Optional[int] = Field(24, description="Fenêtre de déduplication en heures")
    maxPerRun: Optional[int] = Field(5, description="Nombre max d’articles par exécution")
    quietHoursStart: Optional[str] = Field(None, description="Heure calme début (HH:MM)")
    quietHoursEnd: Optional[str] = Field(None, description="Heure calme fin (HH:MM)")
    dailyCap: Optional[int] = Field(None, description="Plafond quotidien d’articles")

class FluxInDB(FluxBase):
    @property
    def checkInterval(self) -> int:
        # Pour compatibilité avec l'ancien code qui attend checkInterval
        return getattr(self, 'interval', 300)
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Identifiant unique du flux")
    createdAt: datetime = Field(default_factory=datetime.utcnow)
    lastError: Optional[str] = None
    lastItem: Optional[str] = None
    lastPubDate: Optional[int] = None
    totalSent: int = 0

class FluxCreate(FluxBase):
    pass

class FluxUpdate(BaseModel):
    name: Optional[str] = None
    newRssUrl: Optional[str] = None
    sourceType: Optional[str] = None
    discordTarget: Optional[str] = None
    interval: Optional[int] = None
    mode: Optional[str] = None
    active: Optional[bool] = None
    allowEmbeds: Optional[bool] = None
    messageTemplate: Optional[str] = None
    mentionUserId: Optional[str] = None
    mentionRoleId: Optional[str] = None

class RssArticle(BaseModel):
    title: str
    link: str
    date: Optional[str] = None

# -----------------------------
# Réponses API
# -----------------------------

class StatsResponse(BaseModel):
    jobCount: int
    activeFluxCount: int
    totalFluxCount: int
    totalSent: int
    schedulerStatus: str
    categoryJobs: List[str]
    aggressiveMode: bool

class SendResult(BaseModel):
    requested: int
    sent: int
    errors: List[str]
