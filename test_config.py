#!/usr/bin/env python3
"""
Script de test pour vérifier toutes les configurations API
"""

import os
from dotenv import load_dotenv
from apify_client import ApifyClient
import gspread
from google.oauth2.service_account import Credentials
import requests

# Charger les variables d'environnement
load_dotenv()

def test_apify():
    """Test de la connexion Apify"""
    print("\n" + "="*60)
    print("🧪 TEST APIFY")
    print("="*60)
    
    try:
        token = os.getenv('APIFY_API_TOKEN')
        if not token:
            print("❌ APIFY_API_TOKEN non trouvé dans .env")
            return False
        
        print(f"✓ Token trouvé: {token[:20]}...")
        
        # Initialiser le client
        client = ApifyClient(token)
        
        # Tester avec un appel simple
        print("🔄 Test de connexion à l'API Apify...")
        user = client.user().get()
        
        print(f"✅ APIFY CONNECTÉ")
        print(f"   - Utilisateur: {user.get('username', 'N/A')}")
        print(f"   - Email: {user.get('email', 'N/A')}")
        return True
        
    except Exception as e:
        print(f"❌ ERREUR APIFY: {e}")
        return False

def test_google_sheets():
    """Test de la connexion Google Sheets"""
    print("\n" + "="*60)
    print("🧪 TEST GOOGLE SHEETS")
    print("="*60)
    
    try:
        sheet_id = os.getenv('GOOGLE_SHEET_ID')
        if not sheet_id:
            print("❌ GOOGLE_SHEET_ID non trouvé dans .env")
            return False
        
        print(f"✓ Sheet ID trouvé: {sheet_id}")
        
        # Vérifier le fichier credentials.json
        if not os.path.exists('credentials.json'):
            print("❌ Fichier credentials.json non trouvé")
            return False
        
        print("✓ Fichier credentials.json trouvé")
        
        # Définir les scopes
        scopes = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]
        
        # Charger les credentials
        print("🔄 Chargement des credentials...")
        creds = Credentials.from_service_account_file(
            'credentials.json',
            scopes=scopes
        )
        
        print("✓ Credentials chargés")
        print(f"   - Service Account: {creds.service_account_email}")
        
        # Autoriser gspread
        print("🔄 Connexion à Google Sheets...")
        gc = gspread.authorize(creds)
        
        # Ouvrir le Google Sheet
        print("🔄 Ouverture du Google Sheet...")
        sheet = gc.open_by_key(sheet_id)
        
        print(f"✅ GOOGLE SHEETS CONNECTÉ")
        print(f"   - Nom du Sheet: {sheet.title}")
        print(f"   - URL: https://docs.google.com/spreadsheets/d/{sheet_id}")
        
        # Vérifier les permissions
        print("\n📋 Vérification des permissions...")
        print(f"   ⚠️  IMPORTANT: Assurez-vous d'avoir partagé le Google Sheet avec:")
        print(f"   📧 {creds.service_account_email}")
        print(f"   🔑 Avec les droits 'Éditeur'")
        
        # Essayer d'accéder à la première feuille
        try:
            worksheet = sheet.get_worksheet(0)
            print(f"\n✓ Accès à la feuille: {worksheet.title}")
            print(f"   - Lignes: {worksheet.row_count}")
            print(f"   - Colonnes: {worksheet.col_count}")
        except Exception as e:
            print(f"\n⚠️  Impossible d'accéder à la feuille: {e}")
            print("   Vérifiez que le service account a bien les permissions")
        
        return True
        
    except Exception as e:
        print(f"❌ ERREUR GOOGLE SHEETS: {e}")
        return False

