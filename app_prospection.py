#!/usr/bin/env python3
"""
Interface CLI interactive pour le Scraper Pro
Mode prospection B2B optimisé
"""

import os
import sys
from datetime import datetime


def clear_screen():
    """Efface l'écran"""
    os.system('clear' if os.name != 'nt' else 'cls')


def print_header():
    """Affiche l'en-tête"""
    clear_screen()
    print("="*70)
    print(" " * 15 + "🎯 SCRAPER PRO - PROSPECTION B2B")
    print("="*70)
    print()


def print_menu():
    """Affiche le menu principal"""
    print("\n📋 MENU PRINCIPAL")
    print("-" * 70)
    print()
    print("  1. 🚀 Lancer une prospection")
    print("  2. ⚙️  Configurer les paramètres")
    print("  3. 📊 Voir les statistiques de scoring")
    print("  4. 🧪 Tester la configuration")
    print("  5. ❓ Aide et documentation")
    print("  6. 🚪 Quitter")
    print()
    print("-" * 70)


def get_prospection_params():
    """
    Récupère les paramètres de prospection auprès de l'utilisateur

    Returns:
        Dict avec search_query, max_results, min_score
    """
    print("\n🔍 CONFIGURATION DE LA PROSPECTION")
    print("-" * 70)
    print()

    # Exemples de recherches
    print("💡 Exemples de recherches:")
    print("   - fabricants vérandas Lyon")
    print("   - installateurs fenêtres Paris")
    print("   - menuisiers Marseille")
    print("   - entreprises rénovation Toulouse")
    print()

    search_query = input("🔍 Votre recherche: ").strip()

    if not search_query:
        print("❌ Recherche vide")
        return None

    print("\n📊 Nombre d'entreprises à scraper")
    print("   Recommandation: 200 entreprises pour obtenir ~50 contacts qualifiés")
    max_results_input = input("   Nombre d'entreprises [200]: ").strip()
    max_results = int(max_results_input) if max_results_input else 200

    print("\n⭐ Score minimum pour qualifier un contact")
    print("   - 80-100: 🟢 Contact premium (email + nom + décideur)")
    print("   - 50-79:  🟡 Contact qualifié (email + infos partielles)")
    print("   - 20-49:  🟠 Contact à vérifier (email générique)")
    print("   - 0-19:   🔴 Contact faible (peu d'infos)")
    print()
    print("   Recommandation: 50 (contacts qualifiés et premium)")
    min_score_input = input("   Score minimum [50]: ").strip()
    min_score = int(min_score_input) if min_score_input else 50

    return {
        'search_query': search_query,
        'max_results': max_results,
        'min_score': min_score
    }


def show_scoring_info():
    """Affiche les informations sur le système de scoring"""
    print("\n📊 SYSTÈME DE SCORING - GUIDE COMPLET")
    print("="*70)

    print("\n🎯 SCORE TOTAL: 0-100 points")
    print("-"*70)
    print("\nLe score est calculé sur 3 critères:")
    print()
    print("  1. 📧 Qualité Email (40 points max)")
    print("     - Email HIGH + nom vérifié + personnalisé:  40 pts")
    print("     - Email HIGH + nom:                         35 pts")
    print("     - Email MEDIUM + nom + personnalisé:        25 pts")
    print("     - Email générique (contact@):               5-10 pts")
    print()
    print("  2. 👤 Qualité Contact (30 points max)")
    print("     - Nom + Fonction décideur trouvés:          30 pts")
    print("     - Nom + Fonction quelconque:                20 pts")
    print("     - Nom seulement:                            15 pts")
    print("     - Fonction seulement:                       10 pts")
    print()
    print("  3. 🏢 Qualité Entreprise (30 points max)")
    print("     - Note 4.5+ avec 50+ avis + site web:       30 pts")
    print("     - Note 4.0+ avec 20+ avis + site web:       20 pts")
    print("     - Note 3.5+ avec site web:                  10 pts")
    print()

    print("\n📈 CATÉGORIES DE CONTACTS")
    print("-"*70)
    print()
    print("  🟢 Premium (80-100 points)")
    print("     → Email personnalisé + Nom du décideur + Entreprise solide")
    print("     → ACTION: Prospecter en priorité absolue")
    print()
    print("  🟡 Qualifié (50-79 points)")
    print("     → Email + Infos partielles + Entreprise correcte")
    print("     → ACTION: Prospecter ensuite")
    print()
    print("  🟠 À vérifier (20-49 points)")
    print("     → Email générique ou infos incomplètes")
    print("     → ACTION: Vérification manuelle recommandée")
    print()
    print("  🔴 Faible (0-19 points)")
    print("     → Très peu d'informations")
    print("     → ACTION: Skip ou vérifier manuellement")
    print()

    print("\n💡 EXEMPLE CONCRET")
    print("-"*70)
    print()
    print("  Entreprise: Véranda Concept Lyon")
    print("  Contact trouvé: Marc Durand - Directeur Commercial")
    print("  Email: marc.durand@veranda-concept-lyon.fr (HIGH)")
    print("  LinkedIn: ✓")
    print("  Note: 4.7/5 (85 avis)")
    print("  Site: veranda-concept-lyon.fr")
    print("  SIRET: ✓")
    print()
    print("  📊 SCORING:")
    print("     Email:      40/40 (email personnalisé + nom)")
    print("     Contact:    30/30 (nom + fonction décideur)")
    print("     Entreprise: 30/30 (note excellente + site pro)")
    print("     ─────────────────")
    print("     TOTAL:      100/100 🟢 PREMIUM")
    print()
    print("  ✅ RECOMMANDATION: Prospecter immédiatement")
    print()

    input("\n👉 Appuyez sur Entrée pour revenir au menu...")


