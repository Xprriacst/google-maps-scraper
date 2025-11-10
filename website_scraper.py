#!/usr/bin/env python3
"""
Module de scraping de sites web pour extraire contacts et emails
Complète Apollo/Dropcontact pour les entreprises non couvertes
"""

import re
import requests
from bs4 import BeautifulSoup
from typing import Dict, List, Tuple
from urllib.parse import urljoin, urlparse
import time


class WebsiteScraper:
    """
    Scrape les sites web d'entreprises pour extraire:
    - Emails de contacts
    - Noms de personnes
    - Pages contact/équipe
    """

    # Emails génériques à éviter (moins pertinents pour prospection)
    GENERIC_EMAILS = [
        'info@', 'contact@', 'hello@', 'support@', 'service@',
        'admin@', 'webmaster@', 'noreply@', 'no-reply@',
        'sales@', 'commercial@', 'marketing@'
    ]

    # Pages intéressantes à explorer
    INTERESTING_PAGES = [
        '/contact', '/contacts', '/contactez-nous',
        '/equipe', '/team', '/about', '/a-propos',
        '/qui-sommes-nous', '/nous-contacter',
        '/direction', '/management'
    ]

    def __init__(self, timeout: int = 10, max_pages: int = 3):
        """
        Initialise le scraper

        Args:
            timeout: Timeout par requête en secondes
            max_pages: Nombre max de pages à scraper par site
        """
        self.timeout = timeout
        self.max_pages = max_pages
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })

    def scrape_website(self, website: str, company_name: str = None) -> Dict:
        """
        Scrape un site web pour extraire les contacts

        Args:
            website: URL du site web
            company_name: Nom de l'entreprise (pour contexte)

        Returns:
            Dict avec emails, noms, et métadonnées
        """
        result = {
            'emails': [],
            'contact_names': [],
            'pages_scraped': 0,
            'success': False
        }

        if not website:
            return result

        try:
            # Normaliser l'URL
            if not website.startswith(('http://', 'https://')):
                website = 'https://' + website

            print(f"  🌐 Scraping web: {website[:60]}...")

            # 1. Scraper la page d'accueil
            homepage_data = self._scrape_page(website)
            if homepage_data:
                result['emails'].extend(homepage_data['emails'])
                result['contact_names'].extend(homepage_data['names'])
                result['pages_scraped'] += 1

            # 2. Trouver et scraper les pages intéressantes
            if result['pages_scraped'] < self.max_pages:
                interesting_urls = self._find_interesting_pages(website, homepage_data.get('soup'))

                for url in interesting_urls[:self.max_pages - 1]:
                    time.sleep(0.5)  # Politesse
                    page_data = self._scrape_page(url)
                    if page_data:
                        result['emails'].extend(page_data['emails'])
                        result['contact_names'].extend(page_data['names'])
                        result['pages_scraped'] += 1

            # 3. Dédupliquer et scorer les emails
            result['emails'] = list(set(result['emails']))
            result['contact_names'] = list(set(result['contact_names']))

            # 4. Filtrer et scorer
            scored_emails = self._score_emails(result['emails'], company_name)

            if scored_emails:
                result['success'] = True
                result['best_email'] = scored_emails[0]
                result['all_emails_scored'] = scored_emails

                print(f"  ✅ {len(scored_emails)} email(s) trouvé(s) sur le site web")
                for i, (email, score, reason) in enumerate(scored_emails[:3], 1):
                    print(f"     {i}. {email} (score: {score}, {reason})")
            else:
                print(f"  ⚠️  Aucun email pertinent trouvé sur le site")

        except Exception as e:
            print(f"  ⚠️  Erreur scraping web: {e}")

        return result

    def _scrape_page(self, url: str) -> Dict:
        """
        Scrape une page spécifique

        Args:
            url: URL de la page

        Returns:
            Dict avec emails, noms, et soup BeautifulSoup
        """
        try:
            response = self.session.get(url, timeout=self.timeout, allow_redirects=True)

            if response.status_code != 200:
                return None

            soup = BeautifulSoup(response.content, 'html.parser')

            # Extraire les emails
            emails = self._extract_emails(soup, response.text)

            # Extraire les noms
            names = self._extract_names(soup)

            return {
                'emails': emails,
                'names': names,
                'soup': soup
            }

        except Exception as e:
            return None

    def _extract_emails(self, soup: BeautifulSoup, text: str) -> List[str]:
        """
        Extrait tous les emails d'une page

        Args:
            soup: BeautifulSoup object
            text: Texte brut de la page

        Returns:
            Liste d'emails
        """
        emails = []

        # Pattern email
        email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')

        # 1. Chercher dans le texte visible
        for text_node in soup.find_all(text=True):
            found = email_pattern.findall(str(text_node))
            emails.extend(found)

        # 2. Chercher dans les attributs href="mailto:"
        for link in soup.find_all('a', href=True):
            if link['href'].startswith('mailto:'):
                email = link['href'].replace('mailto:', '').split('?')[0]
                if '@' in email:
                    emails.append(email)

        # 3. Chercher dans le code source brut (parfois obfusqué)
        found_in_text = email_pattern.findall(text)
        emails.extend(found_in_text)

        # Nettoyer
        cleaned = []
        for email in emails:
            email = email.lower().strip()
            # Éviter les faux emails
            if email and '@' in email and '.' in email.split('@')[1]:
                # Retirer les caractères parasites
                email = re.sub(r'[<>"\']', '', email)
                if len(email) > 5 and len(email) < 100:
                    cleaned.append(email)

        return list(set(cleaned))

    def _extract_names(self, soup: BeautifulSoup) -> List[str]:
        """
        Extrait les noms de personnes d'une page

        Args:
            soup: BeautifulSoup object

        Returns:
            Liste de noms
        """
        names = []

        # Pattern nom: Prénom NOM ou Prénom Nom
        name_pattern = re.compile(
            r'\b([A-ZÀÂÄÉÈÊËÏÎÔÙÛÜÇ][a-zàâäéèêëïîôùûüç]+(?:\s+[A-ZÀÂÄÉÈÊËÏÎÔÙÛÜÇ][a-zàâäéèêëïîôùûüç]+){1,2})\b'
        )

        # Chercher dans les sections pertinentes
        interesting_sections = soup.find_all(['div', 'section', 'p'], class_=re.compile(
            r'(team|equipe|contact|about|direction|management|staff)', re.I
        ))

        for section in interesting_sections:
            text = section.get_text()
            found = name_pattern.findall(text)
            names.extend(found)

        # Chercher aussi dans les balises avec rôles
        for element in soup.find_all(True, {'itemprop': 'name'}):
            names.append(element.get_text().strip())

        return list(set(names))[:10]  # Max 10 noms

    def _find_interesting_pages(self, base_url: str, homepage_soup: BeautifulSoup) -> List[str]:
        """
        Trouve les pages intéressantes à scraper (contact, équipe, etc.)

        Args:
            base_url: URL de base du site
            homepage_soup: Soup de la page d'accueil

        Returns:
            Liste d'URLs intéressantes
        """
        interesting_urls = []

        if not homepage_soup:
            return interesting_urls

        # Chercher tous les liens
        for link in homepage_soup.find_all('a', href=True):
            href = link['href']
            full_url = urljoin(base_url, href)

            # Vérifier si le lien contient un mot-clé intéressant
            href_lower = href.lower()
            for keyword in self.INTERESTING_PAGES:
                if keyword in href_lower:
                    # S'assurer que c'est le même domaine
                    if urlparse(full_url).netloc == urlparse(base_url).netloc:
                        interesting_urls.append(full_url)
                        break

        return list(set(interesting_urls))

    def _score_emails(self, emails: List[str], company_name: str = None) -> List[Tuple[str, int, str]]:
        """
        Score et filtre les emails par pertinence

        Args:
            emails: Liste d'emails bruts
            company_name: Nom de l'entreprise

        Returns:
            Liste de tuples (email, score, raison) triée par score décroissant
        """
        scored = []

        for email in emails:
            score = 0
            reasons = []

            local_part = email.split('@')[0]
            domain_part = email.split('@')[1]

            # Pénaliser les emails génériques
            is_generic = any(generic in email for generic in self.GENERIC_EMAILS)
            if is_generic:
                score -= 50
                reasons.append("générique")

            # Valoriser pattern prenom.nom
            if '.' in local_part and not local_part.startswith('.') and not local_part.endswith('.'):
                score += 30
                reasons.append("pattern nom")

            # Valoriser les emails courts (souvent personnels)
            if len(local_part) < 20 and not is_generic:
                score += 20
                reasons.append("court")

            # Pénaliser très longs (souvent automatiques)
            if len(local_part) > 30:
                score -= 20

            # Valoriser si contient des lettres (pas que chiffres)
            if re.search(r'[a-z]', local_part):
                score += 10

            # Bonus si match avec le nom d'entreprise (email dédié)
            if company_name:
                company_clean = re.sub(r'[^a-z0-9]', '', company_name.lower())
                domain_clean = re.sub(r'[^a-z0-9]', '', domain_part.split('.')[0].lower())
                if company_clean in domain_clean or domain_clean in company_clean:
                    score += 15
                    reasons.append("domaine entreprise")

            # Filtrer les emails avec score trop faible
            if score > -20:
                reason_text = ", ".join(reasons) if reasons else "standard"
                scored.append((email, score, reason_text))

        # Trier par score décroissant
        scored.sort(key=lambda x: x[1], reverse=True)

        return scored


if __name__ == "__main__":
    # Test du module
    print("=== Test Website Scraper ===\n")

    scraper = WebsiteScraper()

    # Test avec un site exemple
    result = scraper.scrape_website("https://www.example.com", "Example Company")

    print(f"\nRésultats:")
    print(f"  Pages scrapées: {result['pages_scraped']}")
    print(f"  Emails trouvés: {len(result['emails'])}")
    print(f"  Noms trouvés: {len(result['contact_names'])}")

    if result['success']:
        print(f"  Meilleur email: {result['best_email']}")
