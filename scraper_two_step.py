#!/usr/bin/env python3
"""
Scraper en 2 étapes : Entreprises puis People
Architecture moderne avec séparation claire des responsabilités

ÉTAPE 1 - Scraper Entreprises :
- Google Maps → Entreprises
- Filtrage blacklist
- Enrichissement (SIRET, effectifs, CA)
- Export Tab "Entreprises"

ÉTAPE 2 - Scraper Contacts :
- Lecture Tab "Entreprises"
- Recherche contacts multi-sources (Apollo, Dropcontact, EmailFinder, Website)
- Export Tab "People" avec colonnes par source

"""

import os
import time
from datetime import datetime
from typing import Dict, List, Optional
from dotenv import load_dotenv
from apify_client import ApifyClient
import gspread
from google.oauth2.service_account import Credentials

from company_blacklist import CompanyBlacklist
from apollo_apify_scraper import ApolloApifyScraper
from contact_enricher import ContactEnricher
from database_manager import DatabaseManager
from gpt_contact_scraper import GPTContactScraper
from utils import get_env, get_gcp_credentials

load_dotenv()


class TwoStepScraper:
    """Scraper moderne en 2 étapes : Entreprises → People"""

    def __init__(self):
        """Initialise le scraper"""
        self.apify_token = get_env('APIFY_API_TOKEN')
        self.google_sheet_id = get_env('GOOGLE_SHEET_ID')

        if not self.apify_token:
            raise ValueError("APIFY_API_TOKEN manquant")
        if not self.google_sheet_id:
            raise ValueError("GOOGLE_SHEET_ID manquant")

        # Clients
        self.apify_client = ApifyClient(self.apify_token)
        self.google_sheet = None
        self.blacklist = CompanyBlacklist()
        self.apollo_scraper = ApolloApifyScraper(self.apify_token)
        self.gpt_scraper = GPTContactScraper()
        self.enricher = ContactEnricher(use_adaptive_targeting=False)  # On gère manuellement
        self.db = DatabaseManager()

        self._init_google_sheets()

        print("✅ TwoStepScraper initialisé")

    def _init_google_sheets(self):
        """Initialise Google Sheets avec 2 onglets"""
        try:
            scopes = [
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive'
            ]

            # Credentials
            creds_data = get_gcp_credentials()
            if isinstance(creds_data, dict):
                # Streamlit secrets
                creds = Credentials.from_service_account_info(creds_data, scopes=scopes)
            else:
                # Fichier local
                creds = Credentials.from_service_account_file('credentials.json', scopes=scopes)

            gc = gspread.authorize(creds)
            self.google_sheet = gc.open_by_key(self.google_sheet_id)

            # Créer ou récupérer les onglets
            self._setup_companies_sheet()
            self._setup_people_sheet()

            print("✅ Google Sheets initialisé (2 onglets)")

        except Exception as e:
            print(f"❌ Erreur Google Sheets: {e}")
            raise

    def _setup_companies_sheet(self):
        """Configure l'onglet Entreprises"""
        try:
            worksheet = self.google_sheet.worksheet('Entreprises')
        except:
            worksheet = self.google_sheet.add_worksheet('Entreprises', rows=1000, cols=20)

            # Headers Tab Entreprises
            headers = [
                # IDENTIFICATION
                'Nom',
                'Adresse',
                'Ville',
                'Téléphone',
                'Site Web',

                # GOOGLE MAPS
                'Note Google',
                'Nombre Avis',
                'Catégorie',
                'URL Google Maps',

                # ENRICHISSEMENT
                'SIRET',
                'SIREN',
                'Forme Juridique',
                'Effectifs',
                'CA Estimé',
                'Date Création',

                # MÉTADONNÉES
                'Date Ajout',
                'Statut',  # 'nouveau', 'en_cours', 'terminé'
                'Nb Contacts Trouvés',
            ]

            worksheet.update('A1:R1', [headers])
            print("✅ Onglet 'Entreprises' créé")

    def _setup_people_sheet(self):
        """Configure l'onglet People (contacts par source)"""
        try:
            worksheet = self.google_sheet.worksheet('People')
        except:
            worksheet = self.google_sheet.add_worksheet('People', rows=5000, cols=25)

            # Headers Tab People - Colonnes par source !
            headers = [
                # ENTREPRISE (FK)
                'Nom Entreprise',
                'Domaine',

                # CONTACT
                'Nom Contact',
                'Fonction',
                'Localisation',

                # SOURCE 1: APOLLO APIFY
                'Email Apollo',
                'Conf. Apollo',
                'Tel Apollo',
                'LinkedIn Apollo',

                # SOURCE 2: DROPCONTACT
                'Email Dropcontact',
                'Conf. Dropcontact',
                'Tel Dropcontact',

                # SOURCE 3: EMAIL FINDER (construction)
                'Email Construit',
                'Pattern',
                'Conf. Construit',

                # SOURCE 4: GPT SCRAPING (intelligent)
                'Email GPT',
                'Conf. GPT',
                'Tel GPT',
                'Notes GPT',

                # METADATA
                'Source Principale',  # apollo, dropcontact, constructed, gpt
                'Email Meilleur',  # Email avec la meilleure confiance
                'Conf. Meilleure',  # Confiance du meilleur email
                'Toutes Sources',  # Liste de toutes les sources utilisées
                'Date Ajout',
            ]

            worksheet.update('A1:X1', [headers])
            print("✅ Onglet 'People' créé")

    def scrape_companies(self, search_query: str, max_results: int = 50,
                        location: str = None) -> List[Dict]:
        """
        ÉTAPE 1: Scraper les entreprises depuis Google Maps

        Args:
            search_query: Recherche (ex: "fabricants de vérandas")
            max_results: Nombre max d'entreprises
            location: Localisation optionnelle

        Returns:
            Liste d'entreprises enrichies
        """
        print("\n" + "="*70)
        print("📍 ÉTAPE 1: SCRAPING ENTREPRISES")
        print("="*70)
        print(f"Recherche: {search_query}")
        print(f"Max résultats: {max_results}")
        print("="*70 + "\n")

        # 1. Scraper Google Maps
        print("🗺️  Scraping Google Maps via Apify...")
        run_input = {
            'searchStringsArray': [search_query],
            'maxCrawledPlacesPerSearch': max_results,
            'language': 'fr',
        }

        if location:
            run_input['locationQuery'] = location

        try:
            run = self.apify_client.actor('compass/crawler-google-places').call(run_input=run_input)
            raw_results = list(self.apify_client.dataset(run['defaultDatasetId']).iterate_items())
            print(f"✅ {len(raw_results)} entreprises trouvées sur Google Maps")
        except Exception as e:
            print(f"❌ Erreur scraping Google Maps: {e}")
            return []

        # 2. Filtrer avec la blacklist
        print(f"\n🚫 Filtrage blacklist...")
        before = len(raw_results)
        filtered_results = self.blacklist.filter_companies(raw_results, name_key='title')
        print(f"✅ {len(filtered_results)} entreprises après filtrage (- {before - len(filtered_results)})")

        # 3. Enrichir chaque entreprise
        print(f"\n💎 Enrichissement des données entreprises...")
        enriched_companies = []

        for i, result in enumerate(filtered_results, 1):
            company_name = result.get('title', '')
            print(f"\n[{i}/{len(filtered_results)}] {company_name[:50]}...")

            # Extraire données de base
            base_data = {
                'name': company_name,
                'address': result.get('address', ''),
                'city': result.get('city', ''),
                'phone': result.get('phone', ''),
                'website': result.get('website', ''),
                'rating': result.get('totalScore', ''),
                'reviews_count': result.get('reviewsCount', ''),
                'category': result.get('categoryName', ''),
                'google_maps_url': result.get('url', ''),
                'date_added': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'status': 'nouveau',
                'contacts_found': 0,
            }

            # Enrichir avec API entreprise.data.gouv.fr
            try:
                api_data = self.enricher.enrich_with_api(
                    company_name,
                    base_data['website'],
                    base_data['address']
                )

                base_data['siret'] = api_data.get('siret', '')
                base_data['siren'] = api_data.get('siren', '')
                base_data['legal_form'] = api_data.get('legal_form', '')
                base_data['employees'] = api_data.get('employees', '')
                base_data['revenue'] = api_data.get('revenue', '')
                base_data['creation_date'] = api_data.get('creation_date', '')

            except Exception as e:
                print(f"  ⚠️  Erreur enrichissement: {e}")

            enriched_companies.append(base_data)

        # 4. Sauvegarder dans l'onglet Entreprises
        print(f"\n💾 Sauvegarde dans Google Sheets (onglet Entreprises)...")
        self._save_companies_to_sheet(enriched_companies)

        print(f"\n✅ ÉTAPE 1 TERMINÉE: {len(enriched_companies)} entreprises enregistrées")

        return enriched_companies

    def scrape_people(self, job_titles: List[str] = None, max_contacts_per_company: int = 3) -> List[Dict]:
        """
        ÉTAPE 2: Scraper les contacts pour les entreprises de l'onglet

        Args:
            job_titles: Titres de poste à cibler
            max_contacts_per_company: Nombre max de contacts par entreprise

        Returns:
            Liste de contacts avec colonnes séparées par source
        """
        print("\n" + "="*70)
        print("👥 ÉTAPE 2: SCRAPING CONTACTS")
        print("="*70)
        print(f"Job titles: {job_titles or ['CEO', 'Founder', 'Director']}")
        print(f"Max contacts/entreprise: {max_contacts_per_company}")
        print("="*70 + "\n")

        # 1. Lire les entreprises depuis l'onglet
        print("📖 Lecture des entreprises depuis Google Sheets...")
        companies = self._read_companies_from_sheet()
        print(f"✅ {len(companies)} entreprise(s) à traiter")

        if not companies:
            print("❌ Aucune entreprise trouvée. Lancez d'abord scrape_companies()")
            return []

        # 2. Pour chaque entreprise, chercher des contacts
        all_contacts = []

        for i, company in enumerate(companies, 1):
            company_name = company.get('name', '')
            company_domain = self._extract_domain(company.get('website', ''))

            print(f"\n[{i}/{len(companies)}] 🔍 Recherche contacts pour: {company_name[:50]}...")

            # Source 1: Apollo Apify (PRIORITAIRE)
            apollo_contacts = self._search_apollo(
                company_name,
                company_domain,
                job_titles or ['CEO', 'Founder', 'Managing Director'],
                max_contacts_per_company
            )

            # Source 2: Dropcontact (si Apollo ne trouve rien)
            dropcontact_contacts = []
            if not apollo_contacts and self.enricher.dropcontact:
                dropcontact_contacts = self._search_dropcontact(company_name, company_domain, company.get('siret'))

            # Source 3: Email Finder (construction d'emails)
            constructed_emails = self._construct_emails(company_name, company_domain)

            # Source 4: GPT Scraping (intelligent website scraping)
            gpt_contacts = self._search_gpt(company.get('website'), company_name)

            # Fusionner toutes les sources
            contacts = self._merge_contact_sources(
                company_name,
                company_domain,
                apollo_contacts,
                dropcontact_contacts,
                constructed_emails,
                gpt_contacts
            )

            all_contacts.extend(contacts)
            print(f"  ✅ Trouvé {len(contacts)} contact(s)")

            # Mettre à jour le compteur dans l'onglet Entreprises
            self._update_company_contacts_count(company_name, len(contacts))

        # 3. Sauvegarder dans l'onglet People
        print(f"\n💾 Sauvegarde de {len(all_contacts)} contact(s) dans Google Sheets (onglet People)...")
        self._save_people_to_sheet(all_contacts)

        print(f"\n✅ ÉTAPE 2 TERMINÉE: {len(all_contacts)} contacts enregistrés")

        return all_contacts

    def _search_apollo(self, company_name: str, company_domain: str,
                      job_titles: List[str], max_contacts: int) -> List[Dict]:
        """Recherche via Apollo Apify"""
        try:
            return self.apollo_scraper.search_people(
                company_name=company_name,
                company_domain=company_domain,
                job_titles=job_titles,
                max_results=max_contacts
            )
        except Exception as e:
            print(f"  ⚠️  Erreur Apollo: {e}")
            return []

    def _search_dropcontact(self, company_name: str, domain: str, siret: str) -> List[Dict]:
        """Recherche via Dropcontact"""
        # TODO: Implémenter
        return []

    def _construct_emails(self, company_name: str, domain: str) -> List[Dict]:
        """Construction d'emails avec EmailFinder"""
        # TODO: Implémenter
        return []

    def _search_gpt(self, website: str, company_name: str) -> List[Dict]:
        """Recherche via GPT Scraping (intelligent)"""
        try:
            return self.gpt_scraper.scrape_website_contacts(website, company_name)
        except Exception as e:
            print(f"  ⚠️  Erreur GPT: {e}")
            return []

    def _merge_contact_sources(self, company_name: str, company_domain: str,
                               apollo: List[Dict], dropcontact: List[Dict],
                               constructed: List[Dict], gpt_contacts: List[Dict]) -> List[Dict]:
        """Fusionne les contacts de toutes les sources avec colonnes séparées"""
        merged = []

        # Fusionner intelligemment toutes les sources
        # Stratégie: créer un contact par personne unique trouvée

        # D'abord, traiter les contacts Apollo (source prioritaire)
        for contact in apollo:
            merged_contact = {
                'company_name': company_name,
                'company_domain': company_domain,
                'contact_name': contact.get('name', ''),
                'position': contact.get('title', ''),
                'location': contact.get('location', ''),

                # Apollo
                'email_apollo': contact.get('email', ''),
                'conf_apollo': 'high' if contact.get('email_status') == 'verified' else 'medium',
                'phone_apollo': contact.get('phone', ''),
                'linkedin_apollo': contact.get('linkedin_url', ''),

                # Autres sources (vides pour Apollo)
                'email_dropcontact': '',
                'conf_dropcontact': '',
                'phone_dropcontact': '',
                'email_constructed': '',
                'pattern': '',
                'conf_constructed': '',
                'email_gpt': '',
                'conf_gpt': '',
                'phone_gpt': '',
                'notes_gpt': '',

                # Métadonnées
                'source_principale': 'apollo',
                'best_email': contact.get('email', ''),
                'best_conf': 'high' if contact.get('email_status') == 'verified' else 'medium',
                'all_sources': 'apollo',
                'date_added': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            }
            merged.append(merged_contact)

        # Ensuite, traiter les contacts GPT
        for contact in gpt_contacts:
            merged_contact = {
                'company_name': company_name,
                'company_domain': company_domain,
                'contact_name': contact.get('name', ''),
                'position': contact.get('position', ''),
                'location': '',

                # Apollo (vide)
                'email_apollo': '',
                'conf_apollo': '',
                'phone_apollo': '',
                'linkedin_apollo': '',

                # Dropcontact (vide)
                'email_dropcontact': '',
                'conf_dropcontact': '',
                'phone_dropcontact': '',

                # Email Finder (vide)
                'email_constructed': '',
                'pattern': '',
                'conf_constructed': '',

                # GPT
                'email_gpt': contact.get('email', ''),
                'conf_gpt': contact.get('confidence', 'medium'),
                'phone_gpt': contact.get('phone', ''),
                'notes_gpt': contact.get('notes', ''),

                # Métadonnées
                'source_principale': 'gpt',
                'best_email': contact.get('email', ''),
                'best_conf': contact.get('confidence', 'medium'),
                'all_sources': 'gpt',
                'date_added': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            }
            merged.append(merged_contact)

        # TODO: Implémenter la fusion Dropcontact et EmailFinder quand ces méthodes seront finalisées

        return merged

    def _extract_domain(self, website: str) -> str:
        """Extrait le domaine d'une URL"""
        if not website:
            return ""
        from urllib.parse import urlparse
        try:
            parsed = urlparse(website if website.startswith('http') else f'https://{website}')
            return parsed.netloc.replace('www.', '')
        except:
            return ""

    def _save_companies_to_sheet(self, companies: List[Dict]):
        """Sauvegarde les entreprises dans l'onglet"""
        try:
            worksheet = self.google_sheet.worksheet('Entreprises')

            rows = []
            for company in companies:
                row = [
                    company.get('name', ''),
                    company.get('address', ''),
                    company.get('city', ''),
                    company.get('phone', ''),
                    company.get('website', ''),
                    company.get('rating', ''),
                    company.get('reviews_count', ''),
                    company.get('category', ''),
                    company.get('google_maps_url', ''),
                    company.get('siret', ''),
                    company.get('siren', ''),
                    company.get('legal_form', ''),
                    company.get('employees', ''),
                    company.get('revenue', ''),
                    company.get('creation_date', ''),
                    company.get('date_added', ''),
                    company.get('status', ''),
                    company.get('contacts_found', ''),
                ]
                rows.append(row)

            if rows:
                worksheet.append_rows(rows)
                print(f"✅ {len(rows)} entreprise(s) sauvegardée(s)")

        except Exception as e:
            print(f"❌ Erreur sauvegarde entreprises: {e}")

    def _save_people_to_sheet(self, contacts: List[Dict]):
        """Sauvegarde les contacts dans l'onglet"""
        try:
            worksheet = self.google_sheet.worksheet('People')

            rows = []
            for contact in contacts:
                row = [
                    contact.get('company_name', ''),
                    contact.get('company_domain', ''),
                    contact.get('contact_name', ''),
                    contact.get('position', ''),
                    contact.get('location', ''),
                    contact.get('email_apollo', ''),
                    contact.get('conf_apollo', ''),
                    contact.get('phone_apollo', ''),
                    contact.get('linkedin_apollo', ''),
                    contact.get('email_dropcontact', ''),
                    contact.get('conf_dropcontact', ''),
                    contact.get('phone_dropcontact', ''),
                    contact.get('email_constructed', ''),
                    contact.get('pattern', ''),
                    contact.get('conf_constructed', ''),
                    contact.get('email_gpt', ''),
                    contact.get('conf_gpt', ''),
                    contact.get('phone_gpt', ''),
                    contact.get('notes_gpt', ''),
                    contact.get('source_principale', ''),
                    contact.get('best_email', ''),
                    contact.get('best_conf', ''),
                    contact.get('all_sources', ''),
                    contact.get('date_added', ''),
                ]
                rows.append(row)

            if rows:
                worksheet.append_rows(rows)
                print(f"✅ {len(rows)} contact(s) sauvegardé(s)")

        except Exception as e:
            print(f"❌ Erreur sauvegarde contacts: {e}")

    def _read_companies_from_sheet(self) -> List[Dict]:
        """Lit les entreprises depuis l'onglet"""
        try:
            worksheet = self.google_sheet.worksheet('Entreprises')
            rows = worksheet.get_all_values()[1:]  # Skip header

            companies = []
            for row in rows:
                if len(row) >= 10:  # Au moins les colonnes de base
                    companies.append({
                        'name': row[0],
                        'address': row[1],
                        'city': row[2],
                        'phone': row[3],
                        'website': row[4],
                        'rating': row[5],
                        'reviews_count': row[6],
                        'category': row[7],
                        'google_maps_url': row[8],
                        'siret': row[9] if len(row) > 9 else '',
                    })

            return companies

        except Exception as e:
            print(f"❌ Erreur lecture entreprises: {e}")
            return []

    def _update_company_contacts_count(self, company_name: str, count: int):
        """Met à jour le nombre de contacts trouvés pour une entreprise"""
        # TODO: Implémenter
        pass


if __name__ == "__main__":
    # Test du scraper
    scraper = TwoStepScraper()

    # ÉTAPE 1: Scraper entreprises
    companies = scraper.scrape_companies(
        search_query="fabricants de vérandas à Paris",
        max_results=10
    )

    # ÉTAPE 2: Scraper contacts
    if companies:
        contacts = scraper.scrape_people(
            job_titles=["CEO", "Gérant", "Directeur Commercial"],
            max_contacts_per_company=3
        )
