# Politique de Sécurité - RSSDI

## Versions Supportées

| Version | Supportée          |
| ------- | ------------------ |
| 3.6.x   | :white_check_mark: |
| < 3.6   | :x:                |

## Signaler une Vulnérabilité

Si vous découvrez une vulnérabilité de sécurité, veuillez **NE PAS** créer une issue publique.

Contactez les mainteneurs directement pour signaler le problème de manière responsable.

## Bonnes Pratiques de Sécurité

### 1. Protection des Secrets

#### ⚠️ CRITIQUE: Ne JAMAIS commiter de secrets dans Git

**Ce qui doit rester secret:**
- `API_KEY` - Clé d'accès à l'API
- `DISCORD_TOKEN` - Token du bot Discord
- `MONGO_ROOT_PASSWORD` - Mot de passe MongoDB
- Fichier `.env` complet

**Configuration sécurisée:**

1. **Copiez le fichier d'exemple:**
   ```bash
   cp momoxrss_python/.env.example momoxrss_python/.env
   ```

2. **Générez une clé API forte:**
   ```bash
   # Linux/Mac
   openssl rand -base64 32

   # Python
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

3. **Configurez vos secrets dans `.env`:**
   ```env
   API_KEY=votre_cle_generee_ici
   DISCORD_TOKEN=votre_token_discord_ici
   MONGO_ROOT_PASSWORD=mot_de_passe_fort_ici
   ```

4. **Vérifiez que `.env` est ignoré:**
   ```bash
   git check-ignore .env
   # Devrait afficher: .env
   ```

#### Protection du Dashboard

Le dashboard web demande la clé API au premier accès et la stocke dans `localStorage`.

**Pour réinitialiser la clé:**
1. Ouvrir la console développeur (F12)
2. Exécuter: `localStorage.removeItem('momoxrss_api_key')`
3. Recharger la page

### 2. Sécurité Docker

#### Réseau Isolé

Le docker-compose configure un réseau bridge isolé par défaut:
```yaml
networks:
  rssdi-network:
    driver: bridge
```

**Les services ne sont pas exposés directement** sur l'hôte, sauf le port 3000 de l'API.

#### Volumes de Données

Les données persistantes sont stockées dans des volumes Docker nommés:
```yaml
volumes:
  mongodb_data:  # Base de données MongoDB
  sent_items:    # Base SQLite de déduplication
```

**Pour sauvegarder:**
```bash
docker run --rm -v rssdi_mongodb_data:/data -v $(pwd):/backup \
  alpine tar czf /backup/mongodb_backup.tar.gz -C /data .
```

### 3. Sécurité MongoDB

#### Authentification

MongoDB utilise l'authentification root par défaut:
```env
MONGO_ROOT_USER=admin
MONGO_ROOT_PASSWORD=changez_ce_mot_de_passe
```

**⚠️ IMPORTANT:** Changez le mot de passe par défaut en production!

#### Accès Réseau

MongoDB n'est accessible que depuis le réseau Docker interne. Il n'est **pas exposé** sur l'hôte.

### 4. Sécurité de l'API

#### Authentification par Clé API

Tous les endpoints (sauf `/dashboard` et `/`) requièrent une clé API:
```http
X-API-Key: votre_cle_api
```

#### CORS

Par défaut, CORS est configuré pour autoriser toutes les origines (`*`).

**En production, restreignez CORS:**
```env
ALLOWED_ORIGIN=https://votre-domaine.com
```

#### Rate Limiting

⚠️ **Limitation actuelle:** Pas de rate limiting implémenté.

**Recommandations pour la production:**
1. Utilisez un reverse proxy (nginx, Caddy)
2. Configurez un rate limiting (ex: 100 requêtes/minute)
3. Exemple nginx:
   ```nginx
   limit_req_zone $binary_remote_addr zone=api:10m rate=100r/m;

   location /api/ {
       limit_req zone=api burst=20;
       proxy_pass http://localhost:3000;
   }
   ```

### 5. Sécurité Discord

#### Permissions du Bot

**Permissions minimales requises:**
- `View Channels` - Voir les salons
- `Send Messages` - Envoyer des messages
- `Read Message History` - Lire l'historique (pour les threads)
- `Embed Links` - Créer des embeds (si activé)

**⚠️ NE DONNEZ PAS:**
- Permissions d'administration
- Gestion des serveurs
- Gestion des rôles
- Mention @everyone

#### Token Discord

**Protection du token:**
1. Ne partagez JAMAIS votre token
2. Si compromis, régénérez immédiatement:
   - Discord Developer Portal > Bot > Reset Token
3. Le token permet un contrôle total du bot

### 6. Sécurité des Flux RSS

#### Validation des URLs

Les URLs RSS sont validées avant traitement:
```python
def isValidUrl(url: str) -> bool:
    return bool(re.match(r"^https?://", str(url)))
