# 📊 Configuration Google Sheets - Historique des Prospections

Ce guide explique comment configurer l'export automatique vers Google Sheets pour sauvegarder toutes vos prospections.

## 🎯 Fonctionnalités

- ✅ Sauvegarde automatique de toutes les recherches
- ✅ Historique complet avec timestamp
- ✅ 3 contacts par entreprise (nom, fonction, email, téléphone, LinkedIn)
- ✅ Données d'enrichissement (effectifs, SIRET, etc.)
- ✅ Accès partagé via Google Sheets (collaboration)
- ✅ Export CSV/Excel depuis Google Sheets

## 📋 Étape 1: Créer un projet Google Cloud

1. **Aller sur Google Cloud Console**
   - Visitez: https://console.cloud.google.com/

2. **Créer un nouveau projet**
   - Cliquez sur "Sélectionner un projet" en haut
   - Cliquez sur "NOUVEAU PROJET"
   - Nom du projet: `prospection-b2b` (ou votre choix)
   - Cliquez sur "CRÉER"

3. **Sélectionner le projet**
   - Attendez quelques secondes
   - Sélectionnez votre nouveau projet dans le menu déroulant

## 🔑 Étape 2: Activer Google Sheets API

1. **Aller dans APIs & Services**
   - Menu ☰ → "APIs & Services" → "Library"
   - Ou visitez directement: https://console.cloud.google.com/apis/library

2. **Activer Google Sheets API**
   - Recherchez "Google Sheets API"
   - Cliquez sur le résultat
   - Cliquez sur "ACTIVER" (ENABLE)

3. **Activer Google Drive API** (nécessaire aussi)
   - Retour à la bibliothèque
   - Recherchez "Google Drive API"
   - Cliquez sur le résultat
   - Cliquez sur "ACTIVER" (ENABLE)

## 👤 Étape 3: Créer un Service Account

1. **Aller dans Credentials**
   - Menu ☰ → "APIs & Services" → "Credentials"
   - Ou visitez: https://console.cloud.google.com/apis/credentials

2. **Créer un Service Account**
   - Cliquez sur "+ CREATE CREDENTIALS"
   - Sélectionnez "Service account"

3. **Détails du Service Account**
   - **Service account name:** `prospection-sheets` (ou votre choix)
   - **Service account ID:** sera généré automatiquement
   - **Description:** "Service account pour export prospections vers Google Sheets"
   - Cliquez sur "CREATE AND CONTINUE"

4. **Accorder des rôles** (Skip cette étape)
   - Cliquez sur "CONTINUE" (pas besoin de rôles pour notre cas)

5. **Finaliser**
   - Cliquez sur "DONE"

## 🔐 Étape 4: Créer et télécharger la clé JSON

1. **Trouver votre Service Account**
   - Dans "APIs & Services" → "Credentials"
   - Section "Service Accounts"
   - Cliquez sur l'email du service account (ex: `prospection-sheets@...`)

2. **Créer une clé**
   - Allez dans l'onglet "KEYS"
   - Cliquez sur "ADD KEY" → "Create new key"
   - Sélectionnez "JSON"
   - Cliquez sur "CREATE"

3. **Télécharger le fichier**
   - Un fichier JSON sera téléchargé automatiquement
   - Nom du fichier: `prospection-b2b-xxxxx.json`
   - **⚠️ GARDEZ CE FICHIER EN SÉCURITÉ !**

## 📝 Étape 5: Copier l'email du Service Account

Dans le fichier JSON téléchargé, trouvez la ligne `client_email`:

```json
{
  "type": "service_account",
  "project_id": "prospection-b2b",
  "client_email": "prospection-sheets@prospection-b2b.iam.gserviceaccount.com",
  ...
}
```

**Copiez cet email** - vous en aurez besoin à l'étape 7.

## ⚙️ Étape 6: Configurer Streamlit Cloud

### Option A: Via l'interface Streamlit Cloud

1. **Aller dans les paramètres de votre app**
   - Ouvrez votre app Streamlit
   - Cliquez sur "⋮" → "Settings"

