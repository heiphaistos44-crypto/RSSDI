# RSSDI - RSS Discord Integration

## 🚀 Nouvelles fonctionnalités v3.6.0

### ✨ Améliorations du Dashboard

- **Section d'erreurs dédiée** : Panneau flottant avec diagnostics détaillés des erreurs
- **Statistiques par catégorie** : Vue d'ensemble des flux organisés par catégorie
- **Actions en lot** : Sélection multiple pour activer/désactiver/supprimer plusieurs flux
- **Recherche avancée** : Filtres multiples (catégorie, type, statut, erreurs, intervalle)
- **Diagnostic Discord amélioré** : Test de connexion, redémarrage bot, infos détaillées
- **Catégories personnalisées** : Saisie manuelle de noms de catégories
- **Export/Import** : Sauvegarde et restauration complète des configurations
- **Monitoring système** : Informations détaillées sur l'état du système

### 🔧 Améliorations techniques

- **Résolution d'URL améliorée** : Support des nouveaux formats YouTube (@username, /c/)
- **Gestion d'erreurs robuste** : Enregistrement et diagnostic automatique des erreurs
- **Client Discord optimisé** : Initialisation automatique et gestion améliorée des connexions
- **APIs étendues** : Nouvelles routes pour diagnostics, recherche, actions en lot et gestion système
- **Logging amélioré** : Messages détaillés pour diagnostiquer les problèmes Discord
- **Interface modernisée** : Design amélioré avec outils de gestion avancés

## 📋 Fonctionnalités principales

### 🎯 Gestion des flux RSS
- Support de multiples sources : RSS/Atom, YouTube, Facebook, Instagram, TikTok
- Catégorisation des flux (general, news, sports, tech, finance, gaming, music, errors)
- Filtres avancés : mots-clés, regex, domaines, langue
- Déduplication intelligente et limitations temporelles

### 🤖 Intégration Discord
- Envoi automatique vers salons Discord
- Support des modes direct et thread
- Personnalisation des messages avec templates
- Mentions d'utilisateurs et rôles
- Gestion des embeds

### 📊 Monitoring et statistiques
- Dashboard web moderne et réactif
- Statistiques en temps réel par catégorie
- Diagnostics d'erreurs détaillés
- Planification flexible avec mode agressif

## 🛠️ Installation

