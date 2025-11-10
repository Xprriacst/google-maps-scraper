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

    # Titres pour TPE/PME (0-250 employés) - Priorité au dirigeant
    ROLES_TPE_PME = [
        'CEO',
        'Managing Director',
        'General Manager',
        'Founder',
        'President',
        'Owner',
        'Gérant',
        'Directeur Général',
        'Sales Director',
        'Commercial Director'
    ]

    # Titres pour ETI/GE (250+ employés) - Priorité aux fonctions opérationnelles
    ROLES_ETI_GE = [
        'Sales Director',
        'Commercial Director',
        'Purchasing Director',
        'Procurement Director',
        'Business Development Director',
        'Head of Sales',
        'Head of Purchasing',
        'Directeur Commercial',
        'Directeur Achats',
        'Directeur Développement',
        'Marketing Director',
        'Head of Marketing'
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

    def _get_company_size_category(self, employees: int) -> str:
        """
        Détermine la catégorie de taille de l'entreprise

        Args:
            employees: Nombre d'employés

        Returns:
            Catégorie: 'TPE', 'PME', 'ETI', 'GE'
        """
        if employees <= 10:
            return 'TPE'
        elif employees <= 250:
            return 'PME'
        elif employees <= 5000:
            return 'ETI'
        else:
            return 'GE'

    def _get_target_roles(self, employees: int) -> List[str]:
        """
        Retourne les rôles à cibler selon la taille de l'entreprise

        Args:
            employees: Nombre d'employés

        Returns:
            Liste des rôles prioritaires
        """
        category = self._get_company_size_category(employees)

        if category in ['TPE', 'PME']:
            return self.ROLES_TPE_PME
        else:  # ETI ou GE
            return self.ROLES_ETI_GE

    def enrich_contact(self, company_name: str, website: str = None,
                       company_siret: str = None, employees: int = 0) -> Dict:
        """
        Enrichit un contact d'entreprise via Dropcontact
        Adapte automatiquement la recherche selon la taille de l'entreprise

        Args:
            company_name: Nom de l'entreprise
            website: Site web de l'entreprise
            company_siret: SIRET de l'entreprise (optionnel, améliore la précision)
            employees: Nombre d'employés (pour adapter les rôles recherchés)

        Returns:
            Dict avec les données enrichies du contact décideur
        """
        # Déterminer la catégorie et les rôles cibles
        category = self._get_company_size_category(employees) if employees > 0 else 'PME'
        target_roles = self._get_target_roles(employees) if employees > 0 else self.ROLES_TPE_PME

        # Message adapté selon la taille
        if category in ['TPE', 'PME']:
            print(f"  🔍 Dropcontact: Recherche dirigeant pour {company_name[:40]} ({category})...")
        else:
            print(f"  🔍 Dropcontact: Recherche contact opérationnel pour {company_name[:40]} ({category})...")

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

            # Extraire les 3 meilleurs décideurs avec les rôles ciblés
            contact = self._extract_best_contact(enriched_data, target_roles)

            # Compter combien de contacts ont été trouvés
            contacts_found = sum(1 for i in range(1, 4) if contact.get(f'contact_{i}_name', '').strip())

            if contacts_found > 0:
                print(f"  ✅ {contacts_found} contact(s) trouvé(s):")
                for i in range(1, contacts_found + 1):
                    name = contact.get(f'contact_{i}_name', '')
                    position = contact.get(f'contact_{i}_position', '')
                    email = contact.get(f'contact_{i}_email', '')
                    if name:
                        print(f"     {i}. {name} ({position}) - {email}")
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

    def _extract_best_contact(self, data: Dict, target_roles: List[str] = None) -> Dict:
        """
        Extrait les 3 meilleurs contacts décideurs des résultats Dropcontact

        Args:
            data: Données enrichies de Dropcontact
            target_roles: Liste des rôles à prioriser (par défaut: ROLES_TPE_PME)

        Returns:
            Dict avec les infos des 3 meilleurs contacts (+ compatibilité avec le contact principal)
        """
        if target_roles is None:
            target_roles = self.ROLES_TPE_PME
        result = {
            'contact_name': '',
            'contact_position': '',
            'contact_email': '',
            'contact_phone': '',
            'contact_linkedin': '',
            'email_confidence': 'none',
            # Contacts 1-3
            'contact_1_name': '',
            'contact_1_position': '',
            'contact_1_email': '',
            'contact_1_phone': '',
            'contact_1_linkedin': '',
            'contact_1_email_confidence': 'none',
            'contact_2_name': '',
            'contact_2_position': '',
            'contact_2_email': '',
            'contact_2_phone': '',
            'contact_2_linkedin': '',
            'contact_2_email_confidence': 'none',
            'contact_3_name': '',
            'contact_3_position': '',
            'contact_3_email': '',
            'contact_3_phone': '',
            'contact_3_linkedin': '',
            'contact_3_email_confidence': 'none',
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

            # Score basé sur le poste (utilise les rôles ciblés selon la taille)
            job_lower = job_title.lower()

            for idx, role in enumerate(target_roles):
                if role.lower() in job_lower:
                    score += (len(target_roles) - idx) * 10
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

        # Prendre les 3 meilleurs contacts
        result['data_sources'].append('dropcontact')

        for i in range(min(3, len(scored_contacts))):
            if scored_contacts[i]['score'] > 0:
                contact = scored_contacts[i]['contact']
                contact_num = i + 1

                # Construire le nom complet
                first_name = contact.get('first_name', '')
                last_name = contact.get('last_name', '')
                full_name = f"{first_name} {last_name}".strip()

                result[f'contact_{contact_num}_name'] = full_name or contact.get('full_name', '')
                result[f'contact_{contact_num}_position'] = contact.get('job', '') or contact.get('job_title', '')
                result[f'contact_{contact_num}_email'] = contact.get('email', '')
                result[f'contact_{contact_num}_phone'] = contact.get('phone', '') or contact.get('mobile_phone', '')
                result[f'contact_{contact_num}_linkedin'] = contact.get('linkedin', '')

                # Confiance basée sur la vérification email
                email_status = contact.get('email_status', '').lower()
                if email_status in ['valid', 'verified', 'deliverable']:
                    confidence = 'high'
                elif email_status == 'risky':
                    confidence = 'medium'
                else:
                    confidence = 'low'
                result[f'contact_{contact_num}_email_confidence'] = confidence

        # Garder la compatibilité : contact_name = contact_1_name
        if 'contact_1_name' in result:
            result['contact_name'] = result['contact_1_name']
            result['contact_position'] = result['contact_1_position']
            result['contact_email'] = result['contact_1_email']
            result['contact_phone'] = result['contact_1_phone']
            result['contact_linkedin'] = result['contact_1_linkedin']
            result['email_confidence'] = result['contact_1_email_confidence']


        return result

    def _empty_result(self) -> Dict:
        """Retourne un résultat vide avec tous les champs initialisés"""
        return {
            'contact_name': '',
            'contact_position': '',
            'contact_email': '',
            'contact_phone': '',
            'contact_linkedin': '',
            'email_confidence': 'none',
            # Contacts 1-3
            'contact_1_name': '',
            'contact_1_position': '',
            'contact_1_email': '',
            'contact_1_phone': '',
            'contact_1_linkedin': '',
            'contact_1_email_confidence': 'none',
            'contact_2_name': '',
            'contact_2_position': '',
            'contact_2_email': '',
            'contact_2_phone': '',
            'contact_2_linkedin': '',
            'contact_2_email_confidence': 'none',
            'contact_3_name': '',
            'contact_3_position': '',
            'contact_3_email': '',
            'contact_3_phone': '',
            'contact_3_linkedin': '',
            'contact_3_email_confidence': 'none',
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