2. **Ajouter les secrets**
   - Section "Secrets"
   - Ouvrez le fichier JSON téléchargé avec un éditeur de texte
   - Copiez **tout le contenu** du fichier JSON

3. **Ajouter dans secrets.toml**
   ```toml
   # Collez ici tout le contenu du fichier JSON téléchargé
   GOOGLE_SHEETS_CREDENTIALS_JSON = '''
   {
     "type": "service_account",
     "project_id": "prospection-b2b",
     "private_key_id": "xxxx...",
     "private_key": "-----BEGIN PRIVATE KEY-----\nMIIE...",
     "client_email": "prospection-sheets@prospection-b2b.iam.gserviceaccount.com",
     "client_id": "xxxx...",
     "auth_uri": "https://accounts.google.com/o/oauth2/auth",
     "token_uri": "https://oauth2.googleapis.com/token",
     "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
     "client_x509_cert_url": "https://www.googleapis.com/robot/v1/metadata/x509/..."
   }
   '''
   ```

4. **Sauvegarder**
   - Cliquez sur "Save"
   - L'application va redémarrer automatiquement

### Option B: En local (développement)

Ajoutez à votre fichier `.env`:

```bash
GOOGLE_SHEETS_CREDENTIALS_JSON='{"type":"service_account","project_id":"prospection-b2b",...}'
```

## 📊 Étape 7: Créer et partager le Google Sheet (IMPORTANT!)

### Option 1: Laisser l'app créer le spreadsheet

1. **Lancer une prospection**
   - L'application créera automatiquement le spreadsheet
   - Vous verrez le lien dans les résultats

2. **Donner accès à vous-même**
   - Cliquez sur le lien du spreadsheet
   - Vous verrez "Vous avez besoin d'une autorisation"
   - **Copiez l'email du Service Account** (étape 5)
   - Demandez au propriétaire du compte Google qui a créé le projet de:
     - Ouvrir le spreadsheet
     - Cliquer sur "Partager"
     - Ajouter votre propre email avec accès "Éditeur"

### Option 2: Créer le spreadsheet manuellement

1. **Créer un nouveau Google Sheet**
   - Allez sur https://sheets.google.com
   - Créez un nouveau spreadsheet
   - Nommez-le: "Prospection B2B - Historique"

2. **Partager avec le Service Account**
   - Cliquez sur "Partager" (bouton vert en haut à droite)
   - Collez l'email du Service Account (ex: `prospection-sheets@prospection-b2b.iam.gserviceaccount.com`)
   - Définir le rôle: **Éditeur**
   - Décochez "Notifier les personnes"
   - Cliquez sur "Partager"

3. **Vérifier le partage**
   - Le Service Account devrait apparaître dans la liste des personnes ayant accès
   - Rôle: Éditeur

## ✅ Étape 8: Tester la configuration

1. **Activer l'export dans l'app**
   - Ouvrez votre app Streamlit
   - Sidebar → "📊 Export Google Sheets"
   - Cochez "Activer l'export automatique"
   - Vérifiez que vous voyez "✅ Credentials configurés"

2. **Lancer une prospection test**
   - Entrez une recherche simple (ex: "restaurants Paris")
   - Nombre d'entreprises: 10 (pour un test rapide)
   - Cliquez sur "🚀 Lancer la prospection"

3. **Vérifier l'export**
   - À la fin de la prospection, vous devriez voir:
     - "📊 Export Google Sheets réussi ! [Voir le spreadsheet](lien)"
     - "📈 Total lignes sauvegardées: XX"
   - Cliquez sur le lien pour ouvrir le spreadsheet
   - Vérifiez que les données sont bien présentes

## 📋 Structure du Google Sheet

Le spreadsheet contiendra les colonnes suivantes:

| Colonne | Description |
|---------|-------------|
| Date/Heure | Timestamp de la prospection |
| Requête | Recherche Google Maps effectuée |
| Score | Score total de qualification (0-100) |
| Catégorie | Premium / Qualifié / À vérifier / Faible |
| Source Contact | Apollo / Dropcontact / Gérant légal |
| Taille | TPE / PME / ETI / GE |
| Entreprise | Nom de l'entreprise |
| **Contact 1** | Nom du contact principal |
| Fonction 1 | Poste du contact 1 |
| Email 1 | Email du contact 1 |
| Téléphone 1 | Téléphone du contact 1 |
| LinkedIn 1 | Profil LinkedIn du contact 1 |
| Confidence 1 | Niveau de confiance email (high/medium/low) |
| **Contact 2** | Nom du 2ème contact |
| Fonction 2 | Poste du contact 2 |
| Email 2 | Email du contact 2 |
| Téléphone 2 | Téléphone du contact 2 |
| LinkedIn 2 | Profil LinkedIn du contact 2 |
| Confidence 2 | Niveau de confiance email |
| **Contact 3** | Nom du 3ème contact |
| Fonction 3 | Poste du contact 3 |
| Email 3 | Email du contact 3 |
| Téléphone 3 | Téléphone du contact 3 |
| LinkedIn 3 | Profil LinkedIn du contact 3 |
| Confidence 3 | Niveau de confiance email |
| Téléphone Entreprise | Téléphone de l'entreprise |
| Site Web | URL du site web |
| Note | Note Google Maps |
| Avis | Nombre d'avis Google Maps |
| Effectifs | Nombre d'employés |
| SIRET | Numéro SIRET |
| Adresse | Adresse complète |
| Ville | Ville |
| Code Postal | Code postal |

## 🔧 Dépannage

### Erreur: "Spreadsheet not found"
- Vérifiez que vous avez bien partagé le spreadsheet avec l'email du Service Account
- Vérifiez que le nom du spreadsheet correspond exactement

### Erreur: "Insufficient permissions"
- Le Service Account doit avoir le rôle "Éditeur" (pas "Lecteur")
- Revérifiez le partage du spreadsheet

### Erreur: "Invalid credentials"
- Vérifiez que vous avez copié **tout** le contenu du JSON
- Vérifiez qu'il n'y a pas d'erreur de formatage dans secrets.toml
- Les triples quotes `'''` doivent entourer le JSON

### L'export ne se lance pas
- Vérifiez que "Activer l'export automatique" est coché
- Vérifiez que les credentials sont configurés (✅ dans l'interface)
- Consultez les logs pour voir les erreurs détaillées

### "You need permission" quand j'ouvre le spreadsheet
- Le spreadsheet a été créé par le Service Account
- Demandez à quelqu'un qui a accès de vous partager le spreadsheet
- Ou créez le spreadsheet manuellement et partagez-le avec le Service Account

## 💡 Conseils d'utilisation

1. **Historique centralisé**: Toutes vos prospections sont dans un seul fichier, facile à analyser

2. **Export vers Excel**: Dans Google Sheets → Fichier → Télécharger → Microsoft Excel (.xlsx)

3. **Filtres et tableaux croisés dynamiques**: Utilisez les fonctionnalités Google Sheets pour analyser vos données

4. **Collaboration**: Partagez le spreadsheet avec votre équipe pour un accès partagé

5. **Backup**: Google Sheets sauvegarde automatiquement, mais vous pouvez aussi faire des exports réguliers

6. **Pivot tables**: Analysez vos prospections par date, catégorie, taille d'entreprise, etc.

## 🔒 Sécurité

⚠️ **Le fichier JSON contient des clés privées sensibles !**

- ✅ Stockez-le dans un endroit sécurisé
- ✅ Ne le commitez JAMAIS dans Git
- ✅ Ne le partagez jamais publiquement
- ✅ Utilisez les secrets Streamlit Cloud pour la production
- ✅ Renouvelez les clés si elles sont compromises

## 📚 Ressources

- [Documentation Google Sheets API](https://developers.google.com/sheets/api)
- [Documentation Service Accounts](https://cloud.google.com/iam/docs/service-accounts)
- [gspread Documentation](https://docs.gspread.org/)

---

**Besoin d'aide ?** Ouvrez une issue sur GitHub avec votre problème et les messages d'erreur.