def test_gohighlevel():
    """Test de la connexion GoHighLevel"""
    print("\n" + "="*60)
    print("🧪 TEST GOHIGHLEVEL")
    print("="*60)
    
    try:
        api_key = os.getenv('GOHIGHLEVEL_API_KEY')
        location_id = os.getenv('GOHIGHLEVEL_LOCATION_ID')
        
        if not api_key:
            print("❌ GOHIGHLEVEL_API_KEY non trouvé dans .env")
            return False
        
        if not location_id:
            print("❌ GOHIGHLEVEL_LOCATION_ID non trouvé dans .env")
            return False
        
        print(f"✓ API Key trouvé: {api_key[:20]}...")
        print(f"✓ Location ID: {location_id}")
        
        # Tester la connexion
        print("🔄 Test de connexion à l'API GoHighLevel...")
        
        # Note: GoHighLevel nécessite une vraie API key pour tester
        # On vérifie juste que les variables sont présentes
        if api_key == "your_gohighlevel_api_key_here":
            print("⚠️  API Key par défaut détectée")
            print("   Vous devez remplacer 'your_gohighlevel_api_key_here' par votre vraie clé")
            return False
        
        print("✅ GOHIGHLEVEL CONFIGURÉ")
        print("   ⚠️  Note: Test de connexion réel nécessite une vraie API key")
        return True
        
    except Exception as e:
        print(f"❌ ERREUR GOHIGHLEVEL: {e}")
        return False

def test_hunter():
    """Test de la connexion Hunter.io (optionnel)"""
    print("\n" + "="*60)
    print("🧪 TEST HUNTER.IO (Optionnel)")
    print("="*60)
    
    try:
        api_key = os.getenv('HUNTER_API_KEY')
        
        if not api_key or api_key == "":
            print("⚠️  HUNTER_API_KEY non configuré (optionnel)")
            print("   Le scraper utilisera des patterns d'emails génériques")
            return True
        
        print(f"✓ API Key trouvé: {api_key[:20]}...")
        
        # Tester la connexion
        print("🔄 Test de connexion à l'API Hunter.io...")
        url = "https://api.hunter.io/v2/account"
        params = {'api_key': api_key}
        
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            account = data.get('data', {})
            print(f"✅ HUNTER.IO CONNECTÉ")
            print(f"   - Email: {account.get('email', 'N/A')}")
            print(f"   - Requêtes restantes: {account.get('requests', {}).get('searches', {}).get('available', 'N/A')}")
            return True
        else:
            print(f"❌ Erreur de connexion: {response.status_code}")
            return False
        
    except Exception as e:
        print(f"⚠️  ERREUR HUNTER.IO: {e}")
        print("   (Optionnel - le scraper fonctionnera sans)")
        return True

def main():
    """Fonction principale de test"""
    print("\n" + "="*70)
    print("🚀 TEST DE CONFIGURATION - GOOGLE MAPS SCRAPER")
    print("="*70)
    
    results = {
        'Apify': test_apify(),
        'Google Sheets': test_google_sheets(),
        'GoHighLevel': test_gohighlevel(),
        'Hunter.io': test_hunter()
    }
    
    # Résumé
    print("\n" + "="*70)
    print("📊 RÉSUMÉ DES TESTS")
    print("="*70)
    
    for service, status in results.items():
        icon = "✅" if status else "❌"
        print(f"{icon} {service}: {'OK' if status else 'ERREUR'}")
    
    # Vérifier si les services essentiels sont OK
    essential_ok = results['Apify'] and results['Google Sheets']
    
    print("\n" + "="*70)
    if essential_ok:
        print("✅ CONFIGURATION PRÊTE")
        print("="*70)
        print("\n🎉 Tous les services essentiels sont configurés !")
        print("   Vous pouvez maintenant lancer le scraper avec:")
        print("   python scraper.py")
    else:
        print("⚠️  CONFIGURATION INCOMPLÈTE")
        print("="*70)
        print("\n❌ Certains services essentiels ont des erreurs")
        print("   Veuillez corriger les problèmes ci-dessus avant de continuer")
    
    print("\n")

if __name__ == "__main__":
    main()
