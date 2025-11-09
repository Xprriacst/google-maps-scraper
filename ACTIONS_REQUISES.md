# ⚠️ Actions Requises pour Finaliser la Configuration

## ✅ Ce qui fonctionne déjà
- **Apify** : Connecté avec succès ✅
- **Hunter.io** : Non configuré (optionnel) - Le scraper utilisera des emails génériques

## ❌ Ce qui nécessite votre action

### 1. Google Sheets - Partager le document (URGENT)

Le service account n'a pas accès à votre Google Sheet.

**Action à faire :**
1. Ouvrez votre Google Sheet : https://docs.google.com/spreadsheets/d/1AiZrgPbrPmyIVAOZrnAIT7iKmKl2BE0hPGEBypQtcdo/edit
2. Cliquez sur le bouton **"Partager"** (en haut à droite)
3. Ajoutez cette adresse email :
   ```
   g-maps-scraper@g-maps-scraper-477617.iam.gserviceaccount.com
   ```
4. Donnez-lui les droits **"Éditeur"**
5. Cliquez sur **"Envoyer"**

### 2. GoHighLevel - API Key manquante (URGENT)

Vous avez fourni le Location ID mais pas l'API Key.

**Action à faire :**
1. Connectez-vous à votre compte GoHighLevel
2. Allez dans **Settings** > **API Keys** ou **Integrations**
3. Créez une nouvelle clé API ou copiez une existante
4. Ouvrez le fichier `.env` dans ce dossier
5. Remplacez `your_gohighlevel_api_key_here` par votre vraie clé API

**Exemple dans le fichier `.env` :**
```env
GOHIGHLEVEL_API_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.votre_vraie_cle_ici
```

## 🧪 Tester à nouveau

Une fois ces 2 actions effectuées, relancez le test :

```bash
python3 test_config.py
```

Vous devriez voir tous les services en ✅

## 🚀 Lancer le scraper

Quand tous les tests sont OK, lancez le scraper :

```bash
python3 scraper.py
```

---

## 📝 Résumé rapide

- [ ] Partager le Google Sheet avec `g-maps-scraper@g-maps-scraper-477617.iam.gserviceaccount.com`
- [ ] Ajouter votre API Key GoHighLevel dans `.env`
- [ ] Relancer `python3 test_config.py`
- [ ] Si tout est ✅, lancer `python3 scraper.py`
