#!/usr/bin/env python3
"""
Database Manager - Gestion du cache des contacts et entreprises
Évite de rechercher plusieurs fois les mêmes informations
"""

import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Optional
import os


class DatabaseManager:
    """
    Gestionnaire de base de données pour le cache des contacts

    Structure:
    - companies: Infos de base des entreprises (Google Maps)
    - contacts: Contacts enrichis trouvés pour chaque entreprise
    - enrichment_data: Données d'enrichissement (SIRET, etc.)
    """

    def __init__(self, db_path: str = 'contacts_cache.db'):
        """
        Initialise la base de données

        Args:
            db_path: Chemin vers le fichier SQLite
        """
        self.db_path = db_path
        self.conn = None
        self._init_database()

    def _init_database(self):
        """Initialise les tables de la base de données"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row  # Pour accéder aux colonnes par nom

        cursor = self.conn.cursor()

        # Table des entreprises
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS companies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                address TEXT,
                phone TEXT,
                website TEXT,
                rating REAL,
                reviews_count INTEGER,
                category TEXT,
                google_maps_url TEXT UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Index pour recherche rapide
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_company_name
            ON companies(name)
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_company_website
            ON companies(website)
        ''')

        # Table des contacts enrichis
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS contacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_id INTEGER NOT NULL,
                contact_name TEXT,
                contact_position TEXT,
                contact_email TEXT,
                email_confidence TEXT,
                contact_linkedin TEXT,
                contact_phone TEXT,
                data_sources TEXT,  -- JSON array
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (company_id) REFERENCES companies(id)
            )
        ''')

        # Table des données d'enrichissement
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS enrichment_data (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_id INTEGER NOT NULL UNIQUE,
                siret TEXT,
                siren TEXT,
                legal_form TEXT,
                revenue TEXT,
                employees TEXT,
                creation_date TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (company_id) REFERENCES companies(id)
            )
        ''')

        # Table des scores
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                company_id INTEGER NOT NULL UNIQUE,
                score_total INTEGER,
                score_email INTEGER,
                score_contact INTEGER,
                score_company INTEGER,
                category TEXT,
                priority TEXT,
                emoji TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (company_id) REFERENCES companies(id)
            )
        ''')

        self.conn.commit()
        print(f"✅ Base de données initialisée: {self.db_path}")

    def company_exists(self, name: str, website: str = None, google_maps_url: str = None) -> Optional[int]:
        """
        Vérifie si une entreprise existe déjà dans la base

        Args:
            name: Nom de l'entreprise
            website: Site web (optionnel)
            google_maps_url: URL Google Maps (optionnel)

        Returns:
            ID de l'entreprise si elle existe, None sinon
        """
        cursor = self.conn.cursor()

        # Recherche par URL Google Maps (le plus fiable)
        if google_maps_url:
            cursor.execute(
                'SELECT id FROM companies WHERE google_maps_url = ?',
                (google_maps_url,)
            )
            result = cursor.fetchone()
            if result:
                return result['id']

        # Recherche par site web
        if website and website.strip():
            cursor.execute(
                'SELECT id FROM companies WHERE website = ? AND website != ""',
                (website,)
            )
            result = cursor.fetchone()
            if result:
                return result['id']

        # Recherche par nom exact
        cursor.execute(
            'SELECT id FROM companies WHERE name = ?',
            (name,)
        )
        result = cursor.fetchone()
        if result:
            return result['id']

        return None

    def get_company_data(self, company_id: int) -> Optional[Dict]:
        """
        Récupère toutes les données d'une entreprise (infos + contact + enrichissement + score)

        Args:
            company_id: ID de l'entreprise

        Returns:
            Dict avec toutes les données ou None
        """
        cursor = self.conn.cursor()

        # Infos de base
        cursor.execute('SELECT * FROM companies WHERE id = ?', (company_id,))
        company = cursor.fetchone()
        if not company:
            return None

        data = dict(company)

        # Contact
        cursor.execute('SELECT * FROM contacts WHERE company_id = ? ORDER BY updated_at DESC LIMIT 1', (company_id,))
        contact = cursor.fetchone()
        if contact:
            contact_data = dict(contact)
            # Convertir le JSON des sources
            if contact_data.get('data_sources'):
                try:
                    contact_data['data_sources'] = json.loads(contact_data['data_sources'])
                except:
                    contact_data['data_sources'] = []
            data.update(contact_data)

        # Enrichissement
        cursor.execute('SELECT * FROM enrichment_data WHERE company_id = ?', (company_id,))
        enrichment = cursor.fetchone()
        if enrichment:
            data.update(dict(enrichment))

        # Score
        cursor.execute('SELECT * FROM scores WHERE company_id = ?', (company_id,))
        score = cursor.fetchone()
        if score:
            data.update(dict(score))

        return data

    def save_company(self, company_data: Dict) -> int:
        """
        Sauvegarde ou met à jour une entreprise complète (infos + contact + enrichissement + score)

        Args:
            company_data: Dict avec toutes les données

        Returns:
            ID de l'entreprise
        """
        cursor = self.conn.cursor()

        # Vérifier si l'entreprise existe déjà
        company_id = self.company_exists(
            company_data.get('name', ''),
            company_data.get('website'),
            company_data.get('url')
        )

        # Préparer les timestamps
        now = datetime.now().isoformat()

        if company_id:
            # Mise à jour
            cursor.execute('''
                UPDATE companies
                SET name = ?, address = ?, phone = ?, website = ?,
                    rating = ?, reviews_count = ?, category = ?,
                    google_maps_url = ?, updated_at = ?
                WHERE id = ?
            ''', (
                company_data.get('name', ''),
                company_data.get('address', ''),
                company_data.get('phone', ''),
                company_data.get('website', ''),
                company_data.get('rating'),
                company_data.get('reviews_count'),
                company_data.get('category', ''),
                company_data.get('url', ''),
                now,
                company_id
            ))
        else:
            # Insertion
            cursor.execute('''
                INSERT INTO companies
                (name, address, phone, website, rating, reviews_count, category, google_maps_url, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                company_data.get('name', ''),
                company_data.get('address', ''),
                company_data.get('phone', ''),
                company_data.get('website', ''),
                company_data.get('rating'),
                company_data.get('reviews_count'),
                company_data.get('category', ''),
                company_data.get('url', ''),
                now,
                now
            ))
            company_id = cursor.lastrowid

        # Sauvegarder le contact si présent
        if company_data.get('contact_email') or company_data.get('contact_name'):
            self._save_contact(company_id, company_data, now)

        # Sauvegarder l'enrichissement si présent
        if any(k in company_data for k in ['siret', 'siren', 'legal_form', 'revenue', 'employees']):
            self._save_enrichment(company_id, company_data, now)

        # Sauvegarder le score si présent
        if company_data.get('score_total') is not None:
            self._save_score(company_id, company_data, now)

        self.conn.commit()
        return company_id

    def _save_contact(self, company_id: int, data: Dict, timestamp: str):
        """Sauvegarde ou met à jour un contact"""
        cursor = self.conn.cursor()

        # Convertir les sources en JSON
        sources_json = json.dumps(data.get('data_sources', []))

        # Vérifier si existe
        cursor.execute('SELECT id FROM contacts WHERE company_id = ?', (company_id,))
        exists = cursor.fetchone()

        if exists:
            cursor.execute('''
                UPDATE contacts
                SET contact_name = ?, contact_position = ?, contact_email = ?,
                    email_confidence = ?, contact_linkedin = ?, contact_phone = ?,
                    data_sources = ?, updated_at = ?
                WHERE company_id = ?
            ''', (
                data.get('contact_name', ''),
                data.get('contact_position', ''),
                data.get('contact_email', ''),
                data.get('email_confidence', ''),
                data.get('contact_linkedin', ''),
                data.get('contact_phone', ''),
                sources_json,
                timestamp,
                company_id
            ))
        else:
            cursor.execute('''
                INSERT INTO contacts
                (company_id, contact_name, contact_position, contact_email,
                 email_confidence, contact_linkedin, contact_phone, data_sources, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                company_id,
                data.get('contact_name', ''),
                data.get('contact_position', ''),
                data.get('contact_email', ''),
                data.get('email_confidence', ''),
                data.get('contact_linkedin', ''),
                data.get('contact_phone', ''),
                sources_json,
                timestamp,
                timestamp
            ))

    def _save_enrichment(self, company_id: int, data: Dict, timestamp: str):
        """Sauvegarde ou met à jour les données d'enrichissement"""
        cursor = self.conn.cursor()

        # Vérifier si existe
        cursor.execute('SELECT id FROM enrichment_data WHERE company_id = ?', (company_id,))
        exists = cursor.fetchone()

        if exists:
            cursor.execute('''
                UPDATE enrichment_data
                SET siret = ?, siren = ?, legal_form = ?, revenue = ?,
                    employees = ?, creation_date = ?, updated_at = ?
                WHERE company_id = ?
            ''', (
                data.get('siret', ''),
                data.get('siren', ''),
                data.get('legal_form', ''),
                data.get('revenue', ''),
                data.get('employees', ''),
                data.get('creation_date', ''),
                timestamp,
                company_id
            ))
        else:
            cursor.execute('''
                INSERT INTO enrichment_data
                (company_id, siret, siren, legal_form, revenue, employees, creation_date, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                company_id,
                data.get('siret', ''),
                data.get('siren', ''),
                data.get('legal_form', ''),
                data.get('revenue', ''),
                data.get('employees', ''),
                data.get('creation_date', ''),
                timestamp,
                timestamp
            ))

    def _save_score(self, company_id: int, data: Dict, timestamp: str):
        """Sauvegarde ou met à jour le score"""
        cursor = self.conn.cursor()

        # Vérifier si existe
        cursor.execute('SELECT id FROM scores WHERE company_id = ?', (company_id,))
        exists = cursor.fetchone()

        if exists:
            cursor.execute('''
                UPDATE scores
                SET score_total = ?, score_email = ?, score_contact = ?,
                    score_company = ?, category = ?, priority = ?, emoji = ?, updated_at = ?
                WHERE company_id = ?
            ''', (
                data.get('score_total'),
                data.get('score_email'),
                data.get('score_contact'),
                data.get('score_company'),
                data.get('category', ''),
                data.get('priority', ''),
                data.get('emoji', ''),
                timestamp,
                company_id
            ))
        else:
            cursor.execute('''
                INSERT INTO scores
                (company_id, score_total, score_email, score_contact, score_company,
                 category, priority, emoji, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                company_id,
                data.get('score_total'),
                data.get('score_email'),
                data.get('score_contact'),
                data.get('score_company'),
                data.get('category', ''),
                data.get('priority', ''),
                data.get('emoji', ''),
                timestamp,
                timestamp
            ))

    def get_stats(self) -> Dict:
        """
        Récupère des statistiques sur la base de données

        Returns:
            Dict avec les stats
        """
        cursor = self.conn.cursor()

        stats = {}

        # Nombre d'entreprises
        cursor.execute('SELECT COUNT(*) as count FROM companies')
        stats['total_companies'] = cursor.fetchone()['count']

        # Nombre de contacts avec email
        cursor.execute('SELECT COUNT(*) as count FROM contacts WHERE contact_email != ""')
        stats['companies_with_email'] = cursor.fetchone()['count']

        # Nombre enrichis
        cursor.execute('SELECT COUNT(*) as count FROM enrichment_data')
        stats['companies_enriched'] = cursor.fetchone()['count']

        # Score moyen
        cursor.execute('SELECT AVG(score_total) as avg FROM scores WHERE score_total IS NOT NULL')
        result = cursor.fetchone()
        stats['average_score'] = round(result['avg'], 1) if result['avg'] else 0

        return stats

    def close(self):
        """Ferme la connexion à la base de données"""
        if self.conn:
            self.conn.close()

    def __enter__(self):
        """Support pour le context manager"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Fermeture automatique avec context manager"""
        self.close()


# Test rapide
if __name__ == "__main__":
    print("\n🧪 Test du DatabaseManager\n")

    # Créer une base de test
    db = DatabaseManager('test_cache.db')

    # Test: Sauvegarder une entreprise
    test_company = {
        'name': 'Test Company',
        'address': '123 Rue Test',
        'phone': '0123456789',
        'website': 'https://test.com',
        'rating': 4.5,
        'reviews_count': 100,
        'category': 'Test',
        'url': 'https://maps.google.com/test',
        'contact_name': 'Jean Dupont',
        'contact_email': 'jean@test.com',
        'email_confidence': 'high',
        'contact_position': 'Gérant',
        'siret': '12345678900001',
        'score_total': 85,
        'score_email': 35,
        'score_contact': 25,
        'score_company': 25,
        'category': '🟢 Premium',
        'data_sources': ['Google Maps', 'Hunter.io']
    }

    company_id = db.save_company(test_company)
    print(f"✅ Entreprise sauvegardée avec ID: {company_id}")

    # Test: Vérifier si existe
    exists = db.company_exists('Test Company', 'https://test.com')
    print(f"✅ Entreprise existe: {exists == company_id}")

    # Test: Récupérer les données
    data = db.get_company_data(company_id)
    print(f"✅ Données récupérées: {data.get('name')}")

    # Stats
    stats = db.get_stats()
    print(f"\n📊 Stats:")
    for key, value in stats.items():
        print(f"   {key}: {value}")

    db.close()

    # Nettoyer
    os.remove('test_cache.db')
    print("\n✅ Test terminé avec succès")
