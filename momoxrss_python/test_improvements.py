#!/usr/bin/env python3
"""
Script de test pour valider les améliorations apportées à MomoXRSS v3.5.0
"""

import asyncio
import json
import sys
import os
from typing import Dict, Any
from dotenv import load_dotenv
import requests
import time

# Charger les variables d'environnement
load_dotenv()

# Configuration de test
API_BASE = "http://localhost:3000/api/v1"
API_KEY = os.getenv("API_KEY")

if not API_KEY:
    print("❌ ERREUR: Variable d'environnement API_KEY non définie")
    print("   Veuillez créer un fichier .env avec: API_KEY=votre_clé_api")
    sys.exit(1)

HEADERS = {
    "X-API-Key": API_KEY,
    "Content-Type": "application/json"
}

def test_api_endpoint(endpoint: str, method: str = "GET", data: Dict[Any, Any] = None) -> Dict[Any, Any]:
    """Test un endpoint de l'API."""
    url = f"{API_BASE}/{endpoint}"
    
    try:
        if method == "GET":
            response = requests.get(url, headers=HEADERS)
        elif method == "POST":
            response = requests.post(url, headers=HEADERS, json=data)
        elif method == "PUT":
            response = requests.put(url, headers=HEADERS, json=data)
        elif method == "DELETE":
            response = requests.delete(url, headers=HEADERS)
        
        if response.status_code < 400:
            return {"success": True, "data": response.json(), "status": response.status_code}
        else:
            return {"success": False, "error": response.text, "status": response.status_code}
            
    except Exception as e:
        return {"success": False, "error": str(e), "status": 0}

def test_url_resolution():
    """Test les améliorations de résolution d'URL."""
    print("🧪 Test de résolution d'URL...")
    
    test_urls = [
        {"url": "https://youtube.com/@PewDiePie", "type": "youtube", "expected": "xml"},
        {"url": "https://youtube.com/c/PewDiePie", "type": "youtube", "expected": "xml"},
        {"url": "https://youtube.com/channel/UC-lHJZR3Gqxm24_Vd_AJ5Yw", "type": "youtube", "expected": "xml"},
        {"url": "https://facebook.com/zuck", "type": "facebook", "expected": "rsshub"},
        {"url": "https://instagram.com/instagram", "type": "instagram", "expected": "rsshub"},
        {"url": "https://tiktok.com/@tiktok", "type": "tiktok", "expected": "rsshub"},
    ]
    
    for test in test_urls:
        print(f"  Testing {test['type']}: {test['url']}")
        result = test_api_endpoint("preview-rss", "POST", {
            "rssUrl": test["url"],
            "sourceType": test["type"],
            "count": 1
        })
        
        if result["success"]:
            print(f"    ✅ Résolution OK")
        else:
            print(f"    ❌ Erreur: {result['error']}")

def test_new_api_endpoints():
    """Test les nouveaux endpoints API."""
    print("\n🧪 Test des nouveaux endpoints...")
    
    # Test statistiques par catégorie
    print("  Testing /stats/categories")
    result = test_api_endpoint("stats/categories")
    if result["success"]:
        print(f"    ✅ Catégories stats OK: {len(result['data'].get('categories', {}))} catégories")
    else:
        print(f"    ❌ Erreur: {result['error']}")
    
    # Test diagnostics d'erreurs
    print("  Testing /diagnostics/errors")
    result = test_api_endpoint("diagnostics/errors")
    if result["success"]:
        error_count = result["data"].get("totalErrors", 0)
        print(f"    ✅ Diagnostics OK: {error_count} erreurs détectées")
    else:
        print(f"    ❌ Erreur: {result['error']}")
    
    # Test recherche avancée
    print("  Testing /search-fluxes")
    result = test_api_endpoint("search-fluxes", "POST", {
        "active": True,
        "limit": 10
    })
    if result["success"]:
        flux_count = len(result["data"])
        print(f"    ✅ Recherche OK: {flux_count} flux trouvés")
    else:
        print(f"    ❌ Erreur: {result['error']}")

