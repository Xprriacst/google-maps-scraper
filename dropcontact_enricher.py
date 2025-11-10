#!/usr/bin/env python3
"""
Module d'enrichissement de contacts via l'API Dropcontact
Trouve les décideurs commerciaux avec emails vérifiés
"""

import requests
import time
from typing import Dict, List, Optional
from utils import get_env


class DropcontactEnricher:
    """Enrichit les contacts d'entreprises via l'API Dropcontact"""

    # Titres de décideurs recherchés (par ordre de priorité)
    DECISION_MAKER_ROLES = [
        'Sales Director',
        'Commercial Director',
        'CEO',
        'Managing Director',
        'General Manager',
        'Business Development Director',
        'Marketing Director',
        'Founder',
        'President',
        'Owner'
    ]

    # Niveaux de séniorité recherchés
    SENIORITY_LEVELS = [
        'executive',  # C-level, VP, Director
        'senior',     # Senior Manager, Senior
        'manager'     # Manager
    ]

    def __init__(self, api_key: str = None):
        """
        Initialise l'enrichisseur Dropcontact

        Args:
            api_key: Clé API Dropcontact (si None, charge depuis env)
        """
        self.api_key = api_key or get_env('DROPCONTACT_API_KEY')

        if not self.api_key:
            raise ValueError("DROPCONTACT_API_KEY non configurée")

        self.base_url = "https://api.dropcontact.io"
        self.session = requests.Session()
        self.session.headers.update({
            'X-Access-Token': self.api_key,
            'Content-Type': 'application/json'
        })

        # Statistiques d'utilisation
        self.stats = {
            'requests': 0,
            'success': 0,
            'no_contact': 0,
            'errors': 0
        }

    def enrich_contact(self, company_name: str, website: str = None,
                       company_siret: str = None, find_role: str = None) -> Dict:
        """
        Enrichit un contact d'entreprise via Dropcontact

        Args:
            company_name: Nom de l'entreprise
            website: Site web de l'entreprise
            company_siret: SIRET de l'entreprise (optionnel, améliore la précision)
            find_role: Rôle spécifique recherché (ex: "Sales Director")

        Returns:
            Dict avec les données enrichies du contact décideur
        """
        print(f"  🔍 Dropcontact: Recherche décideur pour {company_name[:40]}...")

        # Préparer la requête
        data = {
            'data': [{
                'company': company_name,
                'website': website,
                'siret': company_siret,
            }],
            'siren': True,  # Demander le SIREN
            'language': 'fr'  # Priorité aux contacts francophones
        }

        # Filtrer par rôle si spécifié
        if find_role:
            data['search_role'] = find_role

        try:
            self.stats['requests'] += 1

            # Envoi de la requête d'enrichissement
            response = self.session.post(
                f"{self.base_url}/batch",
                json=data,
                timeout=30
            )

            if response.status_code != 200:
                print(f"  ⚠️  Dropcontact API error: {response.status_code}")
                self.stats['errors'] += 1
                return self._empty_result()

            result = response.json()
            request_id = result.get('request_id')

            if not request_id:
                print(f"  ⚠️  Pas de request_id reçu")
                self.stats['errors'] += 1
                return self._empty_result()

            # Attendre que l'enrichissement soit terminé
            enriched_data = self._wait_for_result(request_id)

            if not enriched_data:
                print(f"  ❌ Aucun contact trouvé par Dropcontact")
                self.stats['no_contact'] += 1
                return self._empty_result()

            # Extraire le meilleur décideur
            contact = self._extract_best_contact(enriched_data)

            if contact['contact_name']:
                print(f"  ✅ Contact trouvé: {contact['contact_name']} ({contact['contact_position']})")
                print(f"     Email: {contact['contact_email']} (vérifié)")
                self.stats['success'] += 1
            else:
                print(f"  ❌ Aucun contact décideur trouvé")
                self.stats['no_contact'] += 1

            return contact

        except requests.exceptions.Timeout:
            print(f"  ⚠️  Timeout Dropcontact API")
            self.stats['errors'] += 1
            return self._empty_result()

        except Exception as e:
            print(f"  ⚠️  Erreur Dropcontact: {e}")
            self.stats['errors'] += 1
            return self._empty_result()

    def _wait_for_result(self, request_id: str, max_wait: int = 60) -> Optional[Dict]:
        """
        Attend que l'enrichissement soit terminé

        Args:
            request_id: ID de la requête
            max_wait: Temps d'attente maximum en secondes

        Returns:
            Données enrichies ou None
        """
        start_time = time.time()

        while (time.time() - start_time) < max_wait:
            try:
                response = self.session.get(
                    f"{self.base_url}/batch/{request_id}",
                    timeout=10
                )

                if response.status_code != 200:
                    return None

                result = response.json()

                # Vérifier si le traitement est terminé
                if result.get('success') and result.get('data'):
                    return result['data'][0] if result['data'] else None

                # Attendre avant de réessayer
                time.sleep(2)

            except Exception as e:
                print(f"  ⚠️  Erreur lors de la récupération: {e}")
                return None

        print(f"  ⚠️  Timeout lors de l'attente du résultat")
        return None

    def _extract_best_contact(self, data: Dict) -> Dict:
        """
        Extrait le meilleur contact décideur des résultats Dropcontact

        Args:
            data: Données enrichies de Dropcontact

        Returns:
            Dict avec les infos du meilleur contact
        """
        result = {
            'contact_name': '',
            'contact_position': '',
            'contact_email': '',
            'contact_phone': '',
            'contact_linkedin': '',
            'email_confidence': 'none',
            'data_sources': []
        }

        # Extraire les contacts trouvés
        contacts = data.get('contacts', [])

        if not contacts:
            return result

        # Filtrer et scorer les contacts par pertinence
        scored_contacts = []

        for contact in contacts:
            score = 0
            email = contact.get('email', '')
            job_title = contact.get('job', '') or contact.get('job_title', '') or ''

            # Ignorer si pas d'email
            if not email or '@' not in email:
                continue

            # Score basé sur le poste
            job_lower = job_title.lower()

            for idx, role in enumerate(self.DECISION_MAKER_ROLES):
                if role.lower() in job_lower:
                    score += (len(self.DECISION_MAKER_ROLES) - idx) * 10
                    break

            # Score basé sur les mots-clés
            if any(word in job_lower for word in ['director', 'directeur', 'ceo', 'gérant', 'president']):
                score += 50
            if any(word in job_lower for word in ['commercial', 'sales', 'business development']):
                score += 30
            if any(word in job_lower for word in ['marketing', 'développement']):
                score += 20

            # Score basé sur la vérification de l'email
            email_quality = contact.get('email_status', '')
            if email_quality in ['valid', 'verified', 'deliverable']:
                score += 30

            # Séniorité
            seniority = (contact.get('seniority', '') or '').lower()
            if 'executive' in seniority or 'c-level' in seniority:
                score += 40
            elif 'senior' in seniority or 'director' in seniority:
                score += 25
            elif 'manager' in seniority:
                score += 15

            scored_contacts.append({
                'contact': contact,
                'score': score
            })

        # Trier par score décroissant
        scored_contacts.sort(key=lambda x: x['score'], reverse=True)

        # Prendre le meilleur contact
        if scored_contacts and scored_contacts[0]['score'] > 0:
            best = scored_contacts[0]['contact']

            # Construire le nom complet
            first_name = best.get('first_name', '')
            last_name = best.get('last_name', '')
            full_name = f"{first_name} {last_name}".strip()

            result['contact_name'] = full_name or best.get('full_name', '')
            result['contact_position'] = best.get('job', '') or best.get('job_title', '')
            result['contact_email'] = best.get('email', '')
            result['contact_phone'] = best.get('phone', '') or best.get('mobile_phone', '')
            result['contact_linkedin'] = best.get('linkedin', '')

            # Confiance basée sur la vérification email
            email_status = best.get('email_status', '').lower()
            if email_status in ['valid', 'verified', 'deliverable']:
                result['email_confidence'] = 'high'
            elif email_status == 'risky':
                result['email_confidence'] = 'medium'
            else:
                result['email_confidence'] = 'low'

            result['data_sources'].append('dropcontact')

        return result

    def _empty_result(self) -> Dict:
        """Retourne un résultat vide"""
        return {
            'contact_name': '',
            'contact_position': '',
            'contact_email': '',
            'contact_phone': '',
            'contact_linkedin': '',
            'email_confidence': 'none',
            'data_sources': []
        }

    def enrich_batch(self, companies: List[Dict], batch_size: int = 25) -> List[Dict]:
        """
        Enrichit plusieurs entreprises en batch (plus efficace)

        Args:
            companies: Liste de dicts avec 'name', 'website', 'siret'
            batch_size: Taille des batchs (max 100 pour Dropcontact)

        Returns:
            Liste des contacts enrichis
        """
        results = []

        # Traiter par batchs
        for i in range(0, len(companies), batch_size):
            batch = companies[i:i + batch_size]
            print(f"  🔄 Batch {i//batch_size + 1}/{(len(companies)-1)//batch_size + 1} ({len(batch)} entreprises)...")

            # Préparer les données du batch
            data = {
                'data': [
                    {
                        'company': c.get('name', ''),
                        'website': c.get('website', ''),
                        'siret': c.get('siret', '')
                    }
                    for c in batch
                ],
                'siren': True,
                'language': 'fr'
            }

            try:
                # Envoyer le batch
                response = self.session.post(
                    f"{self.base_url}/batch",
                    json=data,
                    timeout=30
                )

                if response.status_code != 200:
                    print(f"  ⚠️  Erreur batch: {response.status_code}")
                    results.extend([self._empty_result() for _ in batch])
                    continue

                result = response.json()
                request_id = result.get('request_id')

                # Attendre les résultats
                enriched_batch = self._wait_for_batch_result(request_id)

                if enriched_batch:
                    for data in enriched_batch:
                        contact = self._extract_best_contact(data)
                        results.append(contact)
                else:
                    results.extend([self._empty_result() for _ in batch])

            except Exception as e:
                print(f"  ⚠️  Erreur batch: {e}")
                results.extend([self._empty_result() for _ in batch])

            # Pause entre les batchs pour éviter rate limiting
            time.sleep(1)

        return results

    def _wait_for_batch_result(self, request_id: str, max_wait: int = 120) -> Optional[List[Dict]]:
        """Attend les résultats d'un batch"""
        start_time = time.time()

        while (time.time() - start_time) < max_wait:
            try:
                response = self.session.get(
                    f"{self.base_url}/batch/{request_id}",
                    timeout=10
                )

                if response.status_code != 200:
                    return None

                result = response.json()

                if result.get('success') and result.get('data'):
                    return result['data']

                time.sleep(3)

            except Exception:
                return None

        return None

    def get_stats(self) -> Dict:
        """Retourne les statistiques d'utilisation"""
        success_rate = (self.stats['success'] / self.stats['requests'] * 100) if self.stats['requests'] > 0 else 0

        return {
            'total_requests': self.stats['requests'],
            'success': self.stats['success'],
            'no_contact': self.stats['no_contact'],
            'errors': self.stats['errors'],
            'success_rate': f"{success_rate:.1f}%"
        }


if __name__ == "__main__":
    # Test du module
    print("=== Test Dropcontact Enricher ===\n")

    try:
        enricher = DropcontactEnricher()

        # Test 1: Enrichir une entreprise
        print("Test 1: Entreprise française")
        result = enricher.enrich_contact(
            company_name="Dropcontact",
            website="https://www.dropcontact.com"
        )

        print(f"\nRésultat:")
        print(f"  Nom: {result['contact_name']}")
        print(f"  Poste: {result['contact_position']}")
        print(f"  Email: {result['contact_email']}")
        print(f"  Confiance: {result['email_confidence']}")

        print(f"\n📊 Statistiques:")
        stats = enricher.get_stats()
        for key, value in stats.items():
            print(f"  {key}: {value}")

    except ValueError as e:
        print(f"⚠️  Configuration manquante: {e}")
        print(f"💡 Ajoutez DROPCONTACT_API_KEY dans votre .env")
