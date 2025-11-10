#!/usr/bin/env python3
"""
Module d'export vers Google Sheets pour sauvegarder l'historique des prospections
"""

import json
from datetime import datetime
from typing import List, Dict, Optional
import pandas as pd

try:
    import gspread
    from gspread.exceptions import SpreadsheetNotFound, WorksheetNotFound
    from oauth2client.service_account import ServiceAccountCredentials
    GSPREAD_AVAILABLE = True
except ImportError:
    GSPREAD_AVAILABLE = False
    print("⚠️  gspread non installé. Installez avec: pip install gspread oauth2client")


class GoogleSheetsExporter:
    """Gestionnaire d'export vers Google Sheets"""

    def __init__(self, credentials_json: str, spreadsheet_name: str = "Prospection B2B - Historique"):
        """
        Initialise l'exporteur Google Sheets

        Args:
            credentials_json: JSON string des credentials du service account
            spreadsheet_name: Nom du Google Sheet (sera créé s'il n'existe pas)
        """
        if not GSPREAD_AVAILABLE:
            raise ImportError("gspread n'est pas installé")

        self.spreadsheet_name = spreadsheet_name
        self.client = None
        self.spreadsheet = None

        try:
            # Définir les scopes nécessaires
            scope = [
                'https://spreadsheets.google.com/feeds',
                'https://www.googleapis.com/auth/drive'
            ]

            # Parser le JSON
            creds_dict = json.loads(credentials_json)

            # Créer les credentials
            credentials = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)

            # Autoriser le client
            self.client = gspread.authorize(credentials)

            print(f"✅ Connecté à Google Sheets")

        except json.JSONDecodeError as e:
            raise ValueError(f"Format JSON invalide pour les credentials: {e}")
        except Exception as e:
            raise Exception(f"Erreur d'authentification Google Sheets: {e}")

    def get_or_create_spreadsheet(self) -> gspread.Spreadsheet:
        """
        Récupère le spreadsheet ou le crée s'il n'existe pas

        Returns:
            L'objet Spreadsheet
        """
        try:
            # Essayer d'ouvrir le spreadsheet existant
            self.spreadsheet = self.client.open(self.spreadsheet_name)
            print(f"📊 Spreadsheet '{self.spreadsheet_name}' trouvé")
        except SpreadsheetNotFound:
            # Créer un nouveau spreadsheet
            self.spreadsheet = self.client.create(self.spreadsheet_name)
            print(f"📊 Nouveau spreadsheet '{self.spreadsheet_name}' créé")

            # Initialiser avec les en-têtes
            self._initialize_worksheet()

        return self.spreadsheet

    def _initialize_worksheet(self):
        """Initialise la première feuille avec les en-têtes"""
        try:
            worksheet = self.spreadsheet.get_worksheet(0)
            worksheet.update_title("Prospections")

            # En-têtes
            headers = [
                'Date/Heure',
                'Requête',
                'Score',
                'Catégorie',
                'Source Contact',
                'Taille',
                'Entreprise',
                'Contact 1',
                'Fonction 1',
                'Email 1',
                'Téléphone 1',
                'LinkedIn 1',
                'Confidence 1',
                'Contact 2',
                'Fonction 2',
                'Email 2',
                'Téléphone 2',
                'LinkedIn 2',
                'Confidence 2',
                'Contact 3',
                'Fonction 3',
                'Email 3',
                'Téléphone 3',
                'LinkedIn 3',
                'Confidence 3',
                'Téléphone Entreprise',
                'Site Web',
                'Note',
                'Avis',
                'Effectifs',
                'SIRET',
                'Adresse',
                'Ville',
                'Code Postal'
            ]

            # Mettre les en-têtes en gras
            worksheet.update('A1:AH1', [headers])
            worksheet.format('A1:AH1', {
                'textFormat': {'bold': True},
                'backgroundColor': {'red': 0.9, 'green': 0.9, 'blue': 0.9}
            })

            print("✅ Feuille initialisée avec les en-têtes")

        except Exception as e:
            print(f"⚠️  Erreur lors de l'initialisation de la feuille: {e}")

    def export_prospection(self, search_query: str, contacts: List[Dict]) -> bool:
        """
        Exporte une prospection vers Google Sheets

        Args:
            search_query: La requête de recherche utilisée
            contacts: Liste des contacts enrichis

        Returns:
            True si succès, False sinon
        """
        try:
            # S'assurer que le spreadsheet existe
            if not self.spreadsheet:
                self.get_or_create_spreadsheet()

            # Récupérer la première feuille
            worksheet = self.spreadsheet.get_worksheet(0)

            # Préparer les données
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            rows = []
            for contact in contacts:
                row = [
                    timestamp,
                    search_query,
                    contact.get('score_total', 0),
                    contact.get('category', ''),
                    self._get_contact_source(contact),
                    self._get_company_size(contact),
                    contact.get('name', ''),
                    # Contact 1
                    contact.get('contact_1_name', ''),
                    contact.get('contact_1_position', ''),
                    contact.get('contact_1_email', ''),
                    contact.get('contact_1_phone', ''),
                    contact.get('contact_1_linkedin', ''),
                    contact.get('contact_1_email_confidence', ''),
                    # Contact 2
                    contact.get('contact_2_name', ''),
                    contact.get('contact_2_position', ''),
                    contact.get('contact_2_email', ''),
                    contact.get('contact_2_phone', ''),
                    contact.get('contact_2_linkedin', ''),
                    contact.get('contact_2_email_confidence', ''),
                    # Contact 3
                    contact.get('contact_3_name', ''),
                    contact.get('contact_3_position', ''),
                    contact.get('contact_3_email', ''),
                    contact.get('contact_3_phone', ''),
                    contact.get('contact_3_linkedin', ''),
                    contact.get('contact_3_email_confidence', ''),
                    # Autres infos
                    contact.get('phone', ''),
                    contact.get('website', ''),
                    contact.get('rating', ''),
                    contact.get('reviews_count', ''),
                    contact.get('employees', ''),
                    contact.get('siret', ''),
                    contact.get('address', ''),
                    contact.get('city', ''),
                    contact.get('postal_code', '')
                ]
                rows.append(row)

            # Ajouter les lignes (append)
            if rows:
                worksheet.append_rows(rows, value_input_option='USER_ENTERED')
                print(f"✅ {len(rows)} contacts exportés vers Google Sheets")
                return True
            else:
                print("⚠️  Aucun contact à exporter")
                return False

        except Exception as e:
            print(f"❌ Erreur lors de l'export vers Google Sheets: {e}")
            import traceback
            traceback.print_exc()
            return False

    def _get_contact_source(self, contact: Dict) -> str:
        """Détermine la source du contact"""
        sources = contact.get('data_sources', [])
        if not sources:
            return '❌'

        if 'apollo' in sources:
            return '🚀 Apollo'
        elif 'dropcontact' in sources:
            return '💧 Dropcontact'
        elif 'legal_manager' in sources:
            return '⚖️ Gérant légal'
        else:
            return '❓ Autre'

    def _get_company_size(self, contact: Dict) -> str:
        """Détermine la taille de l'entreprise"""
        employees_str = str(contact.get('employees', '')).strip()

        if not employees_str or employees_str == 'N/A':
            return '❓ Inconnu'

        try:
            employees = int(employees_str.replace('+', '').replace(',', ''))

            if employees <= 10:
                return '🔵 TPE (≤10)'
            elif employees <= 250:
                return '🟢 PME (11-250)'
            elif employees <= 5000:
                return '🟡 ETI (251-5000)'
            else:
                return '🔴 GE (5000+)'
        except (ValueError, AttributeError):
            return '❓ Inconnu'

    def get_spreadsheet_url(self) -> Optional[str]:
        """
        Retourne l'URL du spreadsheet

        Returns:
            URL du spreadsheet ou None
        """
        if self.spreadsheet:
            return self.spreadsheet.url
        return None

    def get_stats(self) -> Dict:
        """
        Récupère les statistiques du spreadsheet

        Returns:
            Dict avec nombre total de lignes, etc.
        """
        try:
            if not self.spreadsheet:
                self.get_or_create_spreadsheet()

            worksheet = self.spreadsheet.get_worksheet(0)
            all_values = worksheet.get_all_values()

            return {
                'total_rows': len(all_values) - 1,  # -1 pour les en-têtes
                'spreadsheet_url': self.spreadsheet.url,
                'last_update': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        except Exception as e:
            print(f"Erreur lors de la récupération des stats: {e}")
            return {}


def test_connection(credentials_json: str) -> bool:
    """
    Teste la connexion à Google Sheets

    Args:
        credentials_json: JSON string des credentials

    Returns:
        True si la connexion fonctionne
    """
    try:
        exporter = GoogleSheetsExporter(credentials_json)
        exporter.get_or_create_spreadsheet()
        print("✅ Test de connexion réussi")
        return True
    except Exception as e:
        print(f"❌ Échec du test de connexion: {e}")
        return False
