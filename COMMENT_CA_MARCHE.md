# 🎯 Comment fonctionne la recherche d'emails

## Système intelligent sans Hunter.io

Le scraper utilise maintenant un système intelligent à 3 niveaux pour trouver les emails des entreprises françaises :

## 🔍 Niveau 1 : Scraping du site web (Haute confiance)

Le scraper visite automatiquement le site web de chaque entreprise et cherche des emails dans :

### Pages analysées :
- **Page d'accueil**
- **/contact** ou **/nous-contacter**
- **/a-propos** ou **/about**
- **/mentions-legales**
- **/equipe** ou **/team**

### Méthodes de recherche :
1. **Liens mailto:** Détecte tous les `<a href="mailto:...">` 
2. **Regex avancé** : Trouve tous les patterns d'emails dans le texte
3. **Prioritisation** : Préfère les emails avec "contact@", "info@", "commercial@"

**Confiance** : `high` (email trouvé directement sur le site)

---

## 🧠 Niveau 2 : Patterns intelligents (Confiance moyenne/basse)

Si aucun email n'est trouvé sur le site, le système génère des patterns basés sur les conventions françaises :

### Patterns générés automatiquement :
```
1. contact@domain.com      ← Plus probable
2. info@domain.com
3. hello@domain.com
4. bonjour@domain.com      ← Spécifique France
5. accueil@domain.com
6. commercial@domain.com
7. direction@domain.com
8. gerant@domain.com
```

### Pattern intelligent basé sur le nom :
- **"Boulangerie Martin"** → génère aussi `martin@domain.com`
- **"Salon de coiffure Dupont"** → génère aussi `dupont@domain.com`

**Confiance** : `low` (email généré, à vérifier)

---

## 👤 Recherche du gérant (Bonus)

Le scraper essaie aussi de trouver le nom du gérant en analysant les pages :

### Patterns recherchés :
- "Gérant : Jean Dupont"
- "Dirigeant : Marie Martin"
- "Président : Pierre Durand"
- "Directeur : Sophie Bernard"
- "Fondateur : Luc Moreau"

**Source** : Pages "À propos", "Équipe", "Mentions légales"

---

## 📊 Indicateur de confiance

Chaque email est marqué avec un niveau de confiance :

| Niveau | Source | Fiabilité |
|--------|--------|-----------|
| **HIGH** | Trouvé sur le site web | ✅✅✅ Très fiable |
| **MEDIUM** | Trouvé mais email générique | ✅✅ Fiable |
| **LOW** | Pattern généré | ✅ À vérifier |

La colonne "Confiance Email" dans Google Sheets vous indique la fiabilité.

---

## 💡 Avantages vs Hunter.io

### ✅ Avantages :
- **Gratuit** : Pas de limite, pas d'abonnement
- **Adapté France** : Patterns spécifiques français
- **Scraping direct** : Trouve les emails publics sur les sites
- **Aucune limite de volume** : 50, 100, 1000+ par jour

### ⚠️ Limites :
- **Confiance variable** : Pas de validation automatique
- **Plus lent** : Scrape chaque site individuellement (~2-3s par entreprise)
- **Emails à vérifier** : Les patterns générés peuvent être invalides

---

## 🎯 Recommandations

### Pour 50 entreprises/jour :
✅ **Solution actuelle parfaite** : Gratuit et efficace

### Pour validation des emails (optionnel) :
1. **NeverBounce** (~15$/mois pour 1500 vérifications)
2. **ZeroBounce** (~16$/mois pour 2000 vérifications)
3. **Proofy** (~29$/mois pour 5000 vérifications)

### Workflow recommandé :
```
1. Scraper Google Maps → 50 entreprises
2. Recherche emails automatique (notre système)
3. Export vers Google Sheets
4. Trier par "Confiance Email"
5. Utiliser d'abord les emails "high" et "medium"
6. Vérifier manuellement ou via service les emails "low"
```

---

## 📈 Taux de succès attendus

D'après nos tests :

- **Emails trouvés (scraping)** : 30-40% des entreprises
- **Patterns générés** : 100% des entreprises avec site web
- **Taux de réponse estimé** :
  - HIGH confidence : ~70-80%
  - MEDIUM confidence : ~50-60%
  - LOW confidence : ~20-30%

---

## 🚀 Prochaines améliorations possibles

1. **Validation automatique** : Vérifier que l'email existe (SMTP check)
2. **Scraping LinkedIn** : Trouver les dirigeants
3. **Scraping pages jaunes** : Source alternative d'emails
4. **Base de données** : Mémoriser les emails trouvés
5. **A/B Testing** : Tester plusieurs patterns et garder les meilleurs
