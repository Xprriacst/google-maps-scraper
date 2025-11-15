#!/usr/bin/env python3
"""
Script CLI pour exécuter le Google Maps Scraper Simple
Supporte l'entrée manuelle ou depuis un fichier
"""

import sys
import argparse
from scraper_simple import GoogleMapsScraperSimple


def load_cities_from_file(filename):
    """
    Charge une liste de villes depuis un fichier texte

    Args:
        filename: Nom du fichier contenant les villes (une par ligne)

    Returns:
        Liste des villes
    """
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            cities = [line.strip() for line in f if line.strip()]
        print(f"✅ {len(cities)} villes chargées depuis {filename}")
        return cities
    except FileNotFoundError:
        print(f"❌ Fichier non trouvé: {filename}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Erreur lors de la lecture du fichier: {e}")
        sys.exit(1)


def interactive_mode():
    """Mode interactif pour entrer les paramètres manuellement"""
    print("\n🚀 Google Maps Scraper Simple - Mode Interactif\n")

    # Terme de recherche
    search_term = input("🔍 Terme de recherche (ex: 'restaurants', 'menuisiers'): ").strip()
    if not search_term:
        print("❌ Terme de recherche vide. Arrêt.")
        sys.exit(1)

    # Villes
    print("\n📍 Entrez les villes:")
    print("   Option 1: Tapez-les séparées par des virgules (ex: Paris, Lyon, Marseille)")
    print("   Option 2: Entrez le chemin d'un fichier texte (ex: villes.txt)")
    cities_input = input("\n   Votre choix: ").strip()

    if not cities_input:
        print("❌ Aucune ville fournie. Arrêt.")
        sys.exit(1)

    # Vérifier si c'est un fichier
    if cities_input.endswith('.txt') or '/' in cities_input or '\\' in cities_input:
        cities = load_cities_from_file(cities_input)
    else:
        cities = [city.strip() for city in cities_input.split(',')]

    # Nombre de résultats
    max_results_input = input("\n📊 Max résultats par ville [50]: ").strip()
    max_results = int(max_results_input) if max_results_input else 50

    # Nom du fichier de sortie (optionnel)
    output_file = input("\n💾 Nom du fichier CSV de sortie (optionnel, appuyez sur Entrée pour auto): ").strip()
    if not output_file:
        output_file = None

    return search_term, cities, max_results, output_file


def main():
    """Fonction principale"""
    parser = argparse.ArgumentParser(
        description='Google Maps Scraper Simple - Scrape des entreprises depuis Google Maps',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples d'utilisation:

  Mode interactif:
    python run_scraper.py

  Avec arguments:
    python run_scraper.py -s "restaurants" -c "Paris,Lyon,Marseille" -m 100

  Avec fichier de villes:
    python run_scraper.py -s "menuisiers" -f villes.txt -m 50

  Avec sortie personnalisée:
    python run_scraper.py -s "plombiers" -c "Paris,Lyon" -o mes_resultats.csv

Format du fichier de villes (une ville par ligne):
    Paris
    Lyon
    Marseille
    Toulouse
        """
    )

    parser.add_argument(
        '-s', '--search',
        help='Terme de recherche (ex: "restaurants", "menuisiers")'
    )

    parser.add_argument(
        '-c', '--cities',
        help='Villes séparées par des virgules (ex: "Paris,Lyon,Marseille")'
    )

    parser.add_argument(
        '-f', '--file',
        help='Fichier texte contenant les villes (une par ligne)'
    )

    parser.add_argument(
        '-m', '--max-results',
        type=int,
        default=50,
        help='Nombre maximum de résultats par ville (défaut: 50)'
    )

    parser.add_argument(
        '-o', '--output',
        help='Nom du fichier CSV de sortie (optionnel)'
    )

    parser.add_argument(
        '-t', '--token',
        help='Token API Apify (optionnel, lu depuis .env si non fourni)'
    )

    args = parser.parse_args()

    # Si aucun argument, mode interactif
    if not args.search and not args.cities and not args.file:
        search_term, cities, max_results, output_file = interactive_mode()
    else:
        # Vérifier les arguments requis
        if not args.search:
            print("❌ Erreur: Le terme de recherche (-s) est requis")
            parser.print_help()
            sys.exit(1)

        if not args.cities and not args.file:
            print("❌ Erreur: Les villes (-c) ou un fichier de villes (-f) est requis")
            parser.print_help()
            sys.exit(1)

        search_term = args.search
        max_results = args.max_results
        output_file = args.output

        # Charger les villes
        if args.file:
            cities = load_cities_from_file(args.file)
        else:
            cities = [city.strip() for city in args.cities.split(',')]

    # Afficher le résumé
    print("\n" + "="*70)
    print("📋 CONFIGURATION")
    print("="*70)
    print(f"🔍 Recherche: {search_term}")
    print(f"📍 Villes ({len(cities)}): {', '.join(cities[:5])}" + ("..." if len(cities) > 5 else ""))
    print(f"📊 Max résultats/ville: {max_results}")
    if output_file:
        print(f"💾 Fichier de sortie: {output_file}")
    print("="*70 + "\n")

    # Confirmer
    confirm = input("Continuer ? [O/n]: ").strip().lower()
    if confirm and confirm not in ['o', 'oui', 'y', 'yes']:
        print("❌ Annulé par l'utilisateur")
        sys.exit(0)

    try:
        # Créer et exécuter le scraper
        scraper = GoogleMapsScraperSimple(apify_token=args.token if 'token' in args else None)
        results, csv_file = scraper.run(search_term, cities, max_results, output_file)

        print("\n" + "="*70)
        print("✅ SCRAPING TERMINÉ AVEC SUCCÈS!")
        print("="*70)
        print(f"📊 {len(results)} entreprises scrapées")
        print(f"💾 Fichier créé: {csv_file}")
        print("="*70 + "\n")

    except KeyboardInterrupt:
        print("\n\n❌ Arrêt par l'utilisateur (Ctrl+C)")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
