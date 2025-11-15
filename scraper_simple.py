#!/usr/bin/env python3
"""
Google Maps Scraper Simple
Scrape des entreprises depuis Google Maps pour plusieurs villes et exporte en CSV
"""

import os
import csv
import time
from datetime import datetime
from dotenv import load_dotenv
from apify_client import ApifyClient

# Charger les variables d'environnement
load_dotenv()


class GoogleMapsScraperSimple:
    def __init__(self, apify_token=None):
        """
        Initialise le scraper avec la clé API Apify

        Args:
            apify_token: Token API Apify (optionnel, lu depuis .env si non fourni)
        """
        self.apify_token = apify_token or os.getenv('APIFY_API_TOKEN')

        if not self.apify_token:
            raise ValueError("APIFY_API_TOKEN manquant. Fournissez-le en paramètre ou dans .env")

        self.apify_client = ApifyClient(self.apify_token)
        self.all_results = []

    def scrape_google_maps(self, search_query, max_results=50):
        """
        Scrape Google Maps via Apify pour une requête donnée

        Args:
            search_query: La recherche à effectuer (ex: "restaurants à Paris")
            max_results: Nombre maximum de résultats par recherche (défaut: 50)

        Returns:
            Liste des entreprises trouvées
        """
        print(f"🔍 Recherche: '{search_query}'")
        print(f"📊 Max résultats: {max_results}")

        # Configuration de l'Actor Apify pour Google Maps
        run_input = {
            "searchStringsArray": [search_query],
            "maxCrawledPlacesPerSearch": max_results,
            "language": "fr",
            "deeperCityScrape": False,
            "scrapeReviewerName": False,
            "scrapeReviewerId": False,
            "scrapeReviewId": False,
            "scrapeReviewUrl": False,
            "scrapeResponseFromOwnerText": False,
            "scrapeReviewsPersonalData": False,
        }

        try:
            # Lancer l'actor
            print("🚀 Lancement du scraping...")
            run = self.apify_client.actor("compass/crawler-google-places").call(run_input=run_input)

            # Récupérer les résultats
            print("📥 Récupération des résultats...")
            results = []
            for item in self.apify_client.dataset(run["defaultDatasetId"]).iterate_items():
                results.append(item)

            print(f"✅ {len(results)} entreprises trouvées")
            return results

        except Exception as e:
            print(f"❌ Erreur lors du scraping: {e}")
            return []

    def scrape_multiple_cities(self, search_term, cities, max_results_per_city=50):
        """
        Scrape Google Maps pour une recherche dans plusieurs villes

        Args:
            search_term: Le terme de recherche (ex: "restaurants", "menuisiers")
            cities: Liste des villes (ex: ["Paris", "Lyon", "Marseille"])
            max_results_per_city: Nombre max de résultats par ville (défaut: 50)

        Returns:
            Liste de toutes les entreprises trouvées
        """
        print("\n" + "="*70)
        print("🗺️  GOOGLE MAPS SCRAPER SIMPLE")
        print("="*70)
        print(f"📍 Recherche: {search_term}")
        print(f"🏙️  Villes: {', '.join(cities)}")
        print(f"📊 Max résultats par ville: {max_results_per_city}")
        print("="*70 + "\n")

        all_results = []

        for idx, city in enumerate(cities, 1):
            print(f"\n[{idx}/{len(cities)}] 🏙️  Ville: {city}")
            print("-" * 70)

            # Construire la requête complète
            search_query = f"{search_term} {city}"

            # Scraper pour cette ville
            results = self.scrape_google_maps(search_query, max_results_per_city)

            # Ajouter la ville dans les résultats
            for result in results:
                result['search_city'] = city
                result['search_term'] = search_term

            all_results.extend(results)

            # Pause entre les requêtes pour éviter les rate limits
            if idx < len(cities):
                print("⏸️  Pause de 2 secondes...")
                time.sleep(2)

        print("\n" + "="*70)
        print(f"✅ SCRAPING TERMINÉ - Total: {len(all_results)} entreprises")
        print("="*70 + "\n")

        self.all_results = all_results
        return all_results

    def export_to_csv(self, filename=None, results=None):
        """
        Exporte les résultats en CSV

        Args:
            filename: Nom du fichier CSV (optionnel, généré automatiquement si non fourni)
            results: Résultats à exporter (optionnel, utilise self.all_results si non fourni)

        Returns:
            Nom du fichier créé
        """
        if results is None:
            results = self.all_results

        if not results:
            print("⚠️  Aucun résultat à exporter")
            return None

        # Générer le nom de fichier si non fourni
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"google_maps_results_{timestamp}.csv"

        # S'assurer que le fichier a l'extension .csv
        if not filename.endswith('.csv'):
            filename += '.csv'

        print(f"💾 Export vers: {filename}")

        # En-têtes CSV
        headers = [
            'Nom',
            'Adresse',
            'Téléphone',
            'Site Web',
            'Note',
            'Nombre Avis',
            'Catégorie',
            'Ville de recherche',
            'Terme de recherche',
            'URL Google Maps',
            'Latitude',
            'Longitude',
            'Plus Code',
            'Horaires',
            'Description'
        ]

        try:
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=headers)
                writer.writeheader()

                for result in results:
                    # Extraire les horaires s'ils existent
                    opening_hours = ''
                    if result.get('openingHours'):
                        opening_hours = ' | '.join(result.get('openingHours', []))

                    row = {
                        'Nom': result.get('title', ''),
                        'Adresse': result.get('address', ''),
                        'Téléphone': result.get('phone', ''),
                        'Site Web': result.get('website', ''),
                        'Note': result.get('totalScore', ''),
                        'Nombre Avis': result.get('reviewsCount', ''),
                        'Catégorie': result.get('categoryName', ''),
                        'Ville de recherche': result.get('search_city', ''),
                        'Terme de recherche': result.get('search_term', ''),
                        'URL Google Maps': result.get('url', ''),
                        'Latitude': result.get('location', {}).get('lat', ''),
                        'Longitude': result.get('location', {}).get('lng', ''),
                        'Plus Code': result.get('plusCode', ''),
                        'Horaires': opening_hours,
                        'Description': result.get('description', '')
                    }
                    writer.writerow(row)

            print(f"✅ {len(results)} entreprises exportées dans {filename}")
            return filename

        except Exception as e:
            print(f"❌ Erreur lors de l'export CSV: {e}")
            return None

    def run(self, search_term, cities, max_results_per_city=50, output_filename=None):
        """
        Exécute le pipeline complet: scraping + export CSV

        Args:
            search_term: Terme de recherche (ex: "restaurants")
            cities: Liste des villes (ex: ["Paris", "Lyon"])
            max_results_per_city: Max résultats par ville (défaut: 50)
            output_filename: Nom du fichier CSV de sortie (optionnel)

        Returns:
            Tuple (résultats, nom_fichier_csv)
        """
        # Scraper toutes les villes
        results = self.scrape_multiple_cities(search_term, cities, max_results_per_city)

        # Exporter en CSV
        csv_file = self.export_to_csv(output_filename, results)

        # Afficher les statistiques
        print("\n📊 STATISTIQUES:")
        print(f"   - Total entreprises: {len(results)}")
        print(f"   - Villes scrapées: {len(cities)}")
        print(f"   - Moyenne par ville: {len(results) / len(cities):.1f}")

        # Statistiques par ville
        print("\n📍 PAR VILLE:")
        cities_count = {}
        for result in results:
            city = result.get('search_city', 'Inconnue')
            cities_count[city] = cities_count.get(city, 0) + 1

        for city, count in sorted(cities_count.items()):
            print(f"   - {city}: {count} entreprises")

        return results, csv_file


def main():
    """Fonction principale pour utilisation en ligne de commande"""
    print("\n🚀 Google Maps Scraper Simple\n")

    # Demander le terme de recherche
    search_term = input("🔍 Terme de recherche (ex: 'restaurants', 'menuisiers'): ").strip()
    if not search_term:
        print("❌ Terme de recherche vide. Arrêt.")
        return

    # Demander les villes
    print("\n📍 Entrez les villes (séparées par des virgules)")
    cities_input = input("   Ex: Paris, Lyon, Marseille: ").strip()
    if not cities_input:
        print("❌ Aucune ville fournie. Arrêt.")
        return

    cities = [city.strip() for city in cities_input.split(',')]

    # Demander le nombre de résultats
    max_results_input = input("\n📊 Max résultats par ville [50]: ").strip()
    max_results = int(max_results_input) if max_results_input else 50

    try:
        # Créer et exécuter le scraper
        scraper = GoogleMapsScraperSimple()
        scraper.run(search_term, cities, max_results)

        print("\n✅ TERMINÉ AVEC SUCCÈS!\n")

    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
