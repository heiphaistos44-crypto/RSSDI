# RSSDI v4.0 - Guide de Démarrage Rapide

## ✅ Problèmes Résolus

### 1. Dépendances Installées
Toutes les dépendances Python ont été installées avec succès, y compris:
- ✅ FastAPI & Uvicorn
- ✅ MongoDB (pymongo & motor)
- ✅ Discord.py
- ✅ Pydantic & pydantic-settings
- ✅ feedparser (avec sgmllib3k)
- ✅ Toutes les autres dépendances

### 2. Configuration Pydantic Corrigée
Le fichier `app/core/config.py` a été mis à jour pour Pydantic V2:
- Changé `class Config` en `model_config`
- Compatible avec pydantic-settings 2.5.2

### 3. sgmllib3k Installé
Un problème de compilation de sgmllib3k a été résolu en:
- Téléchargeant le fichier source directement
- L'installant manuellement dans site-packages
- feedparser fonctionne maintenant correctement

## 🚀 Démarrage de l'Application

### Option 1: Directement avec Python

```bash
cd /home/user/RSSDI/momoxrss_python

# Démarrer l'application
python3 main.py
```

L'application démarre sur `http://localhost:3000`

### Option 2: Avec Docker (Recommandé)

```bash
cd /home/user/RSSDI/momoxrss_python

# Démarrer avec Docker Compose
docker-compose up -d

# Voir les logs
docker-compose logs -f app
```

## 📝 Configuration Requise

Assurez-vous que votre fichier `.env` existe et contient:

```env
# API
API_KEY=yEVTF7f7FM-HsIuH6OsYzbIe-Ufu-dtCVVFVfW6kRuw

# MongoDB
MONGO_URL=mongodb://mongodb:27017/momoxrss
MONGO_DB=momoxrss
MONGO_ROOT_USER=admin
MONGO_ROOT_PASSWORD=CbZZsnGvjszZDd4D8dmBRuQJgYDYhZcWD6nfShbeJpo

# Discord
DISCORD_TOKEN=votre_token_discord_ici

# RSSHub
RSSHUB_BASE=https://rsshub.app
```

**⚠️ IMPORTANT:** Remplacez `votre_token_discord_ici` par votre vrai token Discord!

## 🧪 Test de l'Application

### 1. Vérifier que l'app démarre

```bash
# Si lancé directement
python3 main.py

# Si lancé avec Docker
docker-compose logs app | head -20
```

Vous devriez voir:
```
✅ MongoDB connecté: momoxrss
✅ Base SQLite initialisée
✅ Client Discord initialisé (mode REST-only)
✅ Scheduler initialisé
✅ Scheduler démarré
✅ Application démarrée avec succès!
INFO:     Uvicorn running on http://0.0.0.0:3000
```

### 2. Tester les Endpoints

```bash
# Health check
curl http://localhost:3000/health

# Documentation API
curl http://localhost:3000/api/docs
# Ou ouvrez dans navigateur: http://localhost:3000/api/docs

# Dashboard
# Ouvrez dans navigateur: http://localhost:3000/dashboard
```

### 3. Tester avec le Dashboard

1. Ouvrez `http://localhost:3000/dashboard`
2. Entrez votre clé API quand demandé: `yEVTF7f7FM-HsIuH6OsYzbIe-Ufu-dtCVVFVfW6kRuw`
3. Le dashboard devrait charger les statistiques

## ⚠️ Résolution de Problèmes

### Erreur: "Unexpected token 'I', "Internal S"... is not valid JSON"

Cette erreur signifie que l'API retourne une erreur 500 au lieu de JSON. Causes possibles:

1. **MongoDB pas démarré**
   ```bash
   docker-compose up mongodb -d
   # Attendre 5 secondes
   docker-compose up app -d
   ```

2. **Token Discord invalide**
   - Vérifiez votre `DISCORD_TOKEN` dans `.env`
   - Vérifiez que le token est valide sur Discord Developer Portal

3. **Variables d'environnement manquantes**
   ```bash
   # Vérifier que .env existe
   ls -la .env

   # Vérifier le contenu
   cat .env | grep -E "API_KEY|DISCORD_TOKEN"
   ```

### Erreur: "Module not found"

Si vous voyez des erreurs d'import:

```bash
# Réinstaller les dépendances
pip3 install --user -r requirements.txt
```

### Erreur: MongoDB

Si MongoDB ne se connecte pas:

```bash
# Avec Docker
docker-compose down
docker-compose up -d mongodb
sleep 5
docker-compose up -d app

# Sans Docker - installer MongoDB localement
# Ou changer MONGO_URL vers une instance MongoDB externe
```

## 📊 Vérification Complète

Utilisez ce script pour vérifier que tout fonctionne:

```bash
#!/bin/bash
cd /home/user/RSSDI/momoxrss_python

echo "🔍 Vérification RSSDI v4.0"
echo "=========================="

# 1. Vérifier .env
if [ -f ".env" ]; then
    echo "✅ .env existe"
else
    echo "❌ .env manquant - copiez .env.example"
    exit 1
fi

# 2. Tester les imports Python
python3 -c "
from app.routers.fluxes import router
from app.services.rss_service import rss_service
from app.core.config import get_settings
print('✅ Imports Python OK')
" || { echo "❌ Erreur imports Python"; exit 1; }

# 3. Vérifier MongoDB (si Docker)
docker-compose ps mongodb 2>/dev/null && echo "✅ MongoDB Docker OK" || echo "⚠️  MongoDB pas en Docker"

# 4. Démarrer l'app
echo "🚀 Lancement de l'application..."
timeout 3 python3 main.py 2>&1 | head -10 &

sleep 2

# 5. Tester l'endpoint health
curl -s http://localhost:3000/health > /dev/null && echo "✅ API répond" || echo "❌ API ne répond pas"

echo "=========================="
echo "✅ Vérification terminée!"
```

## 📚 Documentation Complète

- **Architecture:** Voir `/home/user/RSSDI/REFACTORING_v4.md`
- **Sécurité:** Voir `/home/user/RSSDI/SECURITY.md`
- **API Docs:** http://localhost:3000/api/docs (quand l'app tourne)

## 🎯 Résumé

L'application RSSDI v4.0 est maintenant:
- ✅ Entièrement refactorisée
- ✅ Dépendances installées
- ✅ Configuration corrigée
- ✅ Prête à démarrer

**Prochaine étape:** Lancez l'application et testez l'ajout d'un flux!

```bash
# Démarrage simple
cd /home/user/RSSDI/momoxrss_python
python3 main.py
```

Puis ouvrez: http://localhost:3000/dashboard
