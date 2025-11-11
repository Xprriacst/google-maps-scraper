#!/usr/bin/env python3
"""
GPT Contact Scraper - Utilise GPT-4/5 pour scraper intelligemment les sites web
Extrait les emails, téléphones et contacts des pages web d'entreprises
"""

import requests
from bs4 import BeautifulSoup
from openai import OpenAI
from typing import List, Dict, Optional
from utils import get_env


class GPTContactScraper:
    """Scraper de contacts utilisant GPT pour l'extraction intelligente"""

    def __init__(self, openai_api_key: str = None):
        """
        Initialise le scraper GPT

        Args:
            openai_api_key: Clé API OpenAI (si None, utilise get_env)
        """
        self.api_key = openai_api_key or get_env('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY requise")

        self.client = OpenAI(api_key=self.api_key)
        print("✅ GPT Contact Scraper initialisé")

    def scrape_website_contacts(self, website_url: str, company_name: str = None) -> List[Dict]:
        """
        Scrape un site web et utilise GPT pour extraire les contacts

        Args:
            website_url: URL du site web à scraper
            company_name: Nom de l'entreprise (optionnel)

        Returns:
            Liste de contacts trouvés avec emails, téléphones, noms
        """
        if not website_url or website_url == 'N/A':
            return []

        print(f"\n🤖 Scraping GPT: {website_url}")

        try:
            # 1. Récupérer le contenu HTML du site
            html_content = self._fetch_website_html(website_url)
            if not html_content:
                return []

            # 2. Extraire le texte pertinent (pages contact, à propos, etc.)
            relevant_text = self._extract_relevant_text(html_content, website_url)
            if not relevant_text:
                print("  ⚠️  Aucun texte pertinent trouvé")
                return []

            # 3. Utiliser GPT pour extraire les contacts
            contacts = self._extract_contacts_with_gpt(relevant_text, company_name)

            print(f"  ✅ Trouvé {len(contacts)} contact(s) via GPT")
            return contacts

        except Exception as e:
            print(f"  ❌ Erreur GPT scraping: {e}")
            return []

    def _fetch_website_html(self, url: str) -> str:
        """Récupère le HTML d'une page web"""
        try:
            # Ajouter https:// si manquant
            if not url.startswith('http'):
                url = f'https://{url}'

            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }

            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            return response.text

        except Exception as e:
            print(f"  ⚠️  Erreur fetch: {e}")
            return ""

    def _extract_relevant_text(self, html: str, base_url: str) -> str:
        """
        Extrait le texte pertinent du HTML
        Se concentre sur les pages contact, équipe, à propos
        """
        try:
            soup = BeautifulSoup(html, 'html.parser')

            # Supprimer les scripts et styles
            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()

            # Chercher les sections pertinentes
            contact_sections = soup.find_all(['div', 'section', 'main'],
                                            class_=lambda x: x and any(
                                                keyword in str(x).lower()
                                                for keyword in ['contact', 'about', 'team', 'equipe', 'propos']
                                            ))

            # Si pas de sections spécifiques, prendre tout le body
            if not contact_sections:
                contact_sections = soup.find_all(['main', 'body'])

            # Extraire le texte
            text_parts = []
            for section in contact_sections[:3]:  # Limiter à 3 sections
                text = section.get_text(separator='\n', strip=True)
                text_parts.append(text)

            full_text = '\n\n'.join(text_parts)

            # Limiter la taille (GPT a des limites de tokens)
            max_chars = 8000
            if len(full_text) > max_chars:
                full_text = full_text[:max_chars] + "..."

            return full_text

        except Exception as e:
            print(f"  ⚠️  Erreur extraction texte: {e}")
            return ""

    def _extract_contacts_with_gpt(self, text: str, company_name: str = None) -> List[Dict]:
        """
        Utilise GPT pour extraire intelligemment les contacts du texte
        """
        try:
            prompt = f"""Tu es un expert en extraction de données de contacts professionnels.

Analyse le texte suivant extrait d'un site web d'entreprise{' (' + company_name + ')' if company_name else ''} et extrais TOUS les contacts commerciaux que tu peux trouver.

Pour chaque contact, extrait :
- Le nom complet (si disponible)
- La fonction/poste (si disponible)
- L'email commercial (PRIORITÉ)
- Le téléphone (si disponible)
- Toute note pertinente

IMPORTANT:
- Cherche les emails génériques comme contact@, commercial@, info@, vente@, etc.
- Cherche aussi les emails de personnes spécifiques
- Note la page ou section où tu as trouvé l'info
- Si plusieurs emails/téléphones existent, retourne-les tous

Format de réponse JSON (liste de contacts):
[
  {{
    "name": "Nom complet ou 'Contact commercial'",
    "position": "Poste ou 'Service commercial'",
    "email": "email@exemple.com",
    "phone": "+33 X XX XX XX XX",
    "notes": "Page Contact, Email principal du site, etc.",
    "confidence": "high|medium|low"
  }}
]

Si aucun contact n'est trouvé, retourne une liste vide: []

TEXTE À ANALYSER:
{text}

Réponds UNIQUEMENT avec le JSON, sans texte avant ou après."""

            # Appel à GPT-5
            response = self.client.chat.completions.create(
                model="gpt-5",  # GPT-5 (novembre 2025)
                messages=[
                    {"role": "system", "content": "Tu es un expert en extraction de données B2B. Tu réponds uniquement en JSON valide."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,  # Plus déterministe
                max_tokens=2000
            )

            # Parser la réponse
            import json
            result_text = response.choices[0].message.content.strip()

            # Nettoyer le JSON (enlever les markdown code blocks si présents)
            if result_text.startswith('```'):
                result_text = result_text.split('```')[1]
                if result_text.startswith('json'):
                    result_text = result_text[4:]
                result_text = result_text.strip()

            contacts = json.loads(result_text)

            # Ajouter la source
            for contact in contacts:
                contact['source'] = 'gpt_scraping'

            return contacts

        except json.JSONDecodeError as e:
            print(f"  ⚠️  Erreur parsing JSON: {e}")
            print(f"  Réponse brute: {result_text[:200]}...")
            return []
        except Exception as e:
            print(f"  ❌ Erreur GPT: {e}")
            return []


if __name__ == "__main__":
    # Test du scraper
    scraper = GPTContactScraper()

    # Test avec un site web
    print("\n" + "="*60)
    print("🧪 TEST: Scraping GPT")
    print("="*60)

    contacts = scraper.scrape_website_contacts(
        website_url="https://www.archiveranda.com",
        company_name="Archi Véranda"
    )

    print(f"\n📊 Résultats: {len(contacts)} contact(s)")
    for contact in contacts:
        print(f"\n  👤 {contact.get('name', 'N/A')}")
        print(f"     Fonction: {contact.get('position', 'N/A')}")
        print(f"     Email: {contact.get('email', 'N/A')}")
        print(f"     Tel: {contact.get('phone', 'N/A')}")
        print(f"     Confiance: {contact.get('confidence', 'N/A')}")
        print(f"     Notes: {contact.get('notes', 'N/A')}")
