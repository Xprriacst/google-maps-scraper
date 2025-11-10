#!/usr/bin/env python3
"""
Module d'enrichissement de contacts pour la prospection B2B
Trouve les décideurs, enrichit avec LinkedIn, APIs publiques et scraping avancé

Stratégie d'enrichissement (v2.0) :
1. API entreprise.data.gouv.fr → Données officielles (SIRET, CA, effectifs, dirigeant légal)
2. Dropcontact → Décideur commercial + email vérifié
3. Fallback → Dirigeant légal si Dropcontact ne trouve rien
"""

import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time
from typing import Dict, List, Optional
import json


class ContactEnricher:
    """Enrichit les contacts d'entreprises avec des données décisionnaires"""

    # Titres de décideurs par ordre de priorité
    DECISION_MAKER_TITLES = [
        # Niveau 1 - Priorité absolue
        'directeur commercial', 'directrice commerciale',
        'directeur général', 'directrice générale', 'dg',
        'gérant', 'gérante',
        'président', 'présidente', 'pdg',
        'ceo', 'chief executive officer',

        # Niveau 2 - Haute priorité
        'directeur développement', 'directrice développement',
        'directeur marketing', 'directrice marketing',
        'responsable commercial', 'responsable commerciale',
        'responsable développement',

        # Niveau 3 - Moyenne priorité
        'directeur', 'directrice',
        'responsable achats',
        'manager',
        'fondateur', 'fondatrice',
        'co-fondateur', 'co-fondatrice',
    ]

    # Titres à éviter
    AVOID_TITLES = [
        'secrétaire', 'secrétariat',
        'sav', 'service après-vente',
        'technicien', 'technicienne',
        'assistant', 'assistante',
        'stagiaire',
        'apprenti', 'apprentie',
    ]

    def __init__(self, use_dropcontact: bool = True):
        """
        Initialise l'enrichisseur de contacts

        Args:
            use_dropcontact: Utiliser Dropcontact pour l'enrichissement (défaut: True)
        """
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })

        # Patterns pour extraire emails
        self.email_pattern = re.compile(
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        )

        # Patterns pour extraire noms de personnes
        self.name_pattern = re.compile(
            r'\b([A-Z][a-zàâäéèêëïîôùûüç]+(?:\s+[A-Z][a-zàâäéèêëïîôùûüç]+)+)\b'
        )

        # Cache pour éviter les appels répétés
        self.cache = {}

        # Dropcontact enricher (optionnel)
        self.dropcontact = None
        self.use_dropcontact = use_dropcontact

        if use_dropcontact:
            try:
                from dropcontact_enricher import DropcontactEnricher
                from utils import get_env

                api_key = get_env('DROPCONTACT_API_KEY')
                if api_key:
                    self.dropcontact = DropcontactEnricher(api_key)
                    print("✅ Dropcontact activé")
                else:
                    print("⚠️  DROPCONTACT_API_KEY non configurée - enrichissement sans Dropcontact")
                    self.use_dropcontact = False
            except Exception as e:
                print(f"⚠️  Impossible d'initialiser Dropcontact: {e}")
                self.use_dropcontact = False

    def extract_domain(self, website: str) -> Optional[str]:
        """
        Extrait le domaine propre d'une URL

        Args:
            website: URL complète

        Returns:
            Domaine propre (ex: example.com)
        """
        if not website:
            return None

        try:
            if not website.startswith(('http://', 'https://')):
                website = 'https://' + website

            parsed = urlparse(website)
            domain = parsed.netloc.replace('www.', '')
            return domain if domain else None
        except:
            return None

    def find_decision_maker_linkedin(self, company_name: str) -> Dict:
        """
        Cherche le décideur sur LinkedIn (via Google Search)

        Args:
            company_name: Nom de l'entreprise

        Returns:
            Dict avec nom, fonction, profil LinkedIn
        """
        result = {
            'name': '',
            'position': '',
            'linkedin_url': '',
            'confidence': 'none'
        }

        # Pour chaque titre de décideur, chercher sur LinkedIn
        for title in self.DECISION_MAKER_TITLES[:5]:  # Top 5 seulement
            search_query = f'site:linkedin.com/in {company_name} {title}'

            try:
                # Simuler une recherche Google (en réalité on utiliserait l'API Google ou un scraper)
                # Pour l'instant, on retourne un placeholder
                # Dans une vraie implémentation, on utiliserait :
                # - L'API LinkedIn (payante)
                # - Un scraper LinkedIn (attention aux ToS)
                # - L'API Google Custom Search

                # PLACEHOLDER - À implémenter avec une vraie API
                print(f"  🔍 LinkedIn: Recherche '{title}' pour {company_name[:30]}...")

                # Pause pour éviter rate limiting
                time.sleep(0.5)

            except Exception as e:
                print(f"  ⚠️  Erreur LinkedIn search: {e}")
                continue

        return result

    def extract_team_from_website(self, website: str, company_name: str) -> List[Dict]:
        """
        Extrait les membres de l'équipe depuis le site web

        Args:
            website: URL du site web
            company_name: Nom de l'entreprise

        Returns:
            Liste de dicts avec nom, fonction, email
        """
        team_members = []

        if not website:
            return team_members

        # Cache check
        cache_key = f"team_{website}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        if not website.startswith(('http://', 'https://')):
            website = 'https://' + website

        # Pages prioritaires pour trouver l'équipe
        priority_pages = [
            '/equipe',
            '/team',
            '/notre-equipe',
            '/qui-sommes-nous',
            '/about',
            '/a-propos',
            '/contact',
            '/mentions-legales',
            '/legal',
            '/leadership',
            '/direction',
            '',  # Page d'accueil en dernier
        ]

        print(f"  👥 Scraping équipe sur {website[:50]}...")

        for page in priority_pages:
            url = urljoin(website, page)

            try:
                response = self.session.get(url, timeout=10, allow_redirects=True)

                if response.status_code != 200:
                    continue

                soup = BeautifulSoup(response.content, 'lxml')
                text = soup.get_text()

                # Chercher des patterns de "Nom - Fonction"
                members = self._extract_team_patterns(soup, text)

                if members:
                    team_members.extend(members)
                    print(f"  ✓ Trouvé {len(members)} membre(s) sur {page or '/'}")
                    break  # On a trouvé, pas besoin de continuer

                time.sleep(0.5)  # Rate limiting

            except Exception as e:
                continue

        # Filtrer pour ne garder que les décideurs
        decision_makers = self._filter_decision_makers(team_members)

        # Cache
        self.cache[cache_key] = decision_makers

        return decision_makers

    def _extract_team_patterns(self, soup: BeautifulSoup, text: str) -> List[Dict]:
        """
        Extrait les patterns de membres d'équipe du HTML

        Args:
            soup: BeautifulSoup object
            text: Texte brut de la page

        Returns:
            Liste de dicts avec nom, fonction
        """
        members = []

        # Pattern 1: Chercher dans les éléments structurés (div, section avec class team/equipe)
        team_sections = soup.find_all(['div', 'section'],
                                       class_=re.compile(r'team|equipe|staff|about', re.I))

        for section in team_sections:
            # Chercher les noms et fonctions
            section_text = section.get_text()

            # Pattern: "Nom\nFonction" ou "Nom - Fonction"
            lines = section_text.split('\n')
            for i in range(len(lines) - 1):
                name = lines[i].strip()
                position = lines[i + 1].strip()

                # Vérifier si c'est un nom valide (commence par majuscule, contient prénom + nom)
                if self._is_valid_name(name) and self._is_valid_position(position):
                    members.append({
                        'name': name,
                        'position': position,
                        'email': ''
                    })

        # Pattern 2: Chercher dans le texte brut avec regex
        # Ex: "Jean Dupont - Directeur Commercial"
        pattern = r'([A-Z][a-zàâäéèêëïîôùûüç]+\s+[A-Z][a-zàâäéèêëïîôùûüç]+)\s*[-–—:]\s*([A-Za-zÀ-ÿ\s]+)'
        matches = re.findall(pattern, text)

        for name, position in matches:
            position_clean = position.strip()
            if self._is_valid_position(position_clean) and len(position_clean) < 50:
                members.append({
                    'name': name.strip(),
                    'position': position_clean,
                    'email': ''
                })

        # Pattern 3: Chercher dans les mentions légales (Gérant: Nom)
        legal_patterns = [
            r'gérant\s*:?\s*([A-Z][a-zàâäéèêëïîôùûüç]+\s+[A-Z][a-zàâäéèêëïîôùûüç]+)',
            r'président\s*:?\s*([A-Z][a-zàâäéèêëïîôùûüç]+\s+[A-Z][a-zàâäéèêëïîôùûüç]+)',
            r'directeur\s*:?\s*([A-Z][a-zàâäéèêëïîôùûüç]+\s+[A-Z][a-zàâäéèêëïîôùûüç]+)',
        ]

        for pattern in legal_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for name in matches:
                members.append({
                    'name': name.strip(),
                    'position': 'Gérant',
                    'email': ''
                })

        # Dédupliquer
        unique_members = []
        seen_names = set()

        for member in members:
            name_key = member['name'].lower()
            if name_key not in seen_names:
                seen_names.add(name_key)
                unique_members.append(member)

        return unique_members

    def _is_valid_name(self, name: str) -> bool:
        """Vérifie si une chaîne ressemble à un nom de personne"""
        if not name or len(name) < 5 or len(name) > 50:
            return False

        # Doit contenir au moins prénom + nom (2 mots)
        words = name.split()
        if len(words) < 2:
            return False

        # Mots à exclure (articles, prépositions, etc.)
        excluded_words = {
            'de', 'la', 'le', 'du', 'des', 'et', 'ou', 'à', 'au', 'aux',
            'en', 'pour', 'par', 'sur', 'dans', 'avec', 'sans', 'nous',
            'notre', 'votre', 'leur', 'son', 'sa', 'ses', 'un', 'une'
        }

        # Vérifier que les mots ne sont pas des mots exclus
        valid_words = []
        for word in words:
            # Ignorer les mots trop courts (< 3 caractères) sauf si majuscule
            if len(word) < 3:
                continue

            # Exclure les mots français courants
            if word.lower() in excluded_words:
                continue

            # Le mot doit commencer par une majuscule
            if word[0].isupper():
                valid_words.append(word)

        # Il faut au moins 2 mots valides pour un nom complet
        if len(valid_words) < 2:
            return False

        # Vérifier que les mots valides contiennent au moins 3 lettres chacun
        for word in valid_words:
            if len(word) < 3:
                return False

        return True

    def _is_valid_position(self, position: str) -> bool:
        """Vérifie si une chaîne ressemble à un titre de poste"""
        if not position or len(position) < 3 or len(position) > 100:
            return False

        position_lower = position.lower()

        # Vérifier si contient un mot-clé de fonction
        keywords = [
            'directeur', 'directrice', 'gérant', 'gérante', 'président', 'présidente',
            'responsable', 'manager', 'chef', 'fondateur', 'fondatrice', 'ceo', 'cto',
            'commercial', 'marketing', 'développement', 'achats', 'ventes'
        ]

        return any(keyword in position_lower for keyword in keywords)

    def _filter_decision_makers(self, team_members: List[Dict]) -> List[Dict]:
        """
        Filtre pour ne garder que les décideurs

        Args:
            team_members: Liste complète de l'équipe

        Returns:
            Liste filtrée des décideurs uniquement
        """
        decision_makers = []

        for member in team_members:
            position_lower = member['position'].lower()

            # Vérifier si c'est un titre à éviter
            if any(avoid in position_lower for avoid in self.AVOID_TITLES):
                continue

            # Vérifier si c'est un décideur
            is_decision_maker = False
            priority = 100  # Plus bas = plus prioritaire

            for idx, title in enumerate(self.DECISION_MAKER_TITLES):
                if title in position_lower:
                    is_decision_maker = True
                    priority = idx
                    break

            if is_decision_maker:
                member['priority'] = priority
                decision_makers.append(member)

        # Trier par priorité
        decision_makers.sort(key=lambda x: x.get('priority', 100))

        return decision_makers

    def build_email_from_name(self, name: str, website: str, found_emails: List[str] = None) -> Dict:
        """
        Construit l'email d'une personne à partir de son nom

        Args:
            name: Nom complet (ex: "Jean Dupont")
            website: Site web de l'entreprise
            found_emails: Liste d'emails trouvés sur le site (pour détecter le pattern)

        Returns:
            Dict avec email, pattern, confiance
        """
        domain = self.extract_domain(website)

        if not domain or not name:
            return {'email': '', 'pattern': '', 'confidence': 'none'}

        # Séparer prénom et nom
        parts = name.strip().split()
        if len(parts) < 2:
            return {'email': '', 'pattern': '', 'confidence': 'none'}

        first_name = parts[0].lower()
        last_name = parts[-1].lower()

        # Détecter le pattern utilisé par l'entreprise
        detected_pattern = self._detect_email_pattern(found_emails, domain) if found_emails else None

        # Générer les patterns possibles (par ordre de probabilité)
        patterns = [
            f"{first_name}.{last_name}@{domain}",      # prenom.nom (le plus commun en France)
            f"{first_name}@{domain}",                   # prenom
            f"{last_name}@{domain}",                    # nom
            f"{first_name[0]}.{last_name}@{domain}",   # p.nom
            f"{first_name}{last_name}@{domain}",        # prenomnom
            f"{first_name[0]}{last_name}@{domain}",    # pnom
            f"{first_name}.{last_name[0]}@{domain}",   # prenom.n
        ]

        # Si on a détecté un pattern, le mettre en premier
        if detected_pattern:
            # Appliquer le pattern détecté
            email = self._apply_pattern(detected_pattern, first_name, last_name, domain)
            return {
                'email': email,
                'pattern': detected_pattern,
                'confidence': 'high'
            }

        # Sinon, retourner le pattern le plus probable (prenom.nom)
        return {
            'email': patterns[0],
            'pattern': 'prenom.nom@domaine',
            'confidence': 'medium'
        }

    def _detect_email_pattern(self, emails: List[str], domain: str) -> Optional[str]:
        """
        Détecte le pattern d'email utilisé par l'entreprise

        Args:
            emails: Liste d'emails trouvés
            domain: Domaine de l'entreprise

        Returns:
            Pattern détecté ou None
        """
        if not emails:
            return None

        # Filtrer les emails du domaine de l'entreprise
        company_emails = [e for e in emails if domain in e.lower()]

        if not company_emails:
            return None

        # Analyser les patterns
        for email in company_emails:
            local_part = email.split('@')[0].lower()

            # Ignorer les emails génériques
            if local_part in ['contact', 'info', 'hello', 'bonjour', 'commercial']:
                continue

            # Détecter le pattern
            if '.' in local_part and len(local_part.split('.')) == 2:
                parts = local_part.split('.')
                if len(parts[0]) > 1 and len(parts[1]) > 1:
                    return 'prenom.nom@domaine'
                elif len(parts[0]) == 1:
                    return 'p.nom@domaine'
            elif len(local_part) > 6:  # prenomnom
                return 'prenomnom@domaine'

        return None

    def _apply_pattern(self, pattern: str, first_name: str, last_name: str, domain: str) -> str:
        """Applique un pattern pour générer un email"""
        patterns_map = {
            'prenom.nom@domaine': f"{first_name}.{last_name}@{domain}",
            'p.nom@domaine': f"{first_name[0]}.{last_name}@{domain}",
            'prenomnom@domaine': f"{first_name}{last_name}@{domain}",
            'prenom@domaine': f"{first_name}@{domain}",
            'nom@domaine': f"{last_name}@{domain}",
        }

        return patterns_map.get(pattern, f"{first_name}.{last_name}@{domain}")

    def validate_email_pattern(self, email: str, website: str) -> str:
        """
        Valide un email en vérifiant le pattern contre le site web

        Args:
            email: Email à valider
            website: Site web de l'entreprise

        Returns:
            Confiance: 'high', 'medium', 'low'
        """
        # Pour l'instant, on retourne medium par défaut
        # Dans une vraie implémentation, on pourrait :
        # - Vérifier le MX record du domaine
        # - Faire une validation SMTP (attention au rate limiting)
        # - Comparer avec les emails trouvés sur le site

        if not email or '@' not in email:
            return 'none'

        domain = self.extract_domain(website)
        if domain and domain in email:
            return 'medium'

        return 'low'

    def enrich_with_api(self, company_name: str, website: str = None,
                        address: str = None) -> Dict:
        """
        Enrichit avec les APIs publiques françaises

        Args:
            company_name: Nom de l'entreprise
            website: Site web (optionnel)
            address: Adresse (optionnel)

        Returns:
            Dict avec SIRET, forme juridique, CA, dirigeant, etc.
        """
        result = {
            'siret': '',
            'siren': '',
            'legal_form': '',
            'revenue': '',
            'employees': '',
            'legal_manager': '',
            'legal_manager_position': '',
            'creation_date': '',
            'api_source': ''
        }

        print(f"  🔍 Recherche SIRET/SIREN pour {company_name[:30]}...")

        try:
            # API 1: entreprise.data.gouv.fr (API publique gratuite)
            # Rechercher l'entreprise par nom
            search_url = "https://recherche-entreprises.api.gouv.fr/search"
            params = {
                'q': company_name,
                'per_page': 1
            }

            response = self.session.get(search_url, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()

                if data.get('results') and len(data['results']) > 0:
                    company = data['results'][0]

                    result['siret'] = company.get('siege', {}).get('siret', '')
                    result['siren'] = company.get('siren', '')
                    result['legal_form'] = company.get('nature_juridique', '')
                    result['creation_date'] = company.get('date_creation', '')
                    result['api_source'] = 'entreprise.data.gouv.fr'

                    # Dirigeant
                    dirigeant = company.get('dirigeants', [])
                    if dirigeant and len(dirigeant) > 0:
                        result['legal_manager'] = dirigeant[0].get('nom', '') + ' ' + dirigeant[0].get('prenom', '')
                        result['legal_manager_position'] = dirigeant[0].get('qualite', '')

                    # Effectifs
                    effectifs = company.get('matching_etablissements', [{}])[0].get('effectif', '')
                    if effectifs:
                        result['employees'] = effectifs

                    print(f"  ✓ SIRET trouvé: {result['siret']}")

        except Exception as e:
            print(f"  ⚠️  Erreur API entreprise.data.gouv.fr: {e}")

        # Pause pour rate limiting
        time.sleep(0.5)

        return result

    def enrich_contact(self, company_name: str, website: str = None,
                       address: str = None) -> Dict:
        """
        Méthode principale d'enrichissement d'un contact

        Args:
            company_name: Nom de l'entreprise
            website: Site web
            address: Adresse

        Returns:
            Dict complet avec toutes les infos enrichies
        """
        print(f"\n🔍 Enrichissement: {company_name}")

        enriched = {
            # Contact
            'contact_name': '',
            'contact_position': '',
            'contact_email': '',
            'contact_phone': '',
            'contact_linkedin': '',
            'email_confidence': 'none',

            # Entreprise
            'siret': '',
            'siren': '',
            'legal_form': '',
            'revenue': '',
            'employees': '',
            'creation_date': '',

            # Métadonnées
            'enrichment_date': time.strftime('%Y-%m-%d %H:%M:%S'),
            'data_sources': []
        }

        # 1. Enrichir avec l'API entreprise.data.gouv.fr (données officielles)
        print("  📊 Étape 1/2: API entreprise.data.gouv.fr...")
        api_data = self.enrich_with_api(company_name, website, address)

        enriched['siret'] = api_data['siret']
        enriched['siren'] = api_data['siren']
        enriched['legal_form'] = api_data['legal_form']
        enriched['revenue'] = api_data['revenue']
        enriched['employees'] = api_data['employees']
        enriched['creation_date'] = api_data['creation_date']

        if api_data['api_source']:
            enriched['data_sources'].append(api_data['api_source'])

        # 2. Chercher le décideur commercial avec Dropcontact
        if self.use_dropcontact and self.dropcontact:
            print("  🎯 Étape 2/2: Dropcontact (décideur commercial)...")

            try:
                dropcontact_result = self.dropcontact.enrich_contact(
                    company_name=company_name,
                    website=website,
                    company_siret=enriched['siret']
                )

                # Si Dropcontact a trouvé un contact
                if dropcontact_result['contact_name']:
                    enriched['contact_name'] = dropcontact_result['contact_name']
                    enriched['contact_position'] = dropcontact_result['contact_position']
                    enriched['contact_email'] = dropcontact_result['contact_email']
                    enriched['contact_phone'] = dropcontact_result['contact_phone']
                    enriched['contact_linkedin'] = dropcontact_result['contact_linkedin']
                    enriched['email_confidence'] = dropcontact_result['email_confidence']
                    enriched['data_sources'].extend(dropcontact_result['data_sources'])

            except Exception as e:
                print(f"  ⚠️  Erreur Dropcontact: {e}")
        else:
            print("  ⏭️  Étape 2/2: Dropcontact désactivé - utilisation du dirigeant légal")

        # 3. Fallback: utiliser le dirigeant légal si aucun contact trouvé
        if not enriched['contact_name'] and api_data['legal_manager']:
            print("  🔄 Fallback: Utilisation du dirigeant légal...")
            enriched['contact_name'] = api_data['legal_manager']
            enriched['contact_position'] = api_data['legal_manager_position'] or 'Gérant'
            enriched['data_sources'].append('legal_data')

            # Construire l'email (non vérifié)
            if website:
                email_result = self.build_email_from_name(
                    api_data['legal_manager'],
                    website
                )
                enriched['contact_email'] = email_result['email']
                enriched['email_confidence'] = email_result['confidence']

        # Message récapitulatif
        if enriched['contact_name']:
            print(f"  ✅ Contact trouvé: {enriched['contact_name']} ({enriched['contact_position']})")
            print(f"     Email: {enriched['contact_email']} (confiance: {enriched['email_confidence']})")
            print(f"     Sources: {', '.join(enriched['data_sources'])}")
        else:
            print(f"  ❌ Aucun contact trouvé pour cette entreprise")
            if enriched['data_sources']:
                print(f"     Données entreprise: {', '.join(enriched['data_sources'])}")

        return enriched


if __name__ == "__main__":
    # Test du module
    enricher = ContactEnricher()

    # Test avec une vraie entreprise
    test_company = "Véranda Concept"
    test_website = "https://www.example.com"  # Remplacer par un vrai site pour tester

    print("\n" + "="*60)
    print("🧪 TEST DU MODULE D'ENRICHISSEMENT")
    print("="*60)

    result = enricher.enrich_contact(test_company, test_website)

    print("\n📊 Résultat:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
