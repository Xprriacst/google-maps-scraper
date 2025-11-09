# Google Maps Scraper avec Apify

Scraper automatisé qui extrait des entreprises depuis Google Maps via Apify, trouve leurs contacts clés et les envoie vers Google Sheets et GoHighLevel.

## Fonctionnalités

- ✅ Scraping de 50 entreprises depuis Google Maps via Apify
- ✅ Export automatique vers Google Sheets
- ✅ Recherche de contacts clés (gérants) sur internet
- ✅ Envoi vers l'API GoHighLevel

## Installation

1. Installer les dépendances :
```bash
pip install -r requirements.txt
```

2. Configurer les variables d'environnement :
```bash
cp .env.example .env
```

3. Compléter le fichier `.env` avec vos clés API :
   - **APIFY_API_TOKEN** : Votre token API Apify (https://console.apify.com/account/integrations)
   - **GOOGLE_SHEET_ID** : L'ID de votre Google Sheet
   - **GOHIGHLEVEL_API_KEY** : Votre clé API GoHighLevel
   - **GOHIGHLEVEL_LOCATION_ID** : Votre Location ID GoHighLevel
   - **HUNTER_API_KEY** : (Optionnel) Votre clé API Hunter.io pour la recherche de contacts

4. Configurer Google Sheets :
   - Créer un projet dans Google Cloud Console
   - Activer l'API Google Sheets
   - Télécharger le fichier `credentials.json` et le placer à la racine du projet

## Utilisation

```bash
python scraper.py
```

Le script vous demandera :
- La recherche à effectuer (ex: "restaurants à Paris")
- Le nombre d'entreprises à scraper (par défaut: 50)

## Structure des données

Le Google Sheet contiendra les colonnes suivantes :
- Nom de l'entreprise
- Adresse
- Téléphone
- Site web
- Note
- Nombre d'avis
- Catégorie
- Nom du contact
- Email du contact
- Poste du contact
- Date d'ajout

## APIs utilisées

- **Apify** : Scraping Google Maps
- **Google Sheets API** : Stockage des données
- **Hunter.io** : Recherche d'emails (optionnel)
- **GoHighLevel API** : CRM Integration
