#!/usr/bin/env python3
"""
Interface interactive améliorée en ligne de commande
Pas de dépendances GUI, juste Python standard
"""

import sys
import os
from datetime import datetime

# Ajouter le répertoire courant au path pour importer le scraper
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scraper import GoogleMapsScraper

def print_header():
    """Affiche l'en-tête stylisé"""
    print("\n" + "="*70)
    print("🗺️  GOOGLE MAPS SCRAPER - Interface Interactive")
    print("="*70)
    print("✨ Extraction automatique d'entreprises et recherche d'emails")
    print("📊 Export vers Google Sheets | 🚀 Intégration GoHighLevel")
    print("="*70 + "\n")

def print_menu():
    """Affiche le menu principal"""
    print("🎯 MENU PRINCIPAL")
    print("-" * 30)
    print("1. 🚀 Lancer le scraping")
    print("2. ⚙️  Tester la configuration")
    print("3. 📋 Voir les dernières recherches")
    print("4. ❓ Aide")
    print("5. 🚪 Quitter")
    print("-" * 30)

def get_user_input():
    """Récupère les paramètres de l'utilisateur"""
    print("\n🔍 CONFIGURATION DU SCRAPING")
    print("-" * 40)
    
    # Recherche
    while True:
        search_query = input("📝 Recherche Google Maps (ex: restaurants à Paris): ").strip()
        if search_query:
            break
        print("❌ Veuillez saisir une recherche valide!")
    
    # Nombre de résultats
    while True:
        try:
            max_results_input = input("📊 Nombre d'entreprises [50]: ").strip()
            max_results = int(max_results_input) if max_results_input else 50
            
            if max_results < 1 or max_results > 200:
                print("⚠️  Veuillez choisir un nombre entre 1 et 200")
                continue
            
            break
        except ValueError:
            print("❌ Veuillez saisir un nombre valide!")
    
    print(f"\n✅ Configuration validée:")
    print(f"   🔍 Recherche: {search_query}")
    print(f"   📊 Nombre: {max_results} entreprises")
    
    return search_query, max_results

def confirm_start():
    """Demande confirmation avant de démarrer"""
    print("\n" + "-" * 50)
    confirm = input("🚀 Lancer le scraping? (O/n): ").strip().lower()
    return confirm in ['', 'o', 'oui', 'yes', 'y']

def run_test_config():
    """Test la configuration"""
    print("\n🧪 TEST DE CONFIGURATION")
    print("-" * 40)
    
    try:
        from test_config import main as test_main
        test_main()
    except Exception as e:
        print(f"❌ Erreur lors du test: {e}")
    
    input("\n📱 Appuyez sur Entrée pour continuer...")

def show_help():
    """Affiche l'aide"""
    print("\n❓ AIDE - GUIDE D'UTILISATION")
    print("=" * 50)
    
    help_text = """
🎯 COMMENT UTILISER LE SCRAPER:

1. CONFIGURATION REQUISE:
   ✅ Token Apify configuré
   ✅ Google Sheets partagé avec le service account
   ⚠️  GoHighLevel (optionnel)

2. TYPES DE RECHERCHES:
   • "restaurants à Paris"
   • "boulangeries Lyon"
   • "médecins Marseille"
   • "garages Bordeaux"

3. NOMBRE D'ENTREPRISES:
   • 10-50: Test rapide
   • 50-100: Usage normal
   • 100-200: Volume élevé

4. RÉSULTATS:
   📊 Google Maps → 📧 Emails → 📱 Google Sheets → 🚀 GoHighLevel

5. DÉPANNAGE:
   • Problème Google Sheets: Vérifiez le partage
   • Pas d'emails: Sites web sans contact
   • Erreur API: Vérifiez vos tokens

💡 CONSEILS:
   • Commencez avec 10-20 entreprises pour tester
   • Utilisez des recherches spécifiques
   • Vérifiez votre Google Sheet après chaque run
"""
    
    print(help_text)
    input("\n📱 Appuyez sur Entrée pour continuer...")

def show_history():
    """Affiche l'historique (simulation)"""
    print("\n📋 HISTORIQUE DES RECHERCHES")
    print("-" * 40)
    print("📝 Aucune recherche enregistrée")
    print("💡 L'historique sera ajouté dans une future version")
    input("\n📱 Appuyez sur Entrée pour continuer...")

def main():
    """Fonction principale de l'interface interactive"""
    
    while True:
        print_header()
        print_menu()
        
        choice = input("\n👆 Choisissez une option (1-5): ").strip()
        
        if choice == '1':
            # Lancer le scraping
            search_query, max_results = get_user_input()
            
            if confirm_start():
                print("\n" + "="*70)
                print("🚀 LANCEMENT DU SCRAPING...")
                print("="*70 + "\n")
                
                try:
                    scraper = GoogleMapsScraper()
                    scraper.run(search_query, max_results)
                except Exception as e:
                    print(f"\n❌ Erreur fatale: {e}")
                
                input("\n📱 Appuyez sur Entrée pour continuer...")
        
        elif choice == '2':
            # Tester la configuration
            run_test_config()
        
        elif choice == '3':
            # Voir l'historique
            show_history()
        
        elif choice == '4':
            # Aide
            show_help()
        
        elif choice == '5':
            # Quitter
            print("\n👋 Au revoir!")
            print("✨ Merci d'utiliser Google Maps Scraper")
            break
        
        else:
            print("\n❌ Option invalide! Veuillez choisir entre 1 et 5.")
            input("📱 Appuyez sur Entrée pour continuer...")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n👋 Programme interrompu. Au revoir!")
    except Exception as e:
        print(f"\n❌ Erreur inattendue: {e}")
        input("📱 Appuyez sur Entrée pour quitter...")
