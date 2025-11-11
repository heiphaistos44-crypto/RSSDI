#!/usr/bin/env python3
"""
Script de test pour diagnostiquer les problèmes Discord dans RSSDI
"""

import asyncio
import os
import sys
from dotenv import load_dotenv
from discord_utils import initialize_discord_client, test_discord_connection, get_guild_channels, get_channel

# Charger les variables d'environnement
load_dotenv()

async def test_discord_setup():
    """Test complet de la configuration Discord."""
    print("🔍 Test de configuration Discord RSSDI")
    print("=" * 50)
    
    # 1. Vérifier le token
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        print("❌ DISCORD_TOKEN non configuré dans .env")
        print("💡 Ajoutez: DISCORD_TOKEN=votre_token_ici")
        return False
    else:
        print(f"✅ Token Discord configuré ({token[:10]}...)")
    
    # 2. Initialiser le client
    print("\n🔧 Initialisation du client Discord...")
    try:
        client = await initialize_discord_client()
        if client:
            print("✅ Client Discord initialisé")
        else:
            print("❌ Échec initialisation client Discord")
            return False
    except Exception as e:
        print(f"❌ Erreur initialisation: {e}")
        return False
    
    # 3. Test de connexion
    print("\n🌐 Test de connexion...")
    try:
        connection_test = await test_discord_connection()
        if connection_test["status"] == "success":
            print(f"✅ {connection_test['message']}")
            print(f"📝 Détails: {connection_test['details']}")
        elif connection_test["status"] == "warning":
            print(f"⚠️  {connection_test['message']}")
            print(f"📝 Détails: {connection_test['details']}")
        else:
            print(f"❌ {connection_test['message']}")
            print(f"📝 Détails: {connection_test['details']}")
            return False
    except Exception as e:
        print(f"❌ Erreur test connexion: {e}")
        return False
    
    # 4. Test interactif de récupération de salons
    print("\n🎯 Test interactif de récupération de salons")
    while True:
        guild_id = input("\nEntrez un ID de serveur (ou 'quit' pour quitter): ").strip()
        if guild_id.lower() == 'quit':
            break
        
        if not guild_id.isdigit():
            print("❌ L'ID doit être un nombre")
            continue
        
        print(f"🔍 Récupération des salons pour le serveur {guild_id}...")
        try:
            channels = await get_guild_channels(None, guild_id)
            if channels:
                print(f"✅ Trouvé {len(channels)} salons:")
                for channel in channels:
                    print(f"  • #{channel['name']} (ID: {channel['id']}, Type: {channel['typeLabel']})")
            else:
                print("❌ Aucun salon trouvé")
                print("💡 Vérifiez que:")
                print("   - L'ID du serveur est correct")
                print("   - Le bot est invité sur ce serveur")
                print("   - Le bot a les permissions 'Voir les salons'")
        except Exception as e:
            print(f"❌ Erreur récupération salons: {e}")
    
    # 5. Test de récupération de salon individuel
    print("\n🎯 Test de récupération de salon individuel")
    while True:
        channel_id = input("\nEntrez un ID de salon (ou 'quit' pour quitter): ").strip()
        if channel_id.lower() == 'quit':
            break
        
        if not channel_id.isdigit():
            print("❌ L'ID doit être un nombre")
            continue
        
        print(f"🔍 Récupération du salon {channel_id}...")
        try:
            channel = await get_channel(None, channel_id)
            if channel:
                print(f"✅ Salon trouvé: #{channel['name']} (Type: {channel['typeLabel']})")
            else:
                print("❌ Salon non trouvé")
                print("💡 Vérifiez que:")
                print("   - L'ID du salon est correct")
                print("   - Le bot a accès à ce salon")
        except Exception as e:
            print(f"❌ Erreur récupération salon: {e}")
    
    print("\n✅ Tests Discord terminés")
    return True

def print_discord_setup_guide():
    """Affiche un guide de configuration Discord."""
    print("\n📘 Guide de configuration Discord")
    print("=" * 40)
    print("1. Créer une application Discord:")
    print("   • Aller sur https://discord.com/developers/applications")
    print("   • Créer une nouvelle application")
    print("   • Aller dans l'onglet 'Bot'")
    print("   • Copier le token")
    print("")
    print("2. Configurer le token:")
    print("   • Ajouter DISCORD_TOKEN=votre_token dans .env")
    print("")
    print("3. Inviter le bot:")
    print("   • Aller dans l'onglet 'OAuth2' > 'URL Generator'")
    print("   • Cocher 'bot' dans Scopes")
    print("   • Cocher ces permissions dans Bot Permissions:")
    print("     - View Channels")
    print("     - Send Messages")
    print("     - Read Message History")
    print("     - Embed Links")
    print("   • Utiliser l'URL générée pour inviter le bot")
    print("")
    print("4. Récupérer les IDs:")
    print("   • Activer le mode développeur dans Discord")
    print("   • Clic droit sur serveur/salon → 'Copier l'ID'")

async def main():
    """Fonction principale."""
    if len(sys.argv) > 1 and sys.argv[1] == "--guide":
        print_discord_setup_guide()
        return
    
    success = await test_discord_setup()
    
    if not success:
        print("\n💡 Pour voir le guide de configuration:")
        print("python test_discord.py --guide")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Test interrompu par l'utilisateur")
    except Exception as e:
        print(f"\n❌ Erreur inattendue: {e}")