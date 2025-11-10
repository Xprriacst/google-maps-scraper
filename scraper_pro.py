#!/usr/bin/env python3
"""
Scraper Pro - Version optimisée pour la prospection B2B
Intègre le scraping Google Maps + enrichissement + scoring automatique
"""

import os
import time
from datetime import datetime
from dotenv import load_dotenv
from apify_client import ApifyClient
import gspread
from google.oauth2.service_account import Credentials
from typing import Dict, List

from contact_enricher import ContactEnricher
from contact_scorer import ContactScorer
from database_manager import DatabaseManager

# Charger les variables d'environnement
load_dotenv()


class GoogleMapsScraperPro:
    """
    Scraper Google Maps optimisé pour la prospection B2B

    Workflow:
    1. Scraping Google Maps (Apify)
    2. Enrichissement automatique (contacts décisionnaires)
    3. Scoring automatique (0-100)
    4. Export contacts qualifiés uniquement
    """

    def __init__(self, min_score: int = 50):
        """
        Initialise le scraper pro

        Args:
            min_score: Score minimum pour exporter un contact (défaut: 50)
        """
        self.apify_token = os.getenv('APIFY_API_TOKEN')
        self.google_sheet_id = os.getenv('GOOGLE_SHEET_ID')

        # Vérifier les clés essentielles
        if not self.apify_token:
            raise ValueError("APIFY_API_TOKEN manquant dans .env")
        if not self.google_sheet_id:
            raise ValueError("GOOGLE_SHEET_ID manquant dans .env")

        # Initialiser les clients
        self.apify_client = ApifyClient(self.apify_token)
        self.google_sheet = None
        self.enricher = ContactEnricher()
        self.scorer = ContactScorer()
        self.db = DatabaseManager()  # Base de données pour le cache
        self.min_score = min_score

        self._init_google_sheets()

    def _init_google_sheets(self):
        """Initialise la connexion Google Sheets avec les nouvelles colonnes"""
        try:
            # Définir les scopes nécessaires
            scopes = [
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive'
            ]

            # Charger les credentials
            creds = Credentials.from_service_account_file(
                'credentials.json',
                scopes=scopes
            )

            # Autoriser gspread
            gc = gspread.authorize(creds)

            # Ouvrir le Google Sheet
            self.google_sheet = gc.open_by_key(self.google_sheet_id)

            # Créer ou récupérer la feuille "Prospection"
            try:
                worksheet = self.google_sheet.worksheet('Prospection')
            except:
                worksheet = self.google_sheet.add_worksheet('Prospection', rows=1000, cols=30)

                # Ajouter les en-têtes complets
                headers = [
                    # Contact
                    'Nom Contact',
                    'Fonction',
                    'Email',
                    'Confiance Email',
                    'LinkedIn',
                    'Téléphone Direct',

                    # Entreprise
                    'Nom Entreprise',
                    'SIRET',
                    'Adresse',
                    'Téléphone',
                    'Site Web',
                    'Note Google',
                    'Nb Avis',
                    'Catégorie',

                    # Enrichissement
                    'SIREN',
                    'Forme Juridique',
                    'CA',
                    'Employés',
                    'Date Création',

                    # Scoring
                    'Score Total (/100)',
                    'Score Email (/40)',
                    'Score Contact (/30)',
                    'Score Entreprise (/30)',
                    'Catégorie',
                    'Priorité',

                    # Métadonnées
                    'Sources Données',
                    'Date Ajout',
                    'Statut',  # À contacter / Contacté / Répondu
                    'URL Google Maps'
                ]
                worksheet.append_row(headers)

            print("✅ Connexion Google Sheets établie (Mode Prospection)")

        except FileNotFoundError:
            print("⚠️  Fichier credentials.json non trouvé. Google Sheets désactivé.")
            print("   Suivez les instructions du README pour configurer Google Sheets.")
        except Exception as e:
            print(f"⚠️  Erreur lors de l'initialisation Google Sheets: {e}")

    def scrape_google_maps(self, search_query: str, max_results: int = 50) -> List[Dict]:
        """
        Scrape Google Maps via Apify

        Args:
            search_query: La recherche à effectuer (ex: "fabricants vérandas Lyon")
            max_results: Nombre maximum de résultats (défaut: 50)

        Returns:
            Liste des entreprises trouvées
        """
        print(f"🔍 Recherche en cours: '{search_query}'")
        print(f"📊 Nombre de résultats demandés: {max_results}")

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
            print("🚀 Lancement du scraping Apify...")
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

    def enrich_and_score(self, raw_results: List[Dict]) -> List[Dict]:
        """
        Enrichit et score les résultats avec cache intelligent

        Args:
            raw_results: Résultats bruts d'Apify

        Returns:
            Liste enrichie et scorée
        """
        enriched_contacts = []
        cache_hits = 0
        new_enrichments = 0

        print(f"\n🔄 Phase d'enrichissement intelligent ({len(raw_results)} entreprises)")
        print("="*60)

        for idx, result in enumerate(raw_results, 1):
            company_name = result.get('title', '')
            print(f"\n[{idx}/{len(raw_results)}] {company_name}")

            # Données de base
            base_data = {
                'name': company_name,
                'address': result.get('address', ''),
                'phone': result.get('phone', ''),
                'website': result.get('website', ''),
                'rating': result.get('totalScore', ''),
                'reviews_count': result.get('reviewsCount', ''),
                'category': result.get('categoryName', ''),
                'url': result.get('url', ''),
            }

            # Vérifier le cache d'abord
            company_id = self.db.company_exists(
                company_name,
                base_data['website'],
                base_data['url']
            )

            if company_id:
                # Utiliser les données du cache
                print(f"  💾 Données trouvées en cache (évite l'enrichissement)")
                cached_data = self.db.get_company_data(company_id)

                # Mettre à jour avec les données fraîches de Google Maps
                full_data = {**cached_data, **base_data}
                cache_hits += 1
            else:
                # Enrichissement depuis zéro
                print(f"  🔍 Enrichissement en cours...")
                enriched = self.enricher.enrich_contact(
                    company_name,
                    base_data['website'],
                    base_data['address']
                )

                # Fusionner les données
                full_data = {**base_data, **enriched}

                # Scoring
                scoring = self.scorer.score_contact(full_data)
                full_data.update(scoring)

                # Sauvegarder dans la base
                company_id = self.db.save_company(full_data)
                new_enrichments += 1

            # Afficher le résultat
            print(f"  {full_data.get('emoji', '⚪')} Score: {full_data.get('score_total', 0)}/100 - {full_data.get('category', 'N/A')}")
            print(f"  📧 Email: {full_data.get('contact_email', 'N/A')} ({full_data.get('email_confidence', 'none')})")
            print(f"  👤 Contact: {full_data.get('contact_name', 'N/A')} - {full_data.get('contact_position', 'N/A')}")

            # Ajouter à la liste
            enriched_contacts.append(full_data)

        print("\n" + "="*60)
        print("✅ Enrichissement terminé")
        print(f"   💾 Cache: {cache_hits} entreprises")
        print(f"   🔍 Nouvelles: {new_enrichments} entreprises")

        # Afficher stats de la DB
        db_stats = self.db.get_stats()
        print(f"\n📊 Base de données totale:")
        print(f"   Entreprises: {db_stats['total_companies']}")
        print(f"   Avec emails: {db_stats['companies_with_email']}")

        return enriched_contacts

    def filter_qualified(self, contacts: List[Dict]) -> List[Dict]:
        """
        Filtre pour ne garder que les contacts qualifiés

        Args:
            contacts: Liste complète des contacts

        Returns:
            Liste filtrée par score minimum
        """
        qualified = [c for c in contacts if c.get('score_total', 0) >= self.min_score]
        qualified.sort(key=lambda x: x.get('score_total', 0), reverse=True)

        print(f"\n📊 Filtrage par score >= {self.min_score}")
        print(f"   Contacts qualifiés: {len(qualified)}/{len(contacts)}")

        return qualified

    def save_to_google_sheets(self, contacts: List[Dict]):
        """
        Sauvegarde les contacts dans Google Sheets

        Args:
            contacts: Liste de contacts enrichis et scorés
        """
        if not self.google_sheet:
            print("⚠️  Google Sheets non configuré, saut de cette étape")
            return

        try:
            worksheet = self.google_sheet.worksheet('Prospection')

            print(f"\n📝 Ajout de {len(contacts)} contacts dans Google Sheets...")

            for idx, contact in enumerate(contacts, 1):
                try:
                    # Préparer les sources de données
                    sources = ', '.join(contact.get('data_sources', []))

                    row = [
                        # Contact
                        contact.get('contact_name', ''),
                        contact.get('contact_position', ''),
                        contact.get('contact_email', ''),
                        contact.get('email_confidence', '').upper(),
                        contact.get('contact_linkedin', ''),
                        contact.get('contact_phone', ''),

                        # Entreprise
                        contact.get('name', ''),
                        contact.get('siret', ''),
                        contact.get('address', ''),
                        contact.get('phone', ''),
                        contact.get('website', ''),
                        contact.get('rating', ''),
                        contact.get('reviews_count', ''),
                        contact.get('category', ''),

                        # Enrichissement
                        contact.get('siren', ''),
                        contact.get('legal_form', ''),
                        contact.get('revenue', ''),
                        contact.get('employees', ''),
                        contact.get('creation_date', ''),

                        # Scoring
                        contact.get('score_total', ''),
                        contact.get('score_email', ''),
                        contact.get('score_contact', ''),
                        contact.get('score_company', ''),
                        f"{contact.get('emoji', '')} {contact.get('category', '')}",
                        contact.get('priority', ''),

                        # Métadonnées
                        sources,
                        datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'À contacter',
                        contact.get('url', '')
                    ]

                    worksheet.append_row(row)
                    time.sleep(0.5)  # Rate limiting

                except Exception as row_error:
                    # Vérifier si c'est une erreur de quota Google Drive
                    error_str = str(row_error)
                    if '403' in error_str and 'quota' in error_str.lower():
                        print(f"\n⚠️  ERREUR: Quota de stockage Google Drive dépassé !")
                        print(f"   Contact {idx}/{len(contacts)} - Impossible de continuer l'export vers Sheets")
                        print(f"\n💡 SOLUTIONS:")
                        print(f"   1. Libérez de l'espace sur votre Google Drive")
                        print(f"   2. Supprimez d'anciennes Google Sheets")
                        print(f"   3. Utilisez un autre compte Google")
                        print(f"\n📦 Les données seront automatiquement exportées en CSV comme alternative")
                        raise row_error  # Propager l'erreur pour le fallback
                    else:
                        print(f"⚠️  Erreur pour le contact {contact.get('name', 'N/A')}: {row_error}")
                        continue

            print("✅ Données ajoutées à Google Sheets")

        except Exception as e:
            error_str = str(e)
            # Gestion spécifique de l'erreur de quota
            if '403' in error_str and 'quota' in error_str.lower():
                print(f"\n❌ Erreur Google Sheets - Quota de stockage dépassé")
                print(f"   Message: {e}")
                print(f"\n💾 Export CSV activé automatiquement comme alternative")
                return False  # Indique que l'export a échoué
            else:
                print(f"❌ Erreur lors de l'ajout à Google Sheets: {e}")
                return False

        return True  # Export réussi

    def export_to_csv(self, contacts: List[Dict], filename: str = None):
        """
        Exporte les contacts en CSV

        Args:
            contacts: Liste de contacts
            filename: Nom du fichier (auto-généré si None)
        """
        import csv

        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"contacts_qualifies_{timestamp}.csv"

        try:
            with open(filename, 'w', newline='', encoding='utf-8') as f:
                if not contacts:
                    print("⚠️  Aucun contact à exporter")
                    return

                # Headers
                fieldnames = [
                    'nom_contact', 'fonction', 'email', 'confiance_email', 'linkedin',
                    'nom_entreprise', 'siret', 'adresse', 'telephone', 'site_web',
                    'note', 'nb_avis', 'score_total', 'categorie', 'priorite'
                ]

                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()

                for contact in contacts:
                    writer.writerow({
                        'nom_contact': contact.get('contact_name', ''),
                        'fonction': contact.get('contact_position', ''),
                        'email': contact.get('contact_email', ''),
                        'confiance_email': contact.get('email_confidence', ''),
                        'linkedin': contact.get('contact_linkedin', ''),
                        'nom_entreprise': contact.get('name', ''),
                        'siret': contact.get('siret', ''),
                        'adresse': contact.get('address', ''),
                        'telephone': contact.get('phone', ''),
                        'site_web': contact.get('website', ''),
                        'note': contact.get('rating', ''),
                        'nb_avis': contact.get('reviews_count', ''),
                        'score_total': contact.get('score_total', ''),
                        'categorie': contact.get('category', ''),
                        'priorite': contact.get('priority', ''),
                    })

            print(f"✅ Export CSV réussi: {filename}")

        except Exception as e:
            print(f"❌ Erreur export CSV: {e}")

    def run(self, search_query: str, max_results: int = 200, min_score: int = None):
        """
        Exécute le pipeline complet de prospection

        Args:
            search_query: Recherche à effectuer
            max_results: Nombre de résultats à scraper (défaut: 200)
            min_score: Score minimum pour filtrer (défaut: self.min_score)
        """
        if min_score is not None:
            self.min_score = min_score

        print("\n" + "="*60)
        print("🎯 SCRAPER PRO - PROSPECTION B2B")
        print("="*60 + "\n")

        # Phase 1: Extraction large
        print("📍 PHASE 1: Extraction large")
        print("-"*60)
        raw_results = self.scrape_google_maps(search_query, max_results)

        if not raw_results:
            print("❌ Aucun résultat trouvé. Arrêt du processus.")
            return

        # Phase 2: Enrichissement intelligent
        print("\n📍 PHASE 2: Enrichissement intelligent")
        print("-"*60)
        enriched = self.enrich_and_score(raw_results)

        # Phase 3: Scoring et qualification
        print("\n📍 PHASE 3: Scoring et qualification")
        print("-"*60)
        qualified = self.filter_qualified(enriched)

        # Statistiques
        stats = self.scorer.get_stats(enriched)

        print("\n" + "="*60)
        print("📊 STATISTIQUES FINALES")
        print("="*60)
        print(f"Total entreprises scrapées: {len(raw_results)}")
        print(f"Total enrichies: {len(enriched)}")
        print(f"Score moyen: {stats['avg_score']}/100")
        print(f"\n🟢 Premium (80-100): {stats['premium']} ({stats['premium_pct']}%)")
        print(f"🟡 Qualifiés (50-79): {stats['qualified']} ({stats['qualified_pct']}%)")
        print(f"🟠 À vérifier (20-49): {stats['verify']}")
        print(f"🔴 Faibles (0-19): {stats['weak']}")
        print(f"\n✅ Contacts qualifiés (score >= {self.min_score}): {len(qualified)}")

        # Export
        if qualified:
            print("\n" + "="*60)
            print("📤 EXPORT DES CONTACTS QUALIFIÉS")
            print("="*60)

            # Export Google Sheets
            sheets_success = self.save_to_google_sheets(qualified)

            # Export CSV (toujours fait, ou comme fallback si Sheets échoue)
            if sheets_success is False:
                print("\n💾 Export CSV de secours activé...")
            self.export_to_csv(qualified)

        print("\n" + "="*60)
        print("✅ PROCESSUS TERMINÉ AVEC SUCCÈS")
        print("="*60 + "\n")

        return {
            'raw_count': len(raw_results),
            'enriched_count': len(enriched),
            'qualified_count': len(qualified),
            'stats': stats,
            'qualified_contacts': qualified
        }


def main():
    """Fonction principale"""
    print("\n🚀 Google Maps Scraper PRO - Prospection B2B\n")

    # Demander les paramètres
    search_query = input("🔍 Entrez votre recherche (ex: 'fabricants vérandas Lyon'): ").strip()

    if not search_query:
        print("❌ Recherche vide. Arrêt du programme.")
        return

    max_results_input = input("📊 Nombre d'entreprises à scraper [200]: ").strip()
    max_results = int(max_results_input) if max_results_input else 200

    min_score_input = input("⭐ Score minimum pour qualifier un contact [50]: ").strip()
    min_score = int(min_score_input) if min_score_input else 50

    try:
        # Créer et exécuter le scraper pro
        scraper = GoogleMapsScraperPro(min_score=min_score)
        scraper.run(search_query, max_results, min_score)

    except Exception as e:
        print(f"\n❌ Erreur fatale: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