def test_configuration():
    """Teste la configuration de l'environnement"""
    print("\n🧪 TEST DE CONFIGURATION")
    print("="*70)
    print()

    from dotenv import load_dotenv
    load_dotenv()

    # Test des clés API
    print("🔑 Vérification des clés API...")
    print()

    tests = {
        'APIFY_API_TOKEN': os.getenv('APIFY_API_TOKEN'),
        'GOOGLE_SHEET_ID': os.getenv('GOOGLE_SHEET_ID'),
    }

    all_ok = True

    for key, value in tests.items():
        if value and value != f'your_{key.lower()}_here':
            print(f"  ✅ {key}: Configuré")
        else:
            print(f"  ❌ {key}: Non configuré")
            all_ok = False

    # Test credentials.json
    print()
    if os.path.exists('credentials.json'):
        print("  ✅ credentials.json: Trouvé")
    else:
        print("  ❌ credentials.json: Non trouvé")
        all_ok = False

    # Test des modules
    print()
    print("📦 Vérification des modules...")
    print()

    try:
        from contact_enricher import ContactEnricher
        print("  ✅ contact_enricher: OK")
    except ImportError as e:
        print(f"  ❌ contact_enricher: {e}")
        all_ok = False

    try:
        from contact_scorer import ContactScorer
        print("  ✅ contact_scorer: OK")
    except ImportError as e:
        print(f"  ❌ contact_scorer: {e}")
        all_ok = False

    try:
        from scraper_pro import GoogleMapsScraperPro
        print("  ✅ scraper_pro: OK")
    except ImportError as e:
        print(f"  ❌ scraper_pro: {e}")
        all_ok = False

    print()
    print("="*70)

    if all_ok:
        print("✅ Configuration OK - Prêt à lancer une prospection!")
    else:
        print("⚠️  Configuration incomplète - Consultez le README")

    print()
    input("\n👉 Appuyez sur Entrée pour revenir au menu...")


def show_help():
    """Affiche l'aide"""
    print("\n❓ AIDE ET DOCUMENTATION")
    print("="*70)
    print()
    print("🎯 QU'EST-CE QUE LE SCRAPER PRO ?")
    print()
    print("Le Scraper Pro est un outil de prospection B2B qui automatise:")
    print()
    print("  1. 🔍 Scraping Google Maps (Apify)")
    print("     → Trouve des entreprises ciblées par recherche")
    print()
    print("  2. 🔎 Enrichissement intelligent")
    print("     → Trouve les décideurs (Directeur, Gérant, etc.)")
    print("     → Scrape les sites web (pages équipe, mentions légales)")
    print("     → Construit les emails personnalisés")
    print("     → Enrichit avec APIs publiques (SIRET, CA, etc.)")
    print()
    print("  3. ⭐ Scoring automatique")
    print("     → Note chaque contact de 0 à 100")
    print("     → Filtre pour ne garder que les meilleurs contacts")
    print()
    print("  4. 📤 Export multi-format")
    print("     → Google Sheets (feuille 'Prospection')")
    print("     → CSV (téléchargement local)")
    print()

    print("\n📊 WORKFLOW COMPLET")
    print("-"*70)
    print()
    print("  Entrée:  'fabricants vérandas Lyon'")
    print("           ↓")
    print("  Phase 1: Scraping de 200 entreprises")
    print("           ↓")
    print("  Phase 2: Enrichissement de chaque entreprise")
    print("           → Recherche du décideur")
    print("           → Construction de l'email")
    print("           → Appel API SIRET")
    print("           ↓")
    print("  Phase 3: Scoring (0-100)")
    print("           → Filtrage (score >= 50)")
    print("           ↓")
    print("  Sortie:  ~50 contacts qualifiés prêts à prospecter")
    print()

    print("\n💡 CONSEILS D'UTILISATION")
    print("-"*70)
    print()
    print("  • Utilisez des recherches précises")
    print("    ✅ BON: 'fabricants vérandas Lyon'")
    print("    ❌ ÉVITER: 'vérandas' (trop large)")
    print()
    print("  • Scrapez plus pour avoir plus de qualifiés")
    print("    → 200 entreprises → ~50 contacts qualifiés (25%)")
    print("    → 100 entreprises → ~25 contacts qualifiés")
    print()
    print("  • Ajustez le score minimum selon vos besoins")
    print("    → Score 80: Contacts premium uniquement (10-20%)")
    print("    → Score 50: Bon équilibre qualité/quantité (25-30%)")
    print("    → Score 20: Plus de contacts mais à vérifier (50%+)")
    print()

    print("\n🔗 RESSOURCES")
    print("-"*70)
    print()
    print("  📖 README.md - Documentation complète")
    print("  🌐 APIs utilisées:")
    print("     - Apify (scraping Google Maps)")
    print("     - entreprise.data.gouv.fr (SIRET/SIREN)")
    print()

    input("\n👉 Appuyez sur Entrée pour revenir au menu...")


