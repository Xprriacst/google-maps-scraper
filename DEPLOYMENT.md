# Guide de déploiement Streamlit Cloud

Ce guide explique comment déployer l'application Scraper Pro sur Streamlit Cloud (gratuit).

## 🚀 Déploiement en 5 minutes

### Étape 1 : Préparer le repository GitHub

1. Assurez-vous que votre code est poussé sur GitHub
2. Le repository doit contenir :
   - `app_streamlit_pro.py`
   - `requirements.txt`
   - `contact_enricher.py`
   - `contact_scorer.py`
   - `scraper_pro.py`
   - `email_finder.py`
   - `.streamlit/config.toml`

### Étape 2 : Créer un compte Streamlit Cloud

1. Allez sur https://share.streamlit.io/
2. Connectez-vous avec votre compte GitHub
3. Autorisez Streamlit à accéder à vos repositories

### Étape 3 : Déployer l'application

1. Cliquez sur "New app"
2. Sélectionnez votre repository : `google-maps-scraper`
3. Choisissez la branche : `main` ou votre branche actuelle
4. Fichier principal : `app_streamlit_pro.py`
5. Cliquez sur "Deploy!"

### Étape 4 : Configurer les secrets

1. Une fois l'app déployée, cliquez sur "⋮" (menu) → "Settings" → "Secrets"
2. Ajoutez vos secrets au format TOML :

```toml
APIFY_API_TOKEN = "votre_token_apify"
GOOGLE_SHEET_ID = "votre_sheet_id"
```

3. Pour Google Sheets, vous devez aussi ajouter le contenu de `credentials.json` :

```toml
[gcp_service_account]
type = "service_account"
project_id = "votre-project-id"
private_key_id = "votre-private-key-id"
private_key = "-----BEGIN PRIVATE KEY-----\nVOTRE_CLE_PRIVEE\n-----END PRIVATE KEY-----\n"
client_email = "votre-service-account@votre-project.iam.gserviceaccount.com"
client_id = "votre-client-id"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "votre-cert-url"
```

4. Sauvegardez les secrets

### Étape 5 : Modifier le code pour utiliser les secrets Streamlit

Dans `scraper_pro.py` et `contact_enricher.py`, modifiez la récupération des variables d'environnement :

```python
import streamlit as st
import os

# Essayer d'abord Streamlit secrets, puis .env
def get_env(key, default=None):
    try:
        return st.secrets[key]
    except:
        return os.getenv(key, default)

# Utiliser ensuite
apify_token = get_env('APIFY_API_TOKEN')
```

### Étape 6 : Tester votre application

1. Streamlit va redémarrer automatiquement
2. Accédez à votre app via l'URL fournie (ex: `https://votre-app.streamlit.app`)
3. Testez une prospection !

## 🎯 Fonctionnalités de l'app déployée

- ✅ Interface web moderne et responsive
- ✅ Scraping Google Maps en temps réel
- ✅ Enrichissement intelligent des contacts
- ✅ Scoring automatique (0-100)
- ✅ Visualisations interactives (graphiques, tableaux)
- ✅ Filtres dynamiques
- ✅ Export CSV
- ✅ Accessible depuis n'importe où

## 💡 Conseils

### Optimisation des performances

- Limitez le nombre d'entreprises en production (max 50-100 pour éviter les timeouts)
- Streamlit Cloud a une limite de 1 Go de RAM
- Pour des volumes importants, utilisez un déploiement local ou serveur dédié

### Sécurité

- Ne commitez JAMAIS vos secrets dans Git
- Utilisez toujours Streamlit Secrets pour la production
- Ajoutez `.streamlit/secrets.toml` au `.gitignore`

### Mise à jour

- Pour mettre à jour l'app, il suffit de pusher sur GitHub
- Streamlit Cloud redéploiera automatiquement

## 🐛 Dépannage

### L'app ne démarre pas

1. Vérifiez les logs dans Streamlit Cloud
2. Assurez-vous que `requirements.txt` contient toutes les dépendances
3. Vérifiez que les secrets sont correctement configurés

### Timeout lors de l'enrichissement

- Réduisez le nombre d'entreprises à scraper
- L'enrichissement peut prendre du temps (30-60 min pour 200 entreprises)

### Erreur Google Sheets

- Vérifiez que le service account a accès au Google Sheet
- Vérifiez que les secrets GCP sont correctement configurés

## 📚 Ressources

- [Documentation Streamlit Cloud](https://docs.streamlit.io/streamlit-community-cloud)
- [Gestion des secrets](https://docs.streamlit.io/streamlit-community-cloud/get-started/deploy-an-app/connect-to-data-sources/secrets-management)
- [Limites de Streamlit Cloud](https://docs.streamlit.io/streamlit-community-cloud/get-started/limitations)

## 🆓 Alternative : Déploiement local

Si vous préférez tester en local :

```bash
streamlit run app_streamlit_pro.py
```

L'app sera accessible sur http://localhost:8501
