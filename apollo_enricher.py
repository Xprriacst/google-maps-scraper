#!/usr/bin/env python3
"""
Module d'enrichissement avec Apollo.io
Meilleure base de données B2B que l'API française
"""

import requests
import time
from typing import Dict, List, Optional
from utils import get_env


class ApolloEnricher:
    """
    Enrichit les données d'entreprises et contacts via Apollo.io

    Apollo.io offre :
    - 70M+ entreprises dans sa base
    - Données firmographiques précises (effectifs, revenue, secteur)
    - Contacts décisionnaires avec emails vérifiés
    - Meilleure couverture internationale
    """

    def __init__(self, api_key: str = None):
        """
        Initialise l'enrichisseur Apollo

        Args:
            api_key: Clé API Apollo (si None, charge depuis env)
        """
        self.api_key = api_key or get_env('APOLLO_API_KEY')

        if not self.api_key:
            raise ValueError("APOLLO_API_KEY non configurée")

        self.base_url = "https://api.apollo.io/v1"
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json',
            'Cache-Control': 'no-cache'
        })

        # Statistiques
        self.stats = {
            'requests': 0,
            'success': 0,
            'no_data': 0,
            'errors': 0
        }

    def enrich_organization(self, company_name: str, website: str = None) -> Dict:
        """
        Enrichit les données d'une entreprise via Apollo

        Args:
            company_name: Nom de l'entreprise
            website: Site web (optionnel mais recommandé)

        Returns:
            Dict avec données enrichies de l'entreprise
        """
        print(f"  🚀 Apollo: Enrichissement entreprise {company_name[:40]}...")

        result = {
            'company_name': '',
            'website': '',
            'industry': '',
            'employees': '',
            'revenue': '',
            'founded_year': '',
            'linkedin_url': '',
            'twitter_url': '',
            'facebook_url': '',
            'phone': '',
            'country': '',
            'city': '',
            'state': '',
            'data_sources': []
        }

        try:
            self.stats['requests'] += 1

            # Construire la requête
            payload = {
                'api_key': self.api_key,
            }

            # Rechercher par domaine (plus précis) ou par nom
            if website:
                # Extraire le domaine
                domain = website.replace('http://', '').replace('https://', '').replace('www.', '').split('/')[0]
                payload['domain'] = domain
            else:
                payload['organization_name'] = company_name

            # Appeler l'API Organization Enrichment
            response = self.session.post(
                f"{self.base_url}/organizations/enrich",
                json=payload,
                timeout=30
            )

            if response.status_code != 200:
                print(f"  ⚠️  Apollo API error: {response.status_code}")
                self.stats['errors'] += 1
                return result

            data = response.json()
            org = data.get('organization', {})

            if not org:
                print(f"  ❌ Aucune donnée Apollo trouvée")
                self.stats['no_data'] += 1
                return result

            # Extraire les données
            result['company_name'] = org.get('name', '')
            result['website'] = org.get('website_url', '')
            result['industry'] = org.get('industry', '')
            result['employees'] = org.get('estimated_num_employees', '')
            result['revenue'] = org.get('annual_revenue', '')
            result['founded_year'] = org.get('founded_year', '')
            result['linkedin_url'] = org.get('linkedin_url', '')
            result['twitter_url'] = org.get('twitter_url', '')
            result['facebook_url'] = org.get('facebook_url', '')
            result['phone'] = org.get('phone', '')
            result['country'] = org.get('country', '')
            result['city'] = org.get('city', '')
            result['state'] = org.get('state', '')
            result['data_sources'].append('apollo')

            print(f"  ✅ Données Apollo récupérées:")
            print(f"     Effectifs: {result['employees']}")
            print(f"     Secteur: {result['industry']}")
            print(f"     Revenue: {result['revenue']}")

            self.stats['success'] += 1
            return result

        except requests.exceptions.Timeout:
            print(f"  ⚠️  Timeout Apollo API")
            self.stats['errors'] += 1
            return result
        except Exception as e:
            print(f"  ⚠️  Erreur Apollo: {e}")
            self.stats['errors'] += 1
            return result

    def search_people(self, company_name: str, website: str = None,
                     job_titles: List[str] = None, max_contacts: int = 3) -> List[Dict]:
        """
        Recherche des contacts dans une entreprise via Apollo

        Args:
            company_name: Nom de l'entreprise
            website: Site web de l'entreprise
            job_titles: Liste de titres recherchés (ex: ["CEO", "Sales Director"])
            max_contacts: Nombre maximum de contacts à retourner

        Returns:
            Liste des contacts trouvés
        """
        print(f"  👥 Apollo: Recherche contacts pour {company_name[:40]}...")

        contacts = []

        try:
            self.stats['requests'] += 1

            # Construire la requête de recherche
            payload = {
                'api_key': self.api_key,
                'page': 1,
                'per_page': max_contacts,
                'organization_names': [company_name]
            }

            # Ajouter les titres si spécifiés
            if job_titles:
                payload['person_titles'] = job_titles

            # Rechercher les personnes
            response = self.session.post(
                f"{self.base_url}/mixed_people/search",
                json=payload,
                timeout=30
            )

            if response.status_code != 200:
                print(f"  ⚠️  Apollo People API error: {response.status_code}")
                self.stats['errors'] += 1
                return contacts

            data = response.json()
            people = data.get('people', [])

            if not people:
                print(f"  ❌ Aucun contact trouvé par Apollo")
                self.stats['no_data'] += 1
                return contacts

            # Extraire les contacts
            for person in people[:max_contacts]:
                contact = {
                    'name': f"{person.get('first_name', '')} {person.get('last_name', '')}".strip(),
                    'first_name': person.get('first_name', ''),
                    'last_name': person.get('last_name', ''),
                    'title': person.get('title', ''),
                    'email': person.get('email', ''),
                    'email_status': person.get('email_status', ''),
                    'phone': person.get('phone_numbers', [{}])[0].get('raw_number', '') if person.get('phone_numbers') else '',
                    'linkedin_url': person.get('linkedin_url', ''),
                    'seniority': person.get('seniority', ''),
                    'departments': person.get('departments', [])
                }
                contacts.append(contact)

            print(f"  ✅ {len(contacts)} contact(s) trouvé(s) par Apollo")
            for i, c in enumerate(contacts, 1):
                print(f"     {i}. {c['name']} ({c['title']}) - {c['email']}")

            self.stats['success'] += 1

        except requests.exceptions.Timeout:
            print(f"  ⚠️  Timeout Apollo People API")
            self.stats['errors'] += 1
        except Exception as e:
            print(f"  ⚠️  Erreur Apollo People: {e}")
            self.stats['errors'] += 1

        return contacts

    def get_stats(self) -> Dict:
        """Retourne les statistiques d'utilisation"""
        return self.stats.copy()


if __name__ == "__main__":
    # Test du module
    print("🧪 Test Apollo Enricher")
    print("=" * 60)

    try:
        enricher = ApolloEnricher()

        # Test enrichissement entreprise
        org_data = enricher.enrich_organization(
            "Salesforce",
            "https://www.salesforce.com"
        )
        print("\n📊 Données entreprise:")
        print(org_data)

        # Test recherche contacts
        contacts = enricher.search_people(
            "Salesforce",
            job_titles=["CEO", "CTO", "VP Sales"]
        )
        print("\n👥 Contacts:")
        for contact in contacts:
            print(f"  - {contact['name']} ({contact['title']})")

        print("\n📈 Statistiques:")
        print(enricher.get_stats())

    except Exception as e:
        print(f"❌ Erreur: {e}")
