# 💾 Système de Cache Base de Données

## Vue d'ensemble

Le scraper utilise maintenant un **système de cache intelligent avec SQLite** pour éviter de rechercher plusieurs fois les mêmes contacts et informations d'enrichissement.

### Avantages

✅ **Gain de temps** : Les contacts déjà trouvés sont réutilisés instantanément
✅ **Économie d'API calls** : Hunter.io, Pappers, etc. ne sont appelés qu'une fois par entreprise
✅ **Persistance** : Les données restent disponibles entre les runs
✅ **Mise à jour intelligente** : Les infos Google Maps sont rafraîchies à chaque run

---

## 🗂️ Structure de la base de données

Le fichier `contacts_cache.db` contient 4 tables principales :

### 1. `companies` - Informations de base
- Nom, adresse, téléphone, site web
- Note Google Maps, nombre d'avis
- Catégorie
- URL Google Maps (clé unique)

### 2. `contacts` - Contacts enrichis
- Nom du contact
- Poste (Gérant, Directeur, etc.)
- Email + niveau de confiance
- LinkedIn, téléphone direct
- Sources des données (Hunter, Pappers, scraping web, etc.)

### 3. `enrichment_data` - Données d'enrichissement
- SIRET, SIREN
- Forme juridique
- Chiffre d'affaires
- Nombre d'employés
- Date de création

### 4. `scores` - Scores de qualification
- Score total (/100)
- Scores détaillés (email, contact, entreprise)
- Catégorie (Premium, Qualifié, À vérifier, Faible)
- Priorité

---

## 🔍 Comment ça fonctionne ?

### Première exécution
```
🔍 Recherche: "fabricants vérandas Lyon"
[1/50] Entreprise ABC
  🔍 Enrichissement en cours...
  📧 Email trouvé: contact@abc.fr (high)
  💾 Sauvegardé en base
```

### Exécutions suivantes
```
🔍 Recherche: "fabricants vérandas Lyon"
[1/50] Entreprise ABC
  💾 Données trouvées en cache (évite l'enrichissement)
  📧 Email: contact@abc.fr (high)
  ⚡ Instantané !
```

### Statistiques affichées
```
✅ Enrichissement terminé
   💾 Cache: 35 entreprises
   🔍 Nouvelles: 15 entreprises

📊 Base de données totale:
   Entreprises: 250
   Avec emails: 180
```

---

## 🎯 Identification des entreprises

Le système identifie une entreprise par (dans l'ordre de priorité) :

1. **URL Google Maps** (le plus fiable)
2. **Site web** (si disponible)
3. **Nom de l'entreprise** (en dernier recours)

Cela permet de :
- Éviter les doublons
- Reconnaître une entreprise même si son nom a légèrement changé
- Mettre à jour les informations si nécessaires

---

## 📊 Utilisation de la base

### Consulter les statistiques

```python
from database_manager import DatabaseManager

db = DatabaseManager()
stats = db.get_stats()

print(f"Total entreprises: {stats['total_companies']}")
print(f"Avec emails: {stats['companies_with_email']}")
print(f"Enrichies: {stats['companies_enriched']}")
print(f"Score moyen: {stats['average_score']}")
```

### Rechercher une entreprise

```python
# Par nom
company_id = db.company_exists("Mon Entreprise")

# Par site web
company_id = db.company_exists(
    "Mon Entreprise",
    website="https://mon-entreprise.fr"
)

# Récupérer toutes les données
if company_id:
    data = db.get_company_data(company_id)
    print(f"Email: {data['contact_email']}")
    print(f"Score: {data['score_total']}/100")
```

### Sauvegarder manuellement

```python
company_data = {
    'name': 'Nouvelle Entreprise',
    'website': 'https://nouvelle.fr',
    'contact_email': 'contact@nouvelle.fr',
    'email_confidence': 'high',
    'score_total': 85,
    # ... autres données
}

company_id = db.save_company(company_data)
print(f"Sauvegardé avec ID: {company_id}")
```

---

## 🔄 Mise à jour automatique

À chaque run, le système :

1. ✅ Vérifie si l'entreprise existe en cache
2. ✅ Si OUI : récupère le contact et l'enrichissement du cache
3. ✅ Met à jour les infos Google Maps (note, avis, etc.)
4. ✅ Si NON : fait l'enrichissement complet et sauvegarde

---

## 🗑️ Gestion de la base

### Emplacement
- Fichier : `contacts_cache.db`
- Dans le répertoire du projet
- Automatiquement ignoré par Git (`.gitignore`)

### Sauvegarder la base
```bash
cp contacts_cache.db contacts_cache_backup_$(date +%Y%m%d).db
```

### Réinitialiser la base
```bash
rm contacts_cache.db
# Un nouveau fichier vide sera créé au prochain run
```

### Exporter en CSV
```python
import sqlite3
import csv

conn = sqlite3.connect('contacts_cache.db')
cursor = conn.cursor()

cursor.execute('''
    SELECT c.name, c.website, co.contact_email, s.score_total
    FROM companies c
    LEFT JOIN contacts co ON c.id = co.company_id
    LEFT JOIN scores s ON c.id = s.company_id
    WHERE co.contact_email != ""
    ORDER BY s.score_total DESC
''')

with open('export_cache.csv', 'w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(['Entreprise', 'Site Web', 'Email', 'Score'])
    writer.writerows(cursor.fetchall())

conn.close()
```

---

## ⚡ Performances

### Sans cache
- 50 entreprises = ~10-15 minutes
- API calls : 150+ (Hunter, Pappers, scraping web)
- Coût API : élevé

### Avec cache (2ème run)
- 50 entreprises (35 en cache) = ~3-5 minutes
- API calls : 45 (seulement pour les 15 nouvelles)
- Coût API : réduit de 70%

### Exemple réel
```
1er run : 100 entreprises → 25 minutes, 300 API calls
2ème run : 100 entreprises (70 en cache) → 10 minutes, 90 API calls
3ème run : 100 entreprises (85 en cache) → 6 minutes, 45 API calls
```

---

## 🛠️ Maintenance

### Nettoyer les vieilles entrées
```python
from database_manager import DatabaseManager
import sqlite3

db = DatabaseManager()

# Supprimer les entreprises sans contact après 30 jours
db.conn.execute('''
    DELETE FROM companies
    WHERE id NOT IN (SELECT company_id FROM contacts WHERE contact_email != "")
    AND created_at < datetime('now', '-30 days')
''')
db.conn.commit()
```

### Mettre à jour en masse
```python
# Exemple: mettre à jour tous les scores
from contact_scorer import ContactScorer

db = DatabaseManager()
scorer = ContactScorer()

cursor = db.conn.cursor()
cursor.execute('SELECT * FROM companies')

for row in cursor.fetchall():
    data = dict(row)
    # Recalculer le score
    new_score = scorer.score_contact(data)
    db._save_score(data['id'], new_score, datetime.now().isoformat())

db.conn.commit()
```

---

## ❓ Questions fréquentes

### Q: La base devient trop grosse ?
**R:** Supprimez les entrées anciennes ou créez une nouvelle base. Les fichiers SQLite sont très compacts (1000 entreprises ≈ 1 MB).

### Q: Je veux forcer un nouvel enrichissement ?
**R:** Supprimez l'entreprise de la base ou renommez le fichier `.db`.

### Q: Les données sont-elles sécurisées ?
**R:** La base est en local et ignorée par Git. Pour plus de sécurité, chiffrez le fichier `.db`.

### Q: Puis-je partager ma base avec l'équipe ?
**R:** Oui, copiez le fichier `contacts_cache.db` à votre équipe. Attention aux conflits si plusieurs personnes l'utilisent simultanément.

---

## 🚀 Prochaines améliorations possibles

- [ ] Export automatique de la base en CSV périodiquement
- [ ] Interface web pour consulter/modifier la base
- [ ] Synchronisation cloud (Google Drive, Dropbox)
- [ ] Détection automatique des données obsolètes
- [ ] Alertes sur les changements importants (nouveau email trouvé, score amélioré)
- [ ] Intégration avec CRM (export vers Pipedrive, HubSpot, etc.)

---

**💡 Astuce** : Lancez le scraper régulièrement sur les mêmes secteurs pour enrichir progressivement votre base de données de prospects qualifiés !
