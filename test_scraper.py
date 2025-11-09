#!/usr/bin/env python3
"""
Script de test automatique pour le scraper
"""

from scraper import GoogleMapsScraper

def test_scraper():
    """Test avec 5 entreprises"""
    print("\n" + "="*70)
    print("🧪 TEST AUTOMATIQUE DU SCRAPER")
    print("="*70 + "\n")
    
    # Paramètres de test
    search_query = "boulangeries à Paris"
    max_results = 5
    
    print(f"📋 Paramètres du test:")
    print(f"   - Recherche: {search_query}")
    print(f"   - Nombre: {max_results} entreprises")
    print()
    
    try:
        # Créer et exécuter le scraper
        scraper = GoogleMapsScraper()
        scraper.run(search_query, max_results)
        
        print("\n" + "="*70)
        print("✅ TEST RÉUSSI !")
        print("="*70)
        print("\nVérifiez votre Google Sheet pour voir les résultats.")
        
    except Exception as e:
        print(f"\n❌ ERREUR PENDANT LE TEST: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_scraper()
