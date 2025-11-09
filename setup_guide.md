# Guide de Configuration - Google Maps Scraper

Ce guide vous aide à configurer toutes les APIs nécessaires pour le scraper.

## 1. Configuration Apify (Obligatoire) ✅

### Étape 1: Créer un compte Apify
1. Allez sur [https://apify.com/](https://apify.com/)
2. Créez un compte gratuit (100$ de crédit gratuit)

### Étape 2: Obtenir votre API Token
1. Connectez-vous à [https://console.apify.com/](https://console.apify.com/)
2. Allez dans **Settings** > **Integrations**
3. Copiez votre **API Token**
4. Ajoutez-le dans le fichier `.env` :
   ```
   APIFY_API_TOKEN=votre_token_ici
   ```

## 2. Configuration Google Sheets (Obligatoire) ✅

### Étape 1: Créer un projet Google Cloud
1. Allez sur [https://console.cloud.google.com/](https://console.cloud.google.com/)
2. Créez un nouveau projet ou sélectionnez un projet existant
3. Notez le nom de votre projet

### Étape 2: Activer les APIs nécessaires
1. Dans le menu, allez dans **APIs & Services** > **Library**
2. Recherchez et activez :
   - **Google Sheets API**
   - **Google Drive API**

### Étape 3: Créer un compte de service
1. Allez dans **APIs & Services** > **Credentials**
2. Cliquez sur **Create Credentials** > **Service Account**
3. Donnez un nom au compte (ex: "google-maps-scraper")
4. Cliquez sur **Create and Continue**
5. Sélectionnez le rôle **Editor** 
6. Cliquez sur **Done**

### Étape 4: Générer la clé JSON
1. Cliquez sur le compte de service que vous venez de créer
2. Allez dans l'onglet **Keys**
3. Cliquez sur **Add Key** > **Create new key**
4. Sélectionnez **JSON**
5. Téléchargez le fichier et renommez-le `credentials.json`
6. Placez-le à la racine du projet (même dossier que scraper.py)

### Étape 5: Créer un Google Sheet et partager
1. Créez un nouveau Google Sheet
2. Copiez l'ID du Sheet depuis l'URL :
   ```
   https://docs.google.com/spreadsheets/d/VOTRE_SHEET_ID/edit
   ```
3. Ajoutez l'ID dans le fichier `.env` :
   ```
   GOOGLE_SHEET_ID=votre_sheet_id_ici
   ```
4. **Important** : Partagez le Google Sheet avec l'email du compte de service
   - L'email se trouve dans le fichier `credentials.json` : champ `client_email`
   - Donnez-lui les droits **Éditeur**

## 3. Configuration GoHighLevel (Obligatoire) ✅

### Étape 1: Obtenir votre API Key
1. Connectez-vous à votre compte GoHighLevel
2. Allez dans **Settings** > **API Keys**
3. Créez une nouvelle clé API ou utilisez une existante
4. Copiez la clé

### Étape 2: Obtenir votre Location ID
1. Dans GoHighLevel, allez dans **Settings** > **Business Profile**
2. Copiez votre **Location ID**

### Étape 3: Configurer les variables
Ajoutez dans le fichier `.env` :
```
GOHIGHLEVEL_API_KEY=votre_api_key_ici
GOHIGHLEVEL_LOCATION_ID=votre_location_id_ici
```

### Étape 4: Créer les champs personnalisés (Optionnel mais recommandé)
Dans GoHighLevel, créez les champs personnalisés suivants :
- `google_maps_rating` (Texte)
- `google_maps_url` (URL)
- `category` (Texte)
- `position` (Texte)

## 4. Configuration Hunter.io (Optionnel) 🔍

Hunter.io permet de trouver les emails professionnels des contacts.

### Étape 1: Créer un compte
1. Allez sur [https://hunter.io/](https://hunter.io/)
2. Créez un compte (plan gratuit disponible avec 50 recherches/mois)

### Étape 2: Obtenir votre API Key
1. Allez dans **Settings** > **API**
2. Copiez votre **API Key**
3. Ajoutez-la dans le fichier `.env` :
   ```
   HUNTER_API_KEY=votre_hunter_key_ici
   ```

**Note** : Sans Hunter.io, le scraper utilisera des patterns d'emails génériques (contact@domain.com)

## 5. Vérification de la configuration

Créez un fichier `.env` à la racine avec toutes vos clés :

```env
# Apify (Obligatoire)
APIFY_API_TOKEN=apify_api_xxxxxxxxxxxxxxxxxxxxxxxxx

# Google Sheets (Obligatoire)
GOOGLE_SHEET_ID=1ABC-xyz123_xxxxxxxxxxxxxxxxx

# GoHighLevel (Obligatoire)
GOHIGHLEVEL_API_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
GOHIGHLEVEL_LOCATION_ID=abc123xyz456

# Hunter.io (Optionnel)
HUNTER_API_KEY=abcdef123456789
```

## 6. Installation et test

```bash
# Installer les dépendances
pip install -r requirements.txt

# Lancer le scraper
python scraper.py
```

## Dépannage

### Erreur "APIFY_API_TOKEN manquant"
- Vérifiez que votre fichier `.env` existe
- Vérifiez que la variable est bien définie dans `.env`

### Erreur "credentials.json non trouvé"
- Téléchargez le fichier JSON depuis Google Cloud Console
- Placez-le à la racine du projet
- Renommez-le exactement `credentials.json`

### Erreur "Permission denied" sur Google Sheets
- Vérifiez que vous avez partagé le Sheet avec l'email du compte de service
- L'email se trouve dans `credentials.json` : `client_email`

### Erreur GoHighLevel
- Vérifiez que votre API Key est valide
- Vérifiez que votre Location ID est correct
- Assurez-vous que l'API Key a les permissions nécessaires

## Support

Pour plus d'aide :
- Apify : [https://docs.apify.com/](https://docs.apify.com/)
- Google Sheets API : [https://developers.google.com/sheets/api](https://developers.google.com/sheets/api)
- GoHighLevel : [https://highlevel.stoplight.io/](https://highlevel.stoplight.io/)
- Hunter.io : [https://hunter.io/api-documentation](https://hunter.io/api-documentation)