### Prérequis
- Python 3.8+
- MongoDB
- Bot Discord avec token
- Docker & Docker Compose (pour l'installation Docker)

### 🐳 Installation Docker (Recommandée)

#### Démarrage rapide avec script d'aide

1. **Cloner le projet**
```bash
git clone <repository-url>
cd momoxrss_python
```

2. **Utilisation du script d'aide (Windows)**
```powershell
# Exécution interactive
.\docker-helper.ps1

# Ou directement
.\docker-helper.ps1 start
```

3. **Utilisation du script d'aide (Linux/Mac)**
```bash
# Rendre exécutable
chmod +x docker-helper.sh

# Exécution interactive
./docker-helper.sh

# Ou directement
./docker-helper.sh start
```

#### Démarrage manuel Docker

1. **Configuration environnement**
```bash
cp .env.example .env
# Éditer .env avec vos paramètres
```

2. **Démarrage des services**
```bash
docker-compose up -d
```

3. **Vérification des services**
```bash
docker-compose ps
docker-compose logs
```

### 📦 Installation manuelle

1. **Cloner le projet**
```bash
git clone <repository-url>
cd momoxrss_python
```

2. **Installation des dépendances**
```bash
pip install -r requirements.txt
```

3. **Configuration environnement**
```bash
cp .env.example .env
# Éditer .env avec vos paramètres
```

4. **Variables d'environnement requises**
```env
# Configuration de base
API_KEY=your_secret_api_key_here
PORT=3000

# MongoDB
MONGO_URL=mongodb://localhost:27017/momoxrss
MONGO_DB=momoxrss

# MongoDB Docker (optionnel)
MONGO_ROOT_USER=admin
MONGO_ROOT_PASSWORD=changeme

# Discord Bot Token (requis)
DISCORD_TOKEN=your_discord_bot_token_here

# RSSHub pour réseaux sociaux
RSSHUB_BASE=https://rsshub.app
```

5. **Démarrage**
```bash
python main.py
```

6. **Accès au dashboard**
- Interface web : `http://localhost:3000/dashboard`
- API : `http://localhost:3000/api/v1/`

### 🔧 Scripts d'aide

Le projet inclut des scripts pour faciliter le déploiement Docker :

- **`docker-helper.ps1`** (Windows PowerShell)
- **`docker-helper.sh`** (Linux/Mac/WSL)

**Fonctionnalités des scripts :**
- Vérification automatique des prérequis
- Test de connectivité réseau
- Démarrage avec diagnostics
- Nettoyage des containers et volumes
- Affichage des logs et statut
- Interface interactive ou commandes directes

**Utilisation :**
```bash
# Mode interactif
./docker-helper.sh

# Commandes directes
./docker-helper.sh check    # Vérifier prérequis
./docker-helper.sh start    # Démarrer avec diagnostics
./docker-helper.sh stop     # Arrêter les services
./docker-helper.sh clean    # Nettoyer containers/volumes
./docker-helper.sh logs     # Afficher logs
./docker-helper.sh status   # Statut des services
```

## 🎛️ Utilisation du Dashboard

### Section d'erreurs
- **Panneau automatique** : Apparaît quand des flux sont en erreur
- **Diagnostics détaillés** : Types d'erreurs groupés (Discord, RSS, HTTP, Timeout)
- **Actions rapides** : Réessayer, éditer ou corriger en lot
- **Réduction/expansion** : Interface adaptative

### Actions en lot
1. Sélectionner les flux avec les checkboxes
2. Choisir l'action : activer, désactiver, changer catégorie, etc.
3. Saisir les paramètres si nécessaire
4. Exécuter l'action sur tous les flux sélectionnés

### Recherche avancée
- **Filtres multiples** : Catégorie, type de source, statut
- **Recherche textuelle** : Nom, URL, salon Discord
- **Filtres d'erreurs** : Avec/sans erreurs
- **Intervalles** : Plage de fréquence de vérification

### Statistiques par catégorie
- **Métriques complètes** : Total, actifs, erreurs, envoyés
- **Indicateur de santé** : Vert (sain) ou orange (problèmes)
- **Vue d'ensemble** : Performance par catégorie

## 🔍 API Endpoints

### Nouvelles routes v3.5.0

#### Actions en lot
```http
POST /api/v1/bulk-actions
Content-Type: application/json
X-API-Key: your_api_key

{
  "action": "activate|deactivate|delete|change_category|change_interval",
  "fluxIds": ["id1", "id2", ...],
  "params": { "category": "news", "interval": 600 }
}
```

#### Statistiques par catégorie
```http
GET /api/v1/stats/categories
X-API-Key: your_api_key
```

#### Recherche avancée
```http
POST /api/v1/search-fluxes
Content-Type: application/json
X-API-Key: your_api_key

{
  "category": "news",
  "sourceType": "youtube",
  "active": true,
  "hasErrors": false,
  "search": "terme de recherche",
  "minInterval": 300,
  "maxInterval": 3600
}
```

#### Diagnostics d'erreurs
```http
GET /api/v1/diagnostics/errors
X-API-Key: your_api_key
```

### Routes existantes
- `GET /api/v1/fluxes` - Liste des flux
- `POST /api/v1/fluxes` - Créer un flux
- `PUT /api/v1/fluxes/{id}` - Modifier un flux
- `DELETE /api/v1/fluxes/{id}` - Supprimer un flux
- `POST /api/v1/preview-rss` - Prévisualiser un flux RSS
- `GET /api/v1/stats` - Statistiques générales

## 🎨 Types de sources supportés

### Web (RSS/Atom)
```
URL directe vers le flux RSS/Atom
```

### YouTube
```
https://youtube.com/channel/CHANNEL_ID
https://youtube.com/@username
https://youtube.com/c/channelname
https://youtube.com/user/username
https://youtube.com/playlist?list=PLAYLIST_ID
```

### Réseaux sociaux (via RSSHub)
```
Facebook: https://facebook.com/pagename
Instagram: https://instagram.com/username
TikTok: https://tiktok.com/@username
```

## 🚨 Résolution des problèmes

### 🐳 Problèmes Docker

#### Erreur de résolution DNS MongoDB
**Symptôme :** `failed to resolve reference "docker.io/library/mongo:latest"`
**Solutions :**
1. **Utiliser le script d'aide :**
   ```bash
   ./docker-helper.sh clean  # Nettoyer
   ./docker-helper.sh start  # Redémarrer avec diagnostics
   ```

2. **Vérifier la connectivité :**
   ```bash
   ./docker-helper.sh 8  # Test de connectivité
   ```

3. **Version MongoDB fixe :** Le `docker-compose.yaml` utilise maintenant `mongo:7.0-jammy`

4. **Configuration proxy/firewall :** Vérifier les paramètres réseau Docker

#### Services qui ne démarrent pas
1. **Vérifier les ports :**
   ```bash
   netstat -an | findstr :3000
   netstat -an | findstr :27017
   ```

2. **Logs détaillés :**
   ```bash
   docker-compose logs mongodb
   docker-compose logs app
   ```

3. **Redémarrage complet :**
   ```bash
   ./docker-helper.sh clean
   ./docker-helper.sh start
   ```

### 🔧 Problèmes application

#### Flux en erreur
1. **Vérifier la section d'erreurs** du dashboard
2. **Analyser le type d'erreur** : Discord, RSS, HTTP, Timeout
3. **Actions recommandées** :
   - Discord : Vérifier les permissions du bot
   - RSS : Tester l'URL dans un lecteur RSS
   - HTTP : Vérifier la connectivité réseau
   - Timeout : Augmenter l'intervalle

#### Bot Discord
- Inviter le bot avec les permissions : "Envoyer des messages", "Lire l'historique"
- Vérifier que le token Discord est valide
- S'assurer que le bot a accès aux salons cibles
- Utiliser `/api/v1/discord/test` pour diagnostiquer

#### Module psutil manquant
**Symptôme :** Informations système limitées
**Solution :**
```bash
pip install psutil
# Ou pour Docker : rebuild l'image
docker-compose build --no-cache
```

### 📊 Performance
- **Mode agressif** : Intervalle 10s pour tous les flux (debug uniquement)
- **Optimisation** : Utiliser des intervalles adaptés (300s+ recommandé)
- **Monitoring** : Surveiller les statistiques par catégorie
- **Ressources système** : Vérifier via `/api/v1/system/info`

## 🔧 Développement

### Structure du projet
```
momoxrss_python/
├── main.py              # API FastAPI principale (améliorée)
├── models.py            # Modèles Pydantic
├── discord_utils.py     # Utilitaires Discord
├── rss_checker.py       # Logique de vérification RSS
├── db.py               # Base de données
├── static/index.html   # Dashboard web
├── requirements.txt    # Dépendances
├── docker-compose.yaml # Configuration Docker moderne
├── docker-helper.sh    # Script d'aide Linux/Mac
├── docker-helper.ps1   # Script d'aide Windows
├── Dockerfile          # Image Docker
└── .env.example        # Configuration exemple
```

### 🆕 Améliorations récentes du code

#### Gestion robuste des dépendances (main.py:5-7)
```python
# Import conditionnel de psutil pour éviter les erreurs fatales
try:
    import psutil
except ImportError:
    psutil = None

# Fonction utilitaire avec gestion d'erreurs
def _get_system_resources() -> Dict[str, Any]:
    if psutil is None:
        return {"status": "unavailable", "message": "Module psutil non installé"}
    # ... gestion des erreurs d'accès aux ressources
```

#### Configuration Docker modernisée
- **Version MongoDB stable :** `mongo:7.0-jammy` au lieu de `latest`
- **Health checks :** Vérification automatique de l'état des services
- **Réseaux isolés :** Sécurité améliorée avec réseau dédié
- **Volumes nommés :** Meilleure gestion de la persistance
- **Variables d'environnement :** Configuration flexible via .env

### Ajout de nouvelles fonctionnalités
1. **Backend** : Ajouter routes dans `main.py`
2. **Frontend** : Modifier `static/index.html`
3. **Modèles** : Étendre `models.py` si nécessaire
4. **Tests** : Utiliser la fonction de test RSS intégrée

## 📈 Roadmap

- [x] **Gestion robuste des dépendances** (v3.6.0)
- [x] **Configuration Docker moderne** (v3.6.0)
- [x] **Scripts d'aide pour déploiement** (v3.6.0)
- [x] **Export/import de configuration** (v3.6.0)
- [ ] Support de webhooks Discord
- [ ] Notifications push
- [ ] Interface mobile optimisée
- [ ] Métriques avancées (Prometheus)
- [ ] Support multi-utilisateurs
- [ ] Clustering et haute disponibilité

## 🤝 Contribution

Les contributions sont les bienvenues ! N'hésitez pas à :
- Signaler des bugs
- Proposer des améliorations
- Contribuer au code
- Améliorer la documentation

## 📜 Licence

[Indiquer la licence utilisée]

---

**MomoXRSS v3.6.0** - Gestionnaire de flux RSS moderne avec interface web intuitive, Docker optimisé, et fonctionnalités avancées de monitoring et gestion en lot.