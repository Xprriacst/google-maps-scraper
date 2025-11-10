# 🗺️ Configuration Google Places API pour Market Size Estimator

Guide complet pour configurer l'estimation de taille de marché avec Google Places API.

---

## 📋 Prérequis

- Un compte Google Cloud Platform
- Une carte bancaire (pour activer l'API, même si $300 de crédit gratuit)
- 10 minutes

---

## 🚀 Étape 1 : Créer un projet Google Cloud

### 1.1 Aller sur Google Cloud Console
```
https://console.cloud.google.com/
```

### 1.2 Créer un nouveau projet
1. Cliquer sur le sélecteur de projet (en haut à gauche)
2. Cliquer sur **"Nouveau projet"**
3. Nom du projet : `google-maps-scraper` ou autre
4. Cliquer sur **"Créer"**

### 1.3 Attendre la création
⏱️ Prend 10-30 secondes

---

## 🔑 Étape 2 : Activer les APIs nécessaires

### 2.1 Activer Places API (new)
1. Dans le menu ☰ → **APIs & Services** → **Bibliothèque**
2. Rechercher : `Places API (new)`
3. Cliquer sur **"Places API (new)"**
4. Cliquer sur **"ACTIVER"**

### 2.2 Activer Places Aggregate API
1. Dans la bibliothèque, rechercher : `Places Aggregate API`
2. Cliquer sur **"Places Aggregate API"**
3. Cliquer sur **"ACTIVER"**

⚠️ **Note:** Si vous ne voyez pas "Places Aggregate API", c'est normal, elle fait partie de la nouvelle Places API.

### 2.3 Vérifier l'activation
✅ Dans le menu **APIs & Services** → **Tableau de bord**, vous devriez voir :
- Places API (new)

---

## 🔐 Étape 3 : Créer une clé API

### 3.1 Créer les identifiants
1. Menu ☰ → **APIs & Services** → **Identifiants**
2. Cliquer sur **"+ CRÉER DES IDENTIFIANTS"**
3. Sélectionner **"Clé API"**
4. Une clé API est créée automatiquement

### 3.2 Copier la clé API
```
AIzaSyD...votre_cle_ici...xyz123
```
⚠️ **Copiez-la immédiatement**, vous en aurez besoin !

### 3.3 Restreindre la clé API (IMPORTANT)
Pour éviter une utilisation non autorisée :

1. Cliquer sur **"RESTREINDRE LA CLÉ"** (ou éditer la clé créée)
2. Dans **"Restrictions relatives aux applications"** :
   - Sélectionner **"Adresses IP"**
   - Ajouter votre IP ou : `0.0.0.0/0` (toutes les IPs - moins sécurisé)
   - OU sélectionner **"Aucune"** si vous testez en local

3. Dans **"Restrictions relatives aux API"** :
   - Sélectionner **"Restreindre la clé"**
   - Cocher uniquement : **Places API (new)**

4. Cliquer sur **"ENREGISTRER"**

---

## 💳 Étape 4 : Activer la facturation

### 4.1 Pourquoi la facturation ?
- Google offre **$300 de crédit gratuit** pour 90 jours
- Places API nécessite la facturation même avec le crédit gratuit
- **Vous ne serez pas débité** tant que vous restez dans la limite gratuite

### 4.2 Activer la facturation
1. Menu ☰ → **Facturation**
2. Cliquer sur **"Lier un compte de facturation"**
3. Suivre les étapes (carte bancaire requise)
4. Activer le compte de facturation pour votre projet

### 4.3 Vérifier les limites gratuites
✅ **Vous avez :**
- $300 de crédit gratuit (90 jours)
- Ensuite, pricing à l'usage

---

## 💰 Étape 5 : Comprendre le pricing

### Places API (new) - Pricing 2025

| Opération | Prix | Quota gratuit |
|-----------|------|---------------|
| **Text Search** | $32 / 1000 requêtes | $200 de crédit/mois |
| **Nearby Search** | $32 / 1000 requêtes | $200 de crédit/mois |
| **Places Aggregate** | $5 / 1000 requêtes | Inclus dans crédit |

### Estimation des coûts pour vous

**Scénario 1 : Estimation simple (1 requête)**
```
1 requête Aggregate API
= $0.005
≈ Gratuit avec le crédit
```

**Scénario 2 : Estimation exhaustive (101 départements)**
```
101 requêtes Text Search
= 101 × $0.032
= $3.23
```

**Scénario 3 : Usage mensuel (10 estimations/mois)**
```
10 requêtes Aggregate API
= 10 × $0.005
= $0.05/mois
≈ Totalement négligeable
```

### Quota gratuit mensuel
Avec $200 de crédit gratuit/mois :
- **6,250 requêtes Text Search** gratuites/mois
- **40,000 requêtes Aggregate** gratuites/mois

👉 **Largement suffisant pour votre usage !**

---

## ⚙️ Étape 6 : Configurer dans votre projet

### 6.1 Ajouter la clé API dans .env
Éditez votre fichier `.env` :

```bash
# Google Places API (pour estimation taille de marché)
GOOGLE_PLACES_API_KEY=AIzaSyD...votre_cle_ici...xyz123
```

### 6.2 Sur Streamlit Cloud
1. Aller dans les **Settings** de votre app
2. Section **Secrets**
3. Ajouter :
```toml
GOOGLE_PLACES_API_KEY = "AIzaSyD...votre_cle_ici...xyz123"
```

---

## 🧪 Étape 7 : Tester l'API

### 7.1 Test en ligne de commande
```bash
cd /home/user/google-maps-scraper
python market_size_estimator.py
```

**Résultat attendu :**
```
=== Test Market Size Estimator ===

✅ Market Size Estimator activé

--- Test 1: Estimation vérandas France ---

📊 Estimation taille de marché pour: 'véranda'
✅ Estimation: 3456 entreprises (confiance: 70%)

Résultat:
  Nombre estimé: 3456
  Confiance: 70%
  Méthode: places_aggregate_api
  Détails: Estimation officielle Google Places Aggregate API
```

### 7.2 Test avec Python
```python
from market_size_estimator import MarketSizeEstimator

# Créer l'estimateur
estimator = MarketSizeEstimator()

# Estimer le marché des vérandas en France
result = estimator.estimate_market_size(
    query="véranda",
    location={'country': 'FR'},
    method='aggregate'
)

print(f"Estimation: {result['estimated_count']} entreprises")
print(f"Confiance: {result['confidence']:.0%}")
```

### 7.3 Test avec régions
```python
# Estimer par échantillon de régions
sample_regions = ['Paris', 'Lyon', 'Marseille', 'Toulouse', 'Nantes']

result = estimator.estimate_by_regions(
    query="véranda",
    regions=sample_regions
)

print(f"Total: {result['estimated_count']} entreprises")
print(f"Détail par région:")
for region, count in result['regional_breakdown'].items():
    print(f"  - {region}: {count}")
```

---

## 🔧 Étape 8 : Intégrer dans Streamlit

### 8.1 Ajouter dans la sidebar
Modifiez `app_streamlit_pro.py` :

```python
# Dans la sidebar, avant le bouton de lancement
if st.sidebar.checkbox("📊 Estimer la taille du marché", value=False):
    st.sidebar.markdown("---")
    st.sidebar.subheader("Estimation du marché")

    estimate_query = st.sidebar.text_input(
        "Mot-clé pour estimation",
        value=search_query.split()[0] if search_query else "",
        help="Ex: véranda, boulangerie, restaurant"
    )

    if st.sidebar.button("🔍 Estimer", use_container_width=True):
        with st.spinner("Estimation en cours..."):
            from market_size_estimator import MarketSizeEstimator
            estimator = MarketSizeEstimator()

            result = estimator.estimate_market_size(
                query=estimate_query,
                location={'country': 'FR'},
                method='aggregate'
            )

            st.sidebar.success(f"**{result['estimated_count']}** entreprises estimées")
            st.sidebar.info(f"Confiance: {result['confidence']:.0%}")
            st.sidebar.caption(f"Méthode: {result['method_used']}")
```

---

## 🚨 Dépannage

### Erreur : "API not enabled"
**Solution :**
1. Vérifier que Places API (new) est activée
2. Attendre 2-3 minutes après activation
3. Vérifier que le projet correct est sélectionné

### Erreur : "Billing not enabled"
**Solution :**
1. Activer la facturation dans Google Cloud Console
2. Lier un compte de facturation au projet
3. Attendre quelques minutes

### Erreur : "API key not valid"
**Solution :**
1. Vérifier que la clé API est correcte dans `.env`
2. Vérifier les restrictions de la clé API
3. S'assurer que Places API (new) est autorisée pour cette clé

### Erreur : 403 "Forbidden"
**Solution :**
1. Vérifier les restrictions IP de la clé API
2. Désactiver temporairement les restrictions pour tester
3. Vérifier que la facturation est active

### Quota dépassé
**Solution :**
1. Vérifier votre consommation dans Cloud Console
2. Augmenter le quota si nécessaire
3. Optimiser les requêtes (utiliser cache, limiter les appels)

---

## 📊 Monitoring et optimisation

### Voir sa consommation
1. Menu ☰ → **APIs & Services** → **Tableau de bord**
2. Sélectionner **Places API (new)**
3. Voir les métriques (requêtes, erreurs, latence)

### Définir des alertes budgétaires
1. Menu ☰ → **Facturation** → **Budgets et alertes**
2. Créer un budget (ex: $10/mois)
3. Configurer les alertes email (50%, 80%, 100%)

### Optimiser les coûts
✅ **Bonnes pratiques :**
1. **Cacher les résultats** : Sauvegarder les estimations pour éviter les appels répétés
2. **Batch les requêtes** : Grouper plusieurs estimations
3. **Limiter les pages** : Ne paginer que si nécessaire (méthode Text Search)
4. **Utiliser Aggregate API** : Plus économique que Text Search ($5 vs $32 / 1000 requêtes)

---

## 📈 Exemples d'utilisation

### Exemple 1 : Estimation rapide
```python
from market_size_estimator import MarketSizeEstimator

estimator = MarketSizeEstimator()
result = estimator.estimate_market_size("véranda", {'country': 'FR'})
print(f"Marché: {result['estimated_count']} entreprises")
# → Marché: 3456 entreprises
```

### Exemple 2 : Estimation exhaustive par départements
```python
from market_size_estimator import MarketSizeEstimator, FRENCH_DEPARTMENTS

estimator = MarketSizeEstimator()
result = estimator.estimate_by_regions("véranda", FRENCH_DEPARTMENTS)

print(f"Total France: {result['estimated_count']}")
print(f"Top 10 départements:")
sorted_regions = sorted(
    result['regional_breakdown'].items(),
    key=lambda x: x[1],
    reverse=True
)[:10]
for region, count in sorted_regions:
    print(f"  {region}: {count}")
```

### Exemple 3 : Comparaison multi-secteurs
```python
sectors = ['véranda', 'piscine', 'pergola', 'fenêtre']

for sector in sectors:
    result = estimator.estimate_market_size(sector, {'country': 'FR'})
    print(f"{sector.capitalize()}: {result['estimated_count']} entreprises")

# Résultat:
# Véranda: 3456 entreprises
# Piscine: 5234 entreprises
# Pergola: 2145 entreprises
# Fenêtre: 8923 entreprises
```

---

## ✅ Checklist finale

Avant de continuer, vérifiez que :
- [ ] Projet Google Cloud créé
- [ ] Places API (new) activée
- [ ] Clé API créée et copiée
- [ ] Clé API restreinte (sécurité)
- [ ] Facturation activée
- [ ] Clé ajoutée dans `.env` → `GOOGLE_PLACES_API_KEY=...`
- [ ] Test réussi : `python market_size_estimator.py`
- [ ] Budget alert configurée (optionnel mais recommandé)

---

## 🎯 Prochaines étapes

Une fois l'API configurée, vous pouvez :
1. ✅ Estimer la taille de n'importe quel marché
2. ✅ Intégrer dans Streamlit pour voir avant scraping
3. ✅ Optimiser votre stratégie de prospection
4. ✅ Comparer plusieurs secteurs/régions

---

**Créé pour :** google-maps-scraper project
**Date :** 2025-11-10
**API Version :** Places API (new) - 2025
