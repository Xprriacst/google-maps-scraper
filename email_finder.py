#!/usr/bin/env python3
"""
Module de recherche d'emails intelligent
Scrape les sites web et génère des patterns d'emails pour les entreprises françaises
"""

import re
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import time

class EmailFinder:
    def __init__(self):
        """Initialise le chercheur d'emails"""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
        
        # Regex pour trouver des emails
        self.email_pattern = re.compile(
            r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        )
        
        # Pages communes où trouver des emails
        self.contact_pages = [
            '', # Page d'accueil
            '/contact',
            '/contact-us',
            '/nous-contacter',
            '/contactez-nous',
            '/about',
            '/a-propos',
            '/mentions-legales',
            '/legal',
            '/equipe',
            '/team'
        ]
    
    def extract_domain(self, website):
        """
        Extrait le domaine propre d'une URL
        
        Args:
            website: URL complète (ex: https://www.example.com/page)
        
        Returns:
            Domaine propre (ex: example.com)
        """
        if not website:
            return None
        
        try:
            # Ajouter http:// si manquant
            if not website.startswith(('http://', 'https://')):
                website = 'https://' + website
            
            parsed = urlparse(website)
            domain = parsed.netloc
            
            # Retirer www.
            domain = domain.replace('www.', '')
            
            return domain if domain else None
        except:
            return None
    
    def scrape_website_for_emails(self, website, timeout=10):
        """
        Scrape un site web pour trouver des emails
        
        Args:
            website: URL du site web
            timeout: Timeout en secondes
        
        Returns:
            Liste d'emails trouvés
        """
        emails = set()
        
        if not website:
            return list(emails)
        
        # Ajouter http:// si manquant
        if not website.startswith(('http://', 'https://')):
            website = 'https://' + website
        
        try:
            # Essayer plusieurs pages potentielles
            for page in self.contact_pages[:3]:  # Limiter à 3 pages pour la rapidité
                url = urljoin(website, page)
                
                try:
                    response = self.session.get(url, timeout=timeout, allow_redirects=True)
                    
                    if response.status_code == 200:
                        # Chercher dans le texte brut
                        page_emails = self.email_pattern.findall(response.text)
                        
                        # Chercher dans le HTML parsé
                        soup = BeautifulSoup(response.content, 'lxml')
                        
                        # Chercher dans les liens mailto:
                        for link in soup.find_all('a', href=True):
                            if link['href'].startswith('mailto:'):
                                email = link['href'].replace('mailto:', '').split('?')[0]
                                page_emails.append(email)
                        
                        # Ajouter les emails valides
                        for email in page_emails:
                            email = email.lower().strip()
                            # Filtrer les emails non pertinents
                            if self._is_valid_email(email):
                                emails.add(email)
                        
                        # Si on a trouvé des emails, pas besoin de chercher plus
                        if emails:
                            break
                    
                    time.sleep(0.5)  # Rate limiting
                    
                except:
                    continue
        
        except Exception as e:
            pass
        
        return list(emails)
    
    def _is_valid_email(self, email):
        """
        Vérifie si un email est valide et pertinent
        
        Args:
            email: Email à vérifier
        
        Returns:
            True si valide, False sinon
        """
        if not email or '@' not in email:
            return False
        
        # Filtrer les emails non pertinents
        blacklist = [
            'example.com',
            'test.com',
            'yoursite.com',
            'domain.com',
            'email.com',
            'wix.com',
            'wordpress.com',
            'sentry.io',
            'noreply',
            'no-reply',
            'mailer-daemon',
            '.png',
            '.jpg',
            '.gif',
            '.css',
            '.js'
        ]
        
        email_lower = email.lower()
        
        for item in blacklist:
            if item in email_lower:
                return False
        
        return True
    
    def generate_email_patterns(self, company_name, website):
        """
        Génère des patterns d'emails intelligents basés sur le nom de l'entreprise
        
        Args:
            company_name: Nom de l'entreprise
            website: Site web de l'entreprise
        
        Returns:
            Liste de patterns d'emails possibles
        """
        domain = self.extract_domain(website)
        
        if not domain:
            return []
        
        patterns = [
            f"contact@{domain}",
            f"info@{domain}",
            f"hello@{domain}",
            f"bonjour@{domain}",
            f"accueil@{domain}",
            f"commercial@{domain}",
            f"direction@{domain}",
            f"gerant@{domain}",
        ]
        
        # Essayer d'extraire un prénom/nom si le nom de l'entreprise contient un nom de personne
        # Ex: "Boulangerie Martin" -> martin@domain.com
        if company_name:
            words = company_name.lower().split()
            for word in words:
                # Éviter les mots génériques
                if len(word) > 3 and word not in ['sarl', 'sas', 'eurl', 'auto', 'boulangerie', 'restaurant', 'salon']:
                    patterns.append(f"{word}@{domain}")
        
        return patterns
    
    def find_contact_email(self, company_name, website):
        """
        Trouve les emails de contact d'une entreprise (3 types)

        Args:
            company_name: Nom de l'entreprise
            website: Site web de l'entreprise

        Returns:
            Dict avec 3 types d'emails:
            - email_generated: Email pattern généré (contact@, info@)
            - email_scraped: Email trouvé sur le site web
            - email: Email principal (meilleur trouvé)
        """
        result = {
            # Contact 1: Email générique généré
            'email_generated': '',
            'email_generated_confidence': 'low',

            # Contact 2: Email scrapé sur le site
            'email_scraped': '',
            'email_scraped_confidence': '',

            # Email principal (pour compatibilité)
            'email': '',
            'source': '',
            'confidence': 'low'
        }

        # 1. Toujours générer un pattern d'email (Contact 1)
        patterns = self.generate_email_patterns(company_name, website)
        if patterns:
            result['email_generated'] = patterns[0]  # contact@ ou info@
            result['email_generated_confidence'] = 'low'

        # 2. Essayer de scraper le site web (Contact 2)
        if website:
            print(f"  🔍 Scraping {website[:50]}...")
            scraped_emails = self.scrape_website_for_emails(website)

            if scraped_emails:
                # Prioriser les emails "contact", "info", etc.
                priority_keywords = ['contact', 'info', 'hello', 'bonjour', 'commercial', 'direction']

                best_scraped = None
                for keyword in priority_keywords:
                    for email in scraped_emails:
                        if keyword in email.lower():
                            best_scraped = email
                            result['email_scraped'] = email
                            result['email_scraped_confidence'] = 'high'
                            break
                    if best_scraped:
                        break

                # Si aucun email prioritaire, prendre le premier
                if not best_scraped and scraped_emails:
                    result['email_scraped'] = scraped_emails[0]
                    result['email_scraped_confidence'] = 'medium'

                # L'email scrapé devient l'email principal
                if result['email_scraped']:
                    result['email'] = result['email_scraped']
                    result['source'] = 'scraped_website'
                    result['confidence'] = result['email_scraped_confidence']
                    return result

        # 3. Si rien de scrapé, utiliser le pattern généré comme principal
        if result['email_generated']:
            result['email'] = result['email_generated']
            result['source'] = 'generated_pattern'
            result['confidence'] = 'low'

        return result
    
    def find_manager_name(self, company_name, website):
        """
        Essaie de trouver le nom du gérant sur le site web
        
        Args:
            company_name: Nom de l'entreprise
            website: Site web
        
        Returns:
            Nom du gérant ou chaîne vide
        """
        if not website:
            return ''
        
        # Ajouter http:// si manquant
        if not website.startswith(('http://', 'https://')):
            website = 'https://' + website
        
        try:
            # Pages potentielles
            pages = ['', '/about', '/a-propos', '/equipe', '/team', '/mentions-legales']
            
            keywords = ['gérant', 'dirigeant', 'président', 'directeur', 'fondateur', 'ceo', 'manager']
            
            for page in pages[:2]:  # Limiter à 2 pages
                url = urljoin(website, page)
                
                try:
                    response = self.session.get(url, timeout=8)
                    
                    if response.status_code == 200:
                        soup = BeautifulSoup(response.content, 'lxml')
                        text = soup.get_text().lower()
                        
                        # Chercher les patterns
                        for keyword in keywords:
                            if keyword in text:
                                # Essayer d'extraire le nom après le titre
                                pattern = rf'{keyword}\s*:?\s*([A-Z][a-z]+\s+[A-Z][a-z]+)'
                                match = re.search(pattern, soup.get_text())
                                if match:
                                    return match.group(1)
                    
                    time.sleep(0.5)
                
                except:
                    continue
        
        except:
            pass
        
        return ''


if __name__ == "__main__":
    # Test du module
    finder = EmailFinder()
    
    test_cases = [
        ("Boulangerie Martin", "https://www.example-boulangerie.fr"),
        ("Restaurant Le Gourmet", "https://legourmet.com"),
    ]
    
    for company, website in test_cases:
        print(f"\n🧪 Test: {company} - {website}")
        result = finder.find_contact_email(company, website)
        print(f"   Email: {result['email']}")
        print(f"   Source: {result['source']}")
        print(f"   Confiance: {result['confidence']}")
