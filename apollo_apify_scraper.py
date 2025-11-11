#!/usr/bin/env python3
"""
Apollo Apify Scraper - Utilise Apify pour scraper Apollo.io
Permet de trouver des contacts B2B sans consommer les crédits Apollo
"""

import time
from typing import List, Dict, Optional
from apify_client import ApifyClient
from utils import get_env


class ApolloApifyScraper:
    """Scraper Apollo.io via Apify pour obtenir des contacts B2B"""

    # Acteurs Apify disponibles pour Apollo (par ordre de préférence)
    APOLLO_ACTORS = [
        'curious_coder/apollo-io-scraper',
        'datavoyantlab/apollo-scraper',
        'supreme_coder/apollo-scraper',
    ]

    def __init__(self, apify_token: str = None, actor_id: str = None):
        """
        Initialise le scraper Apollo via Apify

        Args:
            apify_token: Token API Apify (si None, utilise get_env)
            actor_id: ID de l'acteur Apify à utiliser (si None, utilise le premier disponible)
        """
        self.apify_token = apify_token or get_env('APIFY_API_TOKEN')
        if not self.apify_token:
            raise ValueError("APIFY_API_TOKEN requis")

        self.client = ApifyClient(self.apify_token)
        self.actor_id = actor_id or self.APOLLO_ACTORS[0]

        print(f"✅ Apollo Apify Scraper initialisé avec l'acteur: {self.actor_id}")

    def search_people(self, company_name: str = None, company_domain: str = None,
                     job_titles: List[str] = None, location: str = None,
                     max_results: int = 10) -> List[Dict]:
        """
        Recherche des contacts via Apollo.io

        Args:
            company_name: Nom de l'entreprise
            company_domain: Domaine de l'entreprise (ex: example.com)
            job_titles: Liste de titres de poste à cibler
            location: Localisation (ex: "France", "Paris")
            max_results: Nombre maximum de résultats

        Returns:
            Liste de contacts avec emails, téléphones, LinkedIn
        """
        print(f"\n🔍 Recherche Apollo Apify: {company_name or company_domain}")

        # Configuration de la recherche Apollo
        run_input = {
            "maxResults": max_results,
            "personTitles": job_titles or ["CEO", "Founder", "Director"],
        }

        # Ajouter les filtres d'entreprise
        if company_name:
            run_input["companyName"] = company_name
        if company_domain:
            run_input["companyDomain"] = company_domain
        if location:
            run_input["location"] = location

        try:
            # Lancer l'acteur Apify
            print(f"  🚀 Lancement de l'acteur {self.actor_id}...")
            run = self.client.actor(self.actor_id).call(run_input=run_input)

            # Récupérer les résultats
            results = []
            for item in self.client.dataset(run["defaultDatasetId"]).iterate_items():
                contact = {
                    'name': item.get('name', ''),
                    'title': item.get('title', ''),
                    'email': item.get('email', ''),
                    'phone': item.get('phone', ''),
                    'linkedin_url': item.get('linkedin_url', ''),
                    'company_name': item.get('organization_name', company_name),
                    'company_domain': item.get('organization_domain', company_domain),
                    'location': item.get('city', ''),
                    'email_status': item.get('email_status', ''),  # verified, guessed, etc.
                    'source': 'apollo_apify'
                }
                results.append(contact)

            print(f"  ✅ Trouvé {len(results)} contact(s) via Apollo Apify")
            return results

        except Exception as e:
            print(f"  ❌ Erreur Apollo Apify: {e}")
            return []

    def search_companies(self, search_query: str, location: str = None,
                        industry: str = None, max_results: int = 50) -> List[Dict]:
        """
        Recherche des entreprises via Apollo.io

        Args:
            search_query: Requête de recherche (ex: "SaaS companies")
            location: Localisation
            industry: Industrie
            max_results: Nombre maximum de résultats

        Returns:
            Liste d'entreprises
        """
        print(f"\n🏢 Recherche entreprises Apollo: {search_query}")

        run_input = {
            "searchQuery": search_query,
            "maxResults": max_results,
            "searchType": "organizations",  # Recherche d'entreprises
        }

        if location:
            run_input["location"] = location
        if industry:
            run_input["industry"] = industry

        try:
            run = self.client.actor(self.actor_id).call(run_input=run_input)

            companies = []
            for item in self.client.dataset(run["defaultDatasetId"]).iterate_items():
                company = {
                    'name': item.get('organization_name', ''),
                    'domain': item.get('organization_domain', ''),
                    'industry': item.get('industry', ''),
                    'employees': item.get('employee_count', ''),
                    'revenue': item.get('estimated_revenue', ''),
                    'location': item.get('city', ''),
                    'linkedin_url': item.get('linkedin_url', ''),
                    'phone': item.get('phone', ''),
                    'source': 'apollo_apify'
                }
                companies.append(company)

            print(f"  ✅ Trouvé {len(companies)} entreprise(s) via Apollo Apify")
            return companies

        except Exception as e:
            print(f"  ❌ Erreur Apollo Apify: {e}")
            return []


if __name__ == "__main__":
    # Test du scraper
    scraper = ApolloApifyScraper()

    # Test recherche de contacts
    print("\n" + "="*60)
    print("🧪 TEST: Recherche de contacts")
    print("="*60)

    contacts = scraper.search_people(
        company_name="Stripe",
        job_titles=["CEO", "CTO", "VP Engineering"],
        max_results=5
    )

    print(f"\n📊 Résultats: {len(contacts)} contact(s)")
    for contact in contacts:
        print(f"  - {contact['name']} ({contact['title']}) - {contact['email']}")