def configure_settings():
    """Configure les paramètres"""
    print("\n⚙️  CONFIGURATION")
    print("="*70)
    print()
    print("Pour configurer l'application, éditez le fichier .env")
    print()
    print("Clés requises:")
    print("  - APIFY_API_TOKEN: Votre token Apify")
    print("  - GOOGLE_SHEET_ID: ID de votre Google Sheet")
    print()
    print("Fichier requis:")
    print("  - credentials.json: Credentials Google Sheets API")
    print()
    print("Consultez le README.md pour plus de détails")
    print()

    input("\n👉 Appuyez sur Entrée pour revenir au menu...")


def run_prospection():
    """Lance une prospection"""
    print_header()

    # Récupérer les paramètres
    params = get_prospection_params()

    if not params:
        input("\n👉 Appuyez sur Entrée pour revenir au menu...")
        return

    # Confirmation
    print("\n✅ RÉCAPITULATIF")
    print("-"*70)
    print(f"  Recherche: {params['search_query']}")
    print(f"  Entreprises à scraper: {params['max_results']}")
    print(f"  Score minimum: {params['min_score']}")
    print()

    confirm = input("👉 Lancer la prospection ? [O/n]: ").strip().lower()

    if confirm and confirm != 'o' and confirm != 'oui' and confirm != 'y' and confirm != 'yes':
        print("\n❌ Prospection annulée")
        input("\n👉 Appuyez sur Entrée pour revenir au menu...")
        return

    # Lancer la prospection
    print("\n" + "="*70)
    print("🚀 LANCEMENT DE LA PROSPECTION")
    print("="*70)
    print()

    try:
        from scraper_pro import GoogleMapsScraperPro

        scraper = GoogleMapsScraperPro(min_score=params['min_score'])
        result = scraper.run(
            params['search_query'],
            params['max_results'],
            params['min_score']
        )

        # Résumé final
        print("\n" + "="*70)
        print("🎉 PROSPECTION TERMINÉE AVEC SUCCÈS")
        print("="*70)
        print()
        print(f"📊 Résultats:")
        print(f"   - Entreprises scrapées: {result['raw_count']}")
        print(f"   - Entreprises enrichies: {result['enriched_count']}")
        print(f"   - Contacts qualifiés exportés: {result['qualified_count']}")
        print()
        print(f"✅ Les contacts qualifiés ont été exportés:")
        print(f"   - Google Sheets (feuille 'Prospection')")
        print(f"   - Fichier CSV local")
        print()

    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()

    input("\n👉 Appuyez sur Entrée pour revenir au menu...")


def main():
    """Fonction principale"""
    while True:
        print_header()
        print_menu()

        choice = input("👉 Votre choix [1-6]: ").strip()

        if choice == '1':
            run_prospection()
        elif choice == '2':
            configure_settings()
        elif choice == '3':
            show_scoring_info()
        elif choice == '4':
            test_configuration()
        elif choice == '5':
            show_help()
        elif choice == '6':
            print("\n👋 Au revoir!\n")
            sys.exit(0)
        else:
            print("\n❌ Choix invalide")
            input("\n👉 Appuyez sur Entrée pour continuer...")


if __name__ == "__main__":
    main()
