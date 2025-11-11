# 📖 MomoXRSS – Bot RSS vers Discord

MomoXRSS est une application qui permet de **surveiller des flux RSS** et d’**envoyer automatiquement les nouveaux articles** dans des salons Discord (mode direct ou thread).  
Elle inclut un **bot Discord** et une **interface web** pour gérer facilement les flux.

---

## 1️⃣ Exécuter l’application

Personnellement j'exécute l'application sur un contenaiers docker avec un debian installer dessus mais sa devrais fonctionner sur Windows mais les commandes ne seront pas forcement les même.

### ⚙️ Pré-requis

- **Docker** et **Docker Compose** installés
- Un fichier `.env` configuré avec :
  - `DISCORD_BOT_TOKEN` → ton token de bot Discord
  - `API_KEY` → ta clé API secrète
  - `MONGO_URL` → URL MongoDB (par défaut `mongodb://mongodb:27017/momoxrss`)

### 🚀 Lancer
```bash
docker compose up --build -d

Cela démarre :

MongoDB (base de données)

L’API FastAPI (backend + bot Discord intégré)

Le dashboard web (interface de gestion)


📊 Schéma d’architecture
Code
+-------------------+       +-------------------+       +-------------------+
|   Flux RSS        | --->  |   Application     | --->  |   Discord         |
| (sites, YouTube…) |       | (FastAPI + Bot)   |       | (salons / threads)|
+-------------------+       +-------------------+       +-------------------+
                                |
                                v
                          +-------------+
                          |   MongoDB   |
                          +-------------+
-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


2️⃣ Exécuter le bot Discord 

Le bot est inclus dans l’application : tu n’as rien à lancer en plus. Dès que tu démarres l’application avec Docker, le bot se connecte automatiquement à Discord grâce à ton DISCORD_BOT_TOKEN.

Vérification
Dans les logs (docker compose logs -f app), tu dois voir :

Code
Bot connecté à Discord
Scheduler: X flux, Y actifs...
Dans Discord, ton bot apparaît en ligne ✅

Personnellement j ai un bot en arrière plan qui tourne sur docker coder en python. j'ai pas encore tester sans le bot de lancer simultanément.
-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------


3️⃣ Utiliser l’interface web

🌐 Accès

- Ouvre ton navigateur sur : 👉 http://localhost:3000/dashboard

🖥️ Fonctionnalités principales

Ajouter un flux : URL RSS, catégorie, mode (direct/thread), intervalle, filtres, etc.

Tester une source : prévisualiser les articles avant ajout.

Envoi manuel : envoyer un article ou un lot d’articles immédiatement.

Envoi par catégorie : envoyer tous les flux d’une catégorie.

Planification par catégorie : définir un intervalle global pour une catégorie.

Mode agressif : forcer tous les flux à être vérifiés toutes les 10 secondes.

Déduplication : éviter les doublons (fenêtre de 24h par défaut).

📊 Schéma interface
Code
+---------------------------------------------------+
|                 Dashboard Web                     |
+---------------------------------------------------+
| [Ajouter un flux] [Tester une source]             |
|                                                   |
| Flux par salon :                                  |
|  - Nom du flux | Catégorie | Mode | Intervalle    |
|  - Dernier article envoyé                         |
|  - Boutons : Envoyer / Activer / Supprimer        |
|                                                   |
| [Envoi par catégorie] [Planifier catégorie]       |
+---------------------------------------------------+

-----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
4️⃣ Réglages recommandés pour “articles du jour seulement”

- Pour que le bot envoie uniquement les nouveaux articles du jour et jamais deux fois le même :

Intervalle (s, min 60) → 3600 (1h)

Fenêtre de déduplication (heures) → 24

Max par exécution → 50

Actif → Oui

👉 Résultat : toutes les heures, le bot envoie uniquement les articles publiés dans les dernières 24h, sans jamais republier ceux déjà envoyés.

🔑 Commandes utiles
Démarrer :

bash
docker compose up -d
Arrêter :

bash
docker compose down
Voir les logs :

bash
docker compose logs -f app
✅ Résumé

- Exécuter l’application : docker compose up -d

Le bot Discord tourne automatiquement avec l’app

- Interface web : http://localhost:3000/dashboard

Réglages conseillés : Intervalle = 3600, Déduplication = 24h, Max = 50

# MomoXRSS – Bot RSS vers Discord

MomoXRSS surveille des flux RSS et envoie automatiquement les nouveaux articles vers des salons Discord (mode direct ou thread). Il inclut une API FastAPI, un scheduler, un bot Discord et un dashboard web.

---

## Installation et exécution

Prérequis:
- Docker et Docker Compose
- Un fichier `.env` rempli (API_KEY, DISCORD_BOT_TOKEN, MONGO_URL, etc.)

Démarrage:
- docker compose up --build -d

Services:
- MongoDB
- API FastAPI + bot Discord connecté avec DISCORD_BOT_TOKEN
- Dashboard web

Accès:
- http://localhost:3000/dashboard

---

## Fonctionnalités principales

- Ajout, édition, suppression de flux
- Test de source et prévisualisation RSS
- Envoi manuel (single / batch)
- Envoi par catégorie
- Planification par catégorie
- Mode agressif (vérification toutes les 10s)
- Déduplication par lien/date (fenêtre configurable)

---

## Conseils de configuration

Pour envoyer uniquement les nouveautés du jour sans doublons:
- Intervalle: 3600 (1h)
- Fenêtre de déduplication: 24h
- Max par exécution: 50
- Actif: Oui

---

## Développement local

- uvicorn main:app --reload
- Modifier ALLOWED_ORIGIN dans `.env` si nécessaire
- Le dashboard consomme l’API via X-API-Key (API_KEY dans `.env`)
