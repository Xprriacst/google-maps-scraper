# Google Maps Scraper avec Apify

Scraper automatisé qui extrait des entreprises depuis Google Maps via Apify, trouve leurs contacts clés et les envoie vers Google Sheets et GoHighLevel.

## 🆕 NOUVEAU : Mode Prospection B2B Pro

Version optimisée pour la prospection B2B avec enrichissement intelligent et scoring automatique !

### Fonctionnalités Pro
- 🎯 **Trouve LE bon décideur** : Directeur Commercial, Gérant, Président...
- 🔍 **Enrichissement intelligent** :
  - Scraping LinkedIn ciblé (recherche du décideur)
  - Scraping avancé du site web (pages /equipe, /mentions-legales)
  - Construction d'emails personnalisés (pattern detection)
  - APIs publiques françaises (SIRET, CA, dirigeants)
- ⭐ **Scoring automatique (0-100)** :
  - Qualité Email : 40 points
  - Qualité Contact : 30 points
  - Qualité Entreprise : 30 points
- 📊 **Export contacts qualifiés** :
  - 🟢 Premium (80-100) : Prospecter en priorité
  - 🟡 Qualifié (50-79) : Prospecter ensuite
  - 🟠 À vérifier (20-49) : Vérification manuelle
  - 🔴 Faible (0-19) : Skip

### Workflow Optimisé
```
Entrée: "fabricants vérandas Lyon"
  ↓
Phase 1: Scraping 200 entreprises
  ↓
Phase 2: Enrichissement automatique
  → Recherche décideur
  → Construction email personnalisé
  → API SIRET/SIREN
  ↓
Phase 3: Scoring et filtrage
  → Score >= 50
  ↓
Sortie: ~50 contacts qualifiés prêts à prospecter
```

## Fonctionnalités Standard

- ✅ Scraping Google Maps via Apify
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

### 🚀 Mode Prospection B2B Pro (Recommandé)

**Interface interactive complète avec enrichissement et scoring automatique**

```bash
python3 app_prospection.py
```

Cette interface offre :
- 🎯 Menu intuitif spécialisé prospection
- 🔍 Configuration guidée (recherche, nombre, score min)
- ⭐ Système de scoring automatique (0-100)
- 📊 Statistiques détaillées
- 📤 Export Google Sheets + CSV
- ❓ Aide et documentation intégrées

**Utilisation directe (ligne de commande)**

```bash
python3 scraper_pro.py
```

Le script vous demandera :
- La recherche à effectuer (ex: "fabricants vérandas Lyon")
- Le nombre d'entreprises à scraper (défaut: 200)
- Le score minimum pour qualifier un contact (défaut: 50)

**Exemple de résultat** :
```
Recherche: "fabricants vérandas Lyon"
Scrapé: 200 entreprises
Enrichi: 200 entreprises
Qualifiés: 52 contacts (score >= 50)
  🟢 Premium: 18 (80-100)
  🟡 Qualifiés: 34 (50-79)
```

### Mode Standard

**Scraper simple (sans enrichissement avancé)**

```bash
python scraper.py
```

Le script vous demandera :
- La recherche à effectuer (ex: "restaurants à Paris")
- Le nombre d'entreprises à scraper (par défaut: 50)

### Interface interactive Standard

Pour lancer l'interface interactive en ligne de commande :

```bash
python3 app_interactive.py
```

Cette interface offre :
- 🎯 Menu intuitif avec 5 options
- 🔍 Configuration guidée du scraping
- ⚙️ Test de configuration intégré
- ❓ Aide et documentation intégrées
- 📋 Historique des recherches

### Interface web (Flask)

Pour lancer l'interface web (expérimental) :

```bash
python3 app_simple.py
```

Puis ouvrez http://localhost:5000 dans votre navigateur.

### Interface graphique (Tkinter - macOS limité)

```bash
python3 app_gui.py
```

*Note: Peut avoir des problèmes de compatibilité sur macOS récents*

## Structure des données

### Mode Prospection B2B Pro

Le Google Sheet (feuille "Prospection") contiendra les colonnes suivantes :

