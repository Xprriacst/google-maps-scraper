# 🗺️ Google Maps Scraper Simple

Version simplifiée du scraper Google Maps qui permet de scraper des entreprises dans plusieurs villes et d'exporter les résultats en CSV.

## ✨ Fonctionnalités

- ✅ **Multi-villes** : Scrape plusieurs villes en une seule exécution
- ✅ **Export CSV** : Résultats exportés dans un fichier CSV facile à exploiter
- ✅ **Simple** : Aucune configuration complexe (juste un token Apify)
- ✅ **Flexible** : Mode interactif ou ligne de commande avec arguments
- ✅ **Chargement depuis fichier** : Importez une liste de villes depuis un fichier texte

## 📋 Prérequis

1. **Python 3.7+**
2. **Compte Apify** (gratuit) : [https://console.apify.com/](https://console.apify.com/)
   - Créez un compte gratuit
   - Récupérez votre token API dans `Account > Integrations`

## 🚀 Installation

### 1. Cloner le dépôt

```bash
git clone <votre-repo>
cd google-maps-scraper
```

### 2. Installer les dépendances

```bash
pip install -r requirements_simple.txt
```

### 3. Configurer le token Apify

Copiez le fichier d'exemple et ajoutez votre token :

```bash
cp .env.simple.example .env
```

Éditez `.env` et remplacez `your_apify_token_here` par votre vrai token Apify :

```env
APIFY_API_TOKEN=apify_api_XXXXXXXXXXXXXXXXXXXXXXXXXX
```

## 📖 Utilisation

### Mode 1 : Mode Interactif (Recommandé pour débuter)

Lancez simplement le script sans arguments :

```bash
python run_scraper.py
```

Le script vous guidera étape par étape :
1. Terme de recherche (ex: "restaurants", "menuisiers")
2. Liste des villes (manuellement ou depuis un fichier)
3. Nombre de résultats par ville
4. Nom du fichier de sortie (optionnel)

### Mode 2 : Ligne de Commande

#### Exemple basique avec villes en ligne

```bash
python run_scraper.py -s "restaurants" -c "Paris,Lyon,Marseille" -m 100
```

#### Exemple avec fichier de villes

```bash
python run_scraper.py -s "menuisiers" -f villes_exemple.txt -m 50
```

#### Exemple avec sortie personnalisée

```bash
python run_scraper.py -s "plombiers" -c "Paris,Lyon" -o mes_plombiers.csv -m 75
```

### Mode 3 : Import Python

Vous pouvez également utiliser le scraper dans vos propres scripts Python :

```python
from scraper_simple import GoogleMapsScraperSimple

# Créer le scraper
scraper = GoogleMapsScraperSimple()

# Définir les paramètres
search_term = "restaurants"
cities = ["Paris", "Lyon", "Marseille"]
max_results_per_city = 50

# Exécuter le scraping
results, csv_file = scraper.run(search_term, cities, max_results_per_city)

print(f"✅ {len(results)} entreprises scrapées")
print(f"💾 Résultats dans: {csv_file}")
```

## 📊 Options de la Ligne de Commande

```
Options:
  -s, --search TERME          Terme de recherche (ex: "restaurants")
  -c, --cities VILLES         Villes séparées par virgules (ex: "Paris,Lyon")
  -f, --file FICHIER          Fichier texte avec une ville par ligne
  -m, --max-results NOMBRE    Max résultats par ville (défaut: 50)
  -o, --output FICHIER        Nom du fichier CSV de sortie (optionnel)
  -t, --token TOKEN           Token Apify (optionnel, lu depuis .env)
  -h, --help                  Afficher l'aide
```

## 📁 Format du Fichier de Villes

Créez un fichier texte (`.txt`) avec une ville par ligne :

```
Paris
Lyon
Marseille
Toulouse
Nice
```

Exemple fourni : `villes_exemple.txt`

## 📤 Format du Fichier CSV de Sortie

Le fichier CSV contient les colonnes suivantes :

| Colonne | Description |
|---------|-------------|
| **Nom** | Nom de l'entreprise |
| **Adresse** | Adresse complète |
| **Téléphone** | Numéro de téléphone |
| **Site Web** | URL du site web |
| **Note** | Note Google Maps (0-5) |
| **Nombre Avis** | Nombre d'avis |
| **Catégorie** | Catégorie de l'entreprise |
| **Ville de recherche** | Ville utilisée pour la recherche |
| **Terme de recherche** | Terme utilisé pour la recherche |
| **URL Google Maps** | Lien vers la page Google Maps |
| **Latitude** | Coordonnée GPS |
| **Longitude** | Coordonnée GPS |
| **Plus Code** | Code Plus Google |
| **Horaires** | Horaires d'ouverture |
| **Description** | Description de l'entreprise |

## 💡 Exemples d'Utilisation

### Exemple 1 : Trouver des restaurants dans 3 villes

```bash
python run_scraper.py -s "restaurants italiens" -c "Paris,Lyon,Nice" -m 100
```

**Résultat** : Jusqu'à 300 restaurants italiens (100 par ville) exportés en CSV

### Exemple 2 : Trouver des artisans dans toutes les grandes villes

Créez `grandes_villes.txt` :
```
Paris
Lyon
Marseille
Toulouse
Nice
Nantes
Strasbourg
Montpellier
Bordeaux
Lille
```

Puis exécutez :
```bash
python run_scraper.py -s "menuisiers" -f grandes_villes.txt -m 50 -o menuisiers_france.csv
```

**Résultat** : Jusqu'à 500 menuisiers (50 par ville × 10 villes)

### Exemple 3 : Scraping massif avec Python

```python
from scraper_simple import GoogleMapsScraperSimple

scraper = GoogleMapsScraperSimple()

# Charger les villes depuis un fichier
with open('grandes_villes.txt', 'r') as f:
    cities = [line.strip() for line in f]

# Scraper plusieurs types d'entreprises
search_terms = ["plombiers", "électriciens", "menuisiers"]

for term in search_terms:
    print(f"\n🔍 Scraping: {term}")
    results, csv_file = scraper.run(term, cities, max_results_per_city=50)
    print(f"✅ {csv_file} créé avec {len(results)} résultats")
```

## ⚙️ Architecture Simplifiée

```
google-maps-scraper/
│
├── scraper_simple.py          # Classe principale du scraper
├── run_scraper.py             # Script CLI pour exécuter le scraper
├── requirements_simple.txt    # Dépendances minimales
├── .env.simple.example        # Template de configuration
├── villes_exemple.txt         # Liste d'exemple de villes
└── README_SIMPLE.md          # Cette documentation
```

## 🔧 Dépendances

Seulement 2 dépendances Python :

- `apify-client` : Client officiel Apify pour le scraping
- `python-dotenv` : Gestion des variables d'environnement

## ⚡ Performance

- **Temps moyen par ville** : 30-60 secondes
- **Limite Apify gratuit** : ~500 résultats/mois (varie selon le plan)
- **Pause entre requêtes** : 2 secondes (évite le rate limiting)

## 🆚 Différences avec la Version Complète

| Fonctionnalité | Version Simple | Version Complète |
|---------------|----------------|------------------|
| Scraping Google Maps | ✅ | ✅ |
| Multi-villes | ✅ | ❌ |
| Export CSV | ✅ | ❌ |
| Export Google Sheets | ❌ | ✅ |
| Recherche d'emails | ❌ | ✅ |
| Enrichissement contacts | ❌ | ✅ |
| Scoring qualité | ❌ | ✅ |
| API SIRET | ❌ | ✅ |
| GoHighLevel CRM | ❌ | ✅ |

**➡️ Utilisez la version simple si** : Vous voulez juste scraper des entreprises dans plusieurs villes et obtenir un CSV

**➡️ Utilisez la version complète si** : Vous faites de la prospection B2B et avez besoin d'emails + enrichissement

## 🐛 Dépannage

### Erreur "APIFY_API_TOKEN manquant"

**Solution** : Vérifiez que le fichier `.env` existe et contient votre token Apify valide

### Erreur "Rate limit exceeded"

**Solution** : Le scraper intègre déjà des pauses. Si le problème persiste, augmentez la pause dans `scraper_simple.py` ligne 127 (actuellement 2 secondes)

### Trop peu de résultats

**Solution** :
- Vérifiez votre requête de recherche (soyez plus générique)
- Augmentez `-m` (max résultats par ville)
- Certaines villes peuvent avoir moins d'entreprises que d'autres

### Fichier CSV vide

**Solution** :
- Vérifiez que le scraping n'a pas retourné 0 résultats
- Vérifiez les permissions d'écriture du dossier
- Consultez les logs pour identifier l'erreur

## 📞 Support

Pour toute question ou bug :
1. Consultez d'abord cette documentation
2. Vérifiez les logs d'erreur affichés
3. Ouvrez une issue sur GitHub

## 📄 Licence

Ce projet est fourni tel quel, sans garantie. Utilisez-le de manière responsable et respectez les conditions d'utilisation de Google Maps et Apify.

## 🎯 Roadmap Future

- [ ] Support du format JSON en sortie
- [ ] Filtrage par note minimum
- [ ] Détection et suppression des doublons
- [ ] Mode "append" pour ajouter à un CSV existant
- [ ] Barre de progression visuelle

---

**Bon scraping ! 🚀**
