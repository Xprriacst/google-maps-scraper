#!/usr/bin/env python3
"""
Module d'estimation de la taille d'entreprise via IA (OpenAI GPT-4)
Estime TPE/PME/ETI/GE en analysant le site web et les données disponibles
"""

import requests
from bs4 import BeautifulSoup
from typing import Dict, Optional
from utils import get_env


class CompanySizeEstimator:
    """Estime la taille d'une entreprise via IA"""

    def __init__(self, openai_api_key: str = None):
        """
        Initialise l'estimateur

        Args:
            openai_api_key: Clé API OpenAI (si None, charge depuis env)
        """
        self.openai_api_key = openai_api_key or get_env('OPENAI_API_KEY')

        if not self.openai_api_key:
            print("⚠️  OPENAI_API_KEY non configurée - estimation IA désactivée")
            self.enabled = False
        else:
            self.enabled = True

    def estimate_size(self, company_name: str, website: str = None,
                     description: str = None, category: str = None) -> Dict:
        """
        Estime la taille de l'entreprise via IA

        Args:
            company_name: Nom de l'entreprise
            website: Site web de l'entreprise
            description: Description de l'entreprise (optionnel)
            category: Catégorie d'activité (optionnel)

        Returns:
            Dict avec 'employees_estimated', 'size_category', 'confidence'
        """
        if not self.enabled:
            return {
                'employees_estimated': 0,
                'size_category': 'unknown',
                'confidence': 0.0
            }

        try:
            # Extraire des infos du site web
            website_content = ""
            if website:
                website_content = self._scrape_website_summary(website)

            # Construire le prompt pour GPT-4
            prompt = self._build_prompt(company_name, website_content, description, category)

            # Appel à OpenAI
            result = self._call_openai(prompt)

            print(f"  🤖 IA: Estimation taille - {result['size_category']} ({result['employees_estimated']} employés estimés)")

            return result

        except Exception as e:
            print(f"  ⚠️  Erreur estimation IA: {e}")
            return {
                'employees_estimated': 0,
                'size_category': 'unknown',
                'confidence': 0.0
            }

    def _scrape_website_summary(self, website: str, max_length: int = 3000) -> str:
        """
        Extrait un résumé du contenu du site web

        Args:
            website: URL du site
            max_length: Longueur max du texte extrait

        Returns:
            Résumé du contenu
        """
        try:
            if not website.startswith(('http://', 'https://')):
                website = 'https://' + website

            response = requests.get(website, timeout=5, headers={
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            })

            if response.status_code != 200:
                return ""

            soup = BeautifulSoup(response.content, 'html.parser')

            # Supprimer scripts et styles
            for script in soup(["script", "style"]):
                script.decompose()

            # Extraire le texte
            text = soup.get_text()

            # Nettoyer
            lines = (line.strip() for line in text.splitlines())
            chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
            text = ' '.join(chunk for chunk in chunks if chunk)

            # Limiter la longueur
            return text[:max_length]

        except Exception as e:
            print(f"  ⚠️  Erreur scraping site pour IA: {e}")
            return ""

    def _build_prompt(self, company_name: str, website_content: str,
                      description: str = None, category: str = None) -> str:
        """
        Construit le prompt pour GPT-4

        Args:
            company_name: Nom entreprise
            website_content: Contenu du site
            description: Description
            category: Catégorie

        Returns:
            Prompt formaté
        """
        prompt = f"""Tu es un expert en analyse d'entreprises. Estime la taille de l'entreprise suivante en fonction des informations disponibles.

Entreprise : {company_name}
"""

        if category:
            prompt += f"Catégorie : {category}\n"

        if description:
            prompt += f"Description : {description}\n"

        if website_content:
            prompt += f"\nContenu du site web (extrait) :\n{website_content[:2000]}\n"

        prompt += """
Basé sur ces informations, estime :
1. Le nombre d'employés approximatif
2. La catégorie de taille selon la classification française :
   - TPE : 0-10 employés
   - PME : 11-250 employés
   - ETI : 251-5000 employés
   - GE : 5000+ employés

Indices à considérer :
- Mentions d'équipe, collaborateurs, bureaux multiples
- Présence internationale vs locale
- Gamme de produits/services (large = plus grand)
- Ton du site (artisanal vs corporate)
- Mentions de chiffre d'affaires, levées de fonds, etc.

Réponds UNIQUEMENT au format JSON suivant (sans markdown, juste le JSON) :
{
  "employees_estimated": <nombre>,
  "size_category": "<TPE|PME|ETI|GE>",
  "confidence": <0.0-1.0>,
  "reasoning": "<explication courte>"
}
"""

        return prompt

    def _call_openai(self, prompt: str) -> Dict:
        """
        Appelle l'API OpenAI GPT-4

        Args:
            prompt: Prompt à envoyer

        Returns:
            Dict avec estimation
        """
        import json

        headers = {
            'Authorization': f'Bearer {self.openai_api_key}',
            'Content-Type': 'application/json'
        }

        data = {
            'model': 'gpt-4o',  # GPT-4o pour meilleure précision
            'messages': [
                {
                    'role': 'system',
                    'content': 'Tu es un expert en analyse d\'entreprises. Réponds toujours en JSON valide sans markdown.'
                },
                {
                    'role': 'user',
                    'content': prompt
                }
            ],
            'temperature': 0.3,  # Peu de créativité, on veut de la précision
            'max_tokens': 200
        }

        response = requests.post(
            'https://api.openai.com/v1/chat/completions',
            headers=headers,
            json=data,
            timeout=30
        )

        if response.status_code != 200:
            raise Exception(f"OpenAI API error: {response.status_code} - {response.text}")

        result = response.json()
        content = result['choices'][0]['message']['content'].strip()

        # Parser le JSON
        # Parfois GPT retourne avec des backticks markdown, on les nettoie
        content = content.replace('```json', '').replace('```', '').strip()

        try:
            parsed = json.loads(content)
            return {
                'employees_estimated': parsed.get('employees_estimated', 0),
                'size_category': parsed.get('size_category', 'unknown'),
                'confidence': parsed.get('confidence', 0.5),
                'reasoning': parsed.get('reasoning', '')
            }
        except json.JSONDecodeError as e:
            print(f"  ⚠️  Erreur parsing JSON OpenAI: {content}")
            # Fallback : essayer d'extraire les infos manuellement
            return {
                'employees_estimated': 0,
                'size_category': 'unknown',
                'confidence': 0.0
            }


if __name__ == "__main__":
    # Test du module
    print("=== Test Company Size Estimator ===\n")

    try:
        estimator = CompanySizeEstimator()

        if not estimator.enabled:
            print("⚠️  OpenAI API non configurée")
            print("💡 Ajoutez OPENAI_API_KEY dans votre .env")
        else:
            # Test avec une entreprise connue
            print("Test : Estimation taille entreprise")
            result = estimator.estimate_size(
                company_name="Boulangerie Dupont",
                website="https://example.com",
                category="Boulangerie-pâtisserie"
            )

            print(f"\nRésultat:")
            print(f"  Employés estimés: {result['employees_estimated']}")
            print(f"  Catégorie: {result['size_category']}")
            print(f"  Confiance: {result['confidence']:.0%}")
            if 'reasoning' in result:
                print(f"  Raisonnement: {result['reasoning']}")

    except Exception as e:
        print(f"❌ Erreur: {e}")