**Contact**
- Nom Contact
- Fonction
- Email
- Confiance Email (HIGH/MEDIUM/LOW)
- LinkedIn
- Téléphone Direct

**Entreprise**
- Nom Entreprise
- SIRET
- Adresse
- Téléphone
- Site Web
- Note Google
- Nombre Avis
- Catégorie

**Enrichissement**
- SIREN
- Forme Juridique
- CA (Chiffre d'affaires)
- Employés
- Date Création

**Scoring**
- Score Total (/100)
- Score Email (/40)
- Score Contact (/30)
- Score Entreprise (/30)
- Catégorie (🟢🟡🟠🔴)
- Priorité (1-4)

**Métadonnées**
- Sources Données
- Date Ajout
- Statut (À contacter / Contacté / Répondu)
- URL Google Maps

### Mode Standard

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

### Mode Prospection B2B Pro

- **Apify** : Scraping Google Maps
- **Google Sheets API** : Stockage des données
- **entreprise.data.gouv.fr** : API publique française (SIRET, SIREN, dirigeants, CA)
- **BeautifulSoup + Requests** : Scraping sites web (équipe, mentions légales)

### Mode Standard

- **Apify** : Scraping Google Maps
- **Google Sheets API** : Stockage des données
- **Hunter.io** : Recherche d'emails (optionnel)
- **GoHighLevel API** : CRM Integration

## Architecture du Mode Prospection

### Modules créés

1. **contact_enricher.py** - Module d'enrichissement
   - `find_decision_maker_linkedin()` : Cherche le décideur sur LinkedIn
   - `extract_team_from_website()` : Extrait noms + fonctions du site web
   - `build_email_from_name()` : Construit l'email à partir du nom
   - `validate_email_pattern()` : Valide le pattern d'email
   - `enrich_with_api()` : Enrichit avec SIRET/CA/etc.

2. **contact_scorer.py** - Système de scoring
   - `calculate_email_score()` : Score qualité email (40 pts max)
   - `calculate_contact_score()` : Score qualité contact (30 pts max)
   - `calculate_company_score()` : Score qualité entreprise (30 pts max)
   - `get_final_score()` : Score total sur 100

3. **scraper_pro.py** - Scraper optimisé prospection
   - Intègre le scraper actuel
   - + Enrichissement automatique
   - + Scoring automatique
   - + Export contacts qualifiés seulement

4. **app_prospection.py** - Interface CLI interactive
   - Menu intuitif
   - Configuration guidée
   - Statistiques de scoring
   - Test de configuration
   - Aide intégrée

## Exemple de workflow complet

### Cas d'usage : Trouver des fabricants de vérandas à Lyon

**Input**
```bash
python3 app_prospection.py
# Recherche: "fabricants vérandas Lyon"
# Nombre: 200 entreprises
# Score min: 50
```

**Phase 1 : Scraping** (2min)
- Scrape 200 entreprises sur Google Maps
- Extrait nom, adresse, téléphone, site web, note, avis

**Phase 2 : Enrichissement** (30-60min selon nombre)

Pour chaque entreprise :
1. Scrape le site web (pages /equipe, /qui-sommes-nous, /mentions-legales)
2. Trouve "Marc Durand - Directeur Commercial"
3. Détecte le pattern d'email sur le site (prenom.nom@domaine.fr)
4. Construit marc.durand@veranda-concept-lyon.fr
5. Appel API entreprise.data.gouv.fr pour SIRET/CA/dirigeant

**Phase 3 : Scoring**

Exemple : Véranda Concept Lyon
- Email: marc.durand@veranda-concept-lyon.fr (HIGH) → 40/40
- Contact: Marc Durand, Directeur Commercial → 30/30
- Entreprise: Note 4.7, 85 avis, site pro → 30/30
- **TOTAL: 100/100 🟢 PREMIUM**

**Output**
- Google Sheets : 52 contacts qualifiés (feuille "Prospection")
- CSV local : contacts_qualifies_20250109_143022.csv
- Statistiques :
  - 🟢 18 Premium (prospecter maintenant)
  - 🟡 34 Qualifiés (prospecter ensuite)