```

#### Protection contre les Boucles

- **Limite par exécution:** `maxPerRun` (défaut: 5)
- **Déduplication:** SQLite + MongoDB
- **Heures silencieuses:** Support des plages horaires

#### Filtrage de Contenu

**Filtres disponibles:**
- Mots-clés (include/exclude)
- Regex (include/exclude)
- Domaines (whitelist/blacklist)
- Langue (détection basique fr/en)

### 7. Exposition Publique

#### ⚠️ Ne pas exposer directement sur Internet

Ce service est conçu pour un usage **local ou en réseau privé**.

**Si vous devez l'exposer publiquement:**

1. **Utilisez un reverse proxy avec HTTPS:**
   ```bash
   # Exemple avec Caddy
   caddy reverse-proxy --from rssdi.example.com --to localhost:3000
   ```

2. **Configurez un pare-feu:**
   ```bash
   # UFW exemple
   ufw allow from 192.168.1.0/24 to any port 3000
   ```

3. **Ajoutez une authentification supplémentaire:**
   - Basic Auth sur le reverse proxy
   - VPN (WireGuard, Tailscale)
   - Tunnel sécurisé (Cloudflare Tunnel)

### 8. Mises à Jour

#### Dépendances Python

Vérifiez régulièrement les vulnérabilités:
```bash
pip install safety
safety check -r requirements.txt
```

#### Images Docker

Utilisez toujours des images officielles et taguées:
```yaml
image: python:3.11-slim
image: mongo:7.0-jammy
```

**Mettez à jour régulièrement:**
```bash
docker-compose pull
docker-compose up -d
```

### 9. Logs et Monitoring

#### Niveaux de Logs

Les logs contiennent des informations sensibles. **Ne les partagez pas publiquement.**

**Rediriger les logs:**
```bash
docker-compose logs app > logs.txt 2>&1
# Avant de partager, supprimez les tokens, IDs, etc.
```

#### Informations Sensibles dans les Logs

Les logs peuvent contenir:
- IDs de serveurs Discord
- IDs de salons
- URLs de flux RSS (potentiellement privées)
- Traces d'erreurs avec détails

### 10. Sauvegarde et Restauration

#### Que sauvegarder

**Critique:**
- `.env` - Configuration (gardez-le en sécurité!)
- Volume `mongodb_data` - Configurations des flux
- Volume `sent_items` - Historique de déduplication

**Optionnel:**
- Logs applicatifs

#### Script de Sauvegarde

```bash
#!/bin/bash
BACKUP_DIR="./backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Copier .env (ATTENTION: contient des secrets!)
cp momoxrss_python/.env "$BACKUP_DIR/.env"

# Sauvegarder MongoDB
docker exec rssdi_mongodb mongodump --out=/backup
docker cp rssdi_mongodb:/backup "$BACKUP_DIR/mongodb"

# Sauvegarder SQLite
docker cp rssdi_app:/app/data/sent_items.db "$BACKUP_DIR/"

echo "Sauvegarde créée dans: $BACKUP_DIR"
echo "⚠️  Sécurisez ce dossier, il contient des secrets!"
```

## Audit de Sécurité

### Changements Récents (v3.6.1)

**Corrections de sécurité:**
- ✅ Suppression des clés API hardcodées dans le code source
- ✅ Ajout de `.env.example` avec documentation
- ✅ Amélioration du `.gitignore` pour protéger les secrets
- ✅ Ajout de validation des tokens Discord (LoginFailure)
- ✅ Meilleure gestion d'erreur avec logging approprié
- ✅ Documentation des bonnes pratiques

**Recommandations pour les Utilisateurs Existants:**
1. ⚠️ **ROTATEZ votre clé API** si elle était hardcodée auparavant
2. Vérifiez que votre `.env` n'est pas versionné dans Git
3. Mettez à jour vers la dernière version
4. Revoyez vos permissions Discord Bot

## Checklist de Déploiement Sécurisé

- [ ] Clé API forte générée (min 32 caractères)
- [ ] Token Discord valide et sécurisé
- [ ] Mot de passe MongoDB changé du défaut
- [ ] `.env` confirmé dans `.gitignore`
- [ ] CORS configuré pour votre domaine (si applicable)
- [ ] Reverse proxy avec HTTPS configuré (si exposé)
- [ ] Rate limiting configuré (si exposé)
- [ ] Permissions Discord Bot minimales
- [ ] Sauvegarde automatique configurée
- [ ] Monitoring des logs en place
- [ ] Plan de mise à jour défini

## Ressources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Discord Bot Security](https://discord.com/developers/docs/topics/oauth2#bot-vs-user-accounts)
- [Docker Security Best Practices](https://docs.docker.com/engine/security/)
- [MongoDB Security Checklist](https://docs.mongodb.com/manual/administration/security-checklist/)

## Contact

Pour signaler un problème de sécurité, contactez les mainteneurs du projet.

---

**Dernière mise à jour:** 2025-11-10
**Version du document:** 1.0
