#!/usr/bin/env python3
"""
Google Maps Scraper avec Apify
Scrape des entreprises depuis Google Maps, trouve leurs contacts et les envoie vers Google Sheets et GoHighLevel
"""

import os
import time
from datetime import datetime
from dotenv import load_dotenv
from apify_client import ApifyClient
import gspread
from google.oauth2.service_account import Credentials
import requests
import json
from email_finder import EmailFinder

# Charger les variables d'environnement
load_dotenv()

class GoogleMapsScraper:
    def __init__(self):
        """Initialise le scraper avec les clés API"""
        self.apify_token = os.getenv('APIFY_API_TOKEN')
        self.google_sheet_id = os.getenv('GOOGLE_SHEET_ID')
        self.ghl_api_key = os.getenv('GOHIGHLEVEL_API_KEY')
        self.ghl_location_id = os.getenv('GOHIGHLEVEL_LOCATION_ID')
        self.hunter_api_key = os.getenv('HUNTER_API_KEY')
        
        # Vérifier les clés essentielles
        if not self.apify_token:
            raise ValueError("APIFY_API_TOKEN manquant dans .env")
        if not self.google_sheet_id:
            raise ValueError("GOOGLE_SHEET_ID manquant dans .env")
        
        # Initialiser les clients
        self.apify_client = ApifyClient(self.apify_token)
        self.google_sheet = None
        self.email_finder = EmailFinder()
        self._init_google_sheets()
        
    def _init_google_sheets(self):
        """Initialise la connexion Google Sheets"""
        try:
            # Définir les scopes nécessaires
            scopes = [
                'https://www.googleapis.com/auth/spreadsheets',
                'https://www.googleapis.com/auth/drive'
            ]
            
            # Charger les credentials
            creds = Credentials.from_service_account_file(
                'credentials.json',
                scopes=scopes
            )
            
            # Autoriser gspread
            gc = gspread.authorize(creds)
            
            # Ouvrir le Google Sheet
            self.google_sheet = gc.open_by_key(self.google_sheet_id)
            
            # Créer ou récupérer la première feuille
            try:
                worksheet = self.google_sheet.worksheet('Entreprises')
            except:
                worksheet = self.google_sheet.add_worksheet('Entreprises', rows=1000, cols=12)
                # Ajouter les en-têtes
                headers = [
                    'Nom', 'Adresse', 'Téléphone', 'Site Web', 'Note', 
                    'Nombre Avis', 'Catégorie', 'Nom Contact', 'Email Contact', 
                    'Confiance Email', 'Poste Contact', 'Date Ajout', 'URL Google Maps'
                ]
                worksheet.append_row(headers)
            
            print("✅ Connexion Google Sheets établie")
            
        except FileNotFoundError:
            print("⚠️  Fichier credentials.json non trouvé. Google Sheets désactivé.")
            print("   Suivez les instructions du README pour configurer Google Sheets.")
        except Exception as e:
            print(f"⚠️  Erreur lors de l'initialisation Google Sheets: {e}")
    
    def scrape_google_maps(self, search_query, max_results=50):
        """
        Scrape Google Maps via Apify
        
        Args:
            search_query: La recherche à effectuer (ex: "restaurants à Paris")
            max_results: Nombre maximum de résultats (défaut: 50)
        
        Returns:
            Liste des entreprises trouvées
        """
        print(f"🔍 Recherche en cours: '{search_query}'")
        print(f"📊 Nombre de résultats demandés: {max_results}")
        
        # Configuration de l'Actor Apify pour Google Maps
        # Utilise l'actor officiel: compass/crawler-google-places
        run_input = {
            "searchStringsArray": [search_query],
            "maxCrawledPlacesPerSearch": max_results,
            "language": "fr",
            "deeperCityScrape": False,
            "scrapeReviewerName": False,
            "scrapeReviewerId": False,
            "scrapeReviewId": False,
            "scrapeReviewUrl": False,
            "scrapeResponseFromOwnerText": False,
            "scrapeReviewsPersonalData": False,
        }
        
        try:
            # Lancer l'actor
            print("🚀 Lancement du scraping Apify...")
            run = self.apify_client.actor("compass/crawler-google-places").call(run_input=run_input)
            
            # Récupérer les résultats
            print("📥 Récupération des résultats...")
            results = []
            for item in self.apify_client.dataset(run["defaultDatasetId"]).iterate_items():
                results.append(item)
            
            print(f"✅ {len(results)} entreprises trouvées")
            return results
            
        except Exception as e:
            print(f"❌ Erreur lors du scraping: {e}")
            return []
    
    def find_contact_info(self, company_name, website=None):
        """
        Trouve les informations de contact d'une entreprise
        Scrape le site web et génère des patterns d'emails intelligents
        
        Args:
            company_name: Nom de l'entreprise
            website: Site web de l'entreprise (optionnel)
        
        Returns:
            Dict avec nom, email, poste du contact
        """
        contact_info = {
            'name': '',
            'email': '',
            'position': 'Gérant',
            'email_confidence': 'low'
        }
        
        # Utiliser le nouveau EmailFinder
        result = self.email_finder.find_contact_email(company_name, website)
        contact_info['email'] = result['email']
        contact_info['email_confidence'] = result['confidence']
        
        # Essayer de trouver le nom du gérant
        if website:
            manager_name = self.email_finder.find_manager_name(company_name, website)
            if manager_name:
                contact_info['name'] = manager_name
                contact_info['position'] = 'Gérant'
        
        return contact_info
    
    def save_to_google_sheets(self, businesses_data):
        """
        Sauvegarde les données dans Google Sheets
        
        Args:
            businesses_data: Liste de dicts contenant les infos des entreprises
        """
        if not self.google_sheet:
            print("⚠️  Google Sheets non configuré, saut de cette étape")
            return
        
        try:
            worksheet = self.google_sheet.worksheet('Entreprises')
            
            print(f"📝 Ajout de {len(businesses_data)} entreprises dans Google Sheets...")
            
            for business in businesses_data:
                row = [
                    business.get('name', ''),
                    business.get('address', ''),
                    business.get('phone', ''),
                    business.get('website', ''),
                    business.get('rating', ''),
                    business.get('reviews_count', ''),
                    business.get('category', ''),
                    business.get('contact_name', ''),
                    business.get('contact_email', ''),
                    business.get('email_confidence', 'low'),
                    business.get('contact_position', ''),
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    business.get('url', '')
                ]
                worksheet.append_row(row)
                time.sleep(0.5)  # Éviter de dépasser les limites d'API
            
            print("✅ Données ajoutées à Google Sheets")
            
        except Exception as e:
            print(f"❌ Erreur lors de l'ajout à Google Sheets: {e}")
    
    def send_to_gohighlevel(self, businesses_data):
        """
        Envoie les contacts vers GoHighLevel
        
        Args:
            businesses_data: Liste de dicts contenant les infos des entreprises
        """
        # Vérifier si GoHighLevel est configuré avec une vraie API key
        if (not self.ghl_api_key or 
            not self.ghl_location_id or 
            self.ghl_api_key == 'your_gohighlevel_api_key_here'):
            print("⚠️  GoHighLevel non configuré, saut de cette étape")
            print("   Configurez GOHIGHLEVEL_API_KEY dans .env pour activer cette fonctionnalité")
            return
        
        print(f"📤 Envoi de {len(businesses_data)} contacts vers GoHighLevel...")
        
        url = "https://rest.gohighlevel.com/v1/contacts/"
        headers = {
            "Authorization": f"Bearer {self.ghl_api_key}",
            "Content-Type": "application/json"
        }
        
        success_count = 0
        
        for business in businesses_data:
            try:
                # Préparer les données pour GoHighLevel
                contact_data = {
                    "locationId": self.ghl_location_id,
                    "firstName": business.get('contact_name', '').split()[0] if business.get('contact_name') else business.get('name', ''),
                    "lastName": ' '.join(business.get('contact_name', '').split()[1:]) if business.get('contact_name') and len(business.get('contact_name', '').split()) > 1 else '',
                    "email": business.get('contact_email', ''),
                    "phone": business.get('phone', ''),
                    "companyName": business.get('name', ''),
                    "website": business.get('website', ''),
                    "address1": business.get('address', ''),
                    "customFields": [
                        {
                            "key": "google_maps_rating",
                            "value": str(business.get('rating', ''))
                        },
                        {
                            "key": "google_maps_url",
                            "value": business.get('url', '')
                        },
                        {
                            "key": "category",
                            "value": business.get('category', '')
                        },
                        {
                            "key": "position",
                            "value": business.get('contact_position', '')
                        }
                    ],
                    "tags": ["Google Maps Scraper", "Lead"]
                }
                
                # Envoyer la requête
                response = requests.post(url, headers=headers, json=contact_data, timeout=10)
                
                if response.status_code in [200, 201]:
                    success_count += 1
                else:
                    print(f"⚠️  Erreur pour {business.get('name')}: {response.status_code}")
                
                time.sleep(0.5)  # Rate limiting
                
            except Exception as e:
                print(f"❌ Erreur lors de l'envoi de {business.get('name')}: {e}")
        
        print(f"✅ {success_count}/{len(businesses_data)} contacts envoyés à GoHighLevel")
    
    def process_results(self, results):
        """
        Traite les résultats d'Apify et enrichit avec les contacts
        
        Args:
            results: Résultats bruts d'Apify
        
        Returns:
            Liste enrichie avec les informations de contact
        """
        processed_data = []
        
        print(f"🔄 Traitement et enrichissement de {len(results)} entreprises...")
        
        for idx, result in enumerate(results, 1):
            print(f"  [{idx}/{len(results)}] Traitement de {result.get('title', 'N/A')}...")
            
            # Extraire les données de base
            business = {
                'name': result.get('title', ''),
                'address': result.get('address', ''),
                'phone': result.get('phone', ''),
                'website': result.get('website', ''),
                'rating': result.get('totalScore', ''),
                'reviews_count': result.get('reviewsCount', ''),
                'category': result.get('categoryName', ''),
                'url': result.get('url', ''),
            }
            
            # Chercher les informations de contact
            contact = self.find_contact_info(
                business['name'],
                business['website']
            )
            
            business['contact_name'] = contact['name']
            business['contact_email'] = contact['email']
            business['email_confidence'] = contact.get('email_confidence', 'low')
            business['contact_position'] = contact['position']
            
            processed_data.append(business)
        
        print("✅ Traitement terminé")
        return processed_data
    
    def run(self, search_query, max_results=50):
        """
        Exécute le pipeline complet
        
        Args:
            search_query: Recherche à effectuer
            max_results: Nombre de résultats (défaut: 50)
        """
        print("\n" + "="*60)
        print("🗺️  GOOGLE MAPS SCRAPER - Démarrage")
        print("="*60 + "\n")
        
        # 1. Scraper Google Maps
        results = self.scrape_google_maps(search_query, max_results)
        
        if not results:
            print("❌ Aucun résultat trouvé. Arrêt du processus.")
            return
        
        # 2. Traiter et enrichir les résultats
        processed_data = self.process_results(results)
        
        # 3. Sauvegarder dans Google Sheets
        self.save_to_google_sheets(processed_data)
        
        # 4. Envoyer vers GoHighLevel
        self.send_to_gohighlevel(processed_data)
        
        print("\n" + "="*60)
        print("✅ PROCESSUS TERMINÉ AVEC SUCCÈS")
        print("="*60 + "\n")
        print(f"📊 Résumé:")
        print(f"   - Entreprises scrapées: {len(results)}")
        print(f"   - Entreprises traitées: {len(processed_data)}")
        print(f"   - Avec contacts trouvés: {sum(1 for b in processed_data if b['contact_email'])}")


def main():
    """Fonction principale"""
    print("\n🚀 Google Maps Scraper avec Apify\n")
    
    # Demander les paramètres à l'utilisateur
    search_query = input("🔍 Entrez votre recherche (ex: 'restaurants à Paris'): ").strip()
    
    if not search_query:
        print("❌ Recherche vide. Arrêt du programme.")
        return
    
    max_results_input = input("📊 Nombre d'entreprises à scraper [50]: ").strip()
    max_results = int(max_results_input) if max_results_input else 50
    
    try:
        # Créer et exécuter le scraper
        scraper = GoogleMapsScraper()
        scraper.run(search_query, max_results)
        
    except Exception as e:
        print(f"\n❌ Erreur fatale: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