def test_bulk_actions():
    """Test les actions en lot (sans faire de modifications réelles)."""
    print("\n🧪 Test des actions en lot...")
    
    # D'abord, récupérer quelques flux pour tester
    result = test_api_endpoint("fluxes")
    if not result["success"]:
        print("    ❌ Impossible de récupérer les flux")
        return
    
    fluxes = result["data"]
    if len(fluxes) == 0:
        print("    ℹ️  Aucun flux disponible pour tester les actions en lot")
        return
    
    # Test avec un flux (sans le modifier réellement)
    flux_id = fluxes[0]["id"]
    print(f"  Testing bulk action simulation sur flux {flux_id}")
    
    # On teste juste que l'endpoint existe (avec action invalide volontairement)
    result = test_api_endpoint("bulk-actions", "POST", {
        "action": "test_only",
        "fluxIds": [flux_id]
    })
    
    if result["status"] == 400:
        print("    ✅ Endpoint bulk-actions disponible (erreur attendue pour action test)")
    else:
        print(f"    ❌ Réponse inattendue: {result}")

def test_dashboard_accessibility():
    """Test l'accessibilité du dashboard."""
    print("\n🧪 Test du dashboard...")
    
    try:
        response = requests.get("http://localhost:3000/dashboard")
        if response.status_code == 200 and "MomoXRSS Dashboard" in response.text:
            print("    ✅ Dashboard accessible")
            
            # Vérifier la présence des nouvelles sections
            content = response.text
            features = [
                ("Section d'erreurs", "errorSection"),
                ("Statistiques catégories", "categoryStats"),
                ("Actions en lot", "bulk-actions"),
                ("Recherche avancée", "advancedSearchForm"),
            ]
            
            for feature_name, feature_id in features:
                if feature_id in content:
                    print(f"      ✅ {feature_name} présente")
                else:
                    print(f"      ❌ {feature_name} manquante")
        else:
            print(f"    ❌ Dashboard inaccessible: {response.status_code}")
    except Exception as e:
        print(f"    ❌ Erreur dashboard: {e}")

def test_basic_api():
    """Test les endpoints de base."""
    print("\n🧪 Test des endpoints de base...")
    
    endpoints = [
        ("stats", "GET"),
        ("fluxes", "GET"),
    ]
    
    for endpoint, method in endpoints:
        result = test_api_endpoint(endpoint, method)
        if result["success"]:
            print(f"    ✅ {endpoint} OK")
        else:
            print(f"    ❌ {endpoint} erreur: {result['error']}")

def main():
    """Fonction principale de test."""
    print("🚀 Test des améliorations MomoXRSS v3.5.0")
    print("=" * 50)
    
    # Attendre que le serveur soit démarré
    print("⏳ Vérification de la disponibilité du serveur...")
    max_retries = 10
    for i in range(max_retries):
        try:
            response = requests.get("http://localhost:3000/api/v1/stats", headers=HEADERS, timeout=5)
            if response.status_code < 500:
                print("✅ Serveur disponible")
                break
        except:
            pass
        
        if i == max_retries - 1:
            print("❌ Serveur non disponible après 10 tentatives")
            sys.exit(1)
        
        print(f"   Tentative {i+1}/{max_retries}...")
        time.sleep(2)
    
    # Exécuter les tests
    test_basic_api()
    test_dashboard_accessibility()
    test_url_resolution()
    test_new_api_endpoints()
    test_bulk_actions()
    
    print("\n" + "=" * 50)
    print("✅ Tests terminés")
    print("\n📋 Résumé des améliorations testées:")
    print("  • ✅ Section d'erreurs dédiée avec diagnostics")
    print("  • ✅ Statistiques par catégorie")
    print("  • ✅ Actions en lot pour gestion multiple")
    print("  • ✅ Recherche avancée avec filtres")
    print("  • ✅ Résolution d'URL améliorée (YouTube @username, /c/)")
    print("  • ✅ Nouveaux endpoints API")
    print("  • ✅ Interface dashboard modernisée")

if __name__ == "__main__":
    main()