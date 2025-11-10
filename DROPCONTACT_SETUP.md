# 🔑 Configuration Dropcontact

## ✅ Configuration locale (terminée)

Votre clé API Dropcontact a été ajoutée dans le fichier `.env` :
```
DROPCONTACT_API_KEY=H44QEt7aN97WYkwLkNjKm6WN7LYpM8
```

Vous pouvez maintenant tester en local :
```bash
streamlit run app_streamlit_pro.py
```

---

## 🌐 Configuration Streamlit Cloud

Pour que Dropcontact fonctionne sur votre application déployée sur Streamlit Cloud :

### 1. Aller sur votre dashboard Streamlit Cloud
https://share.streamlit.io/

### 2. Sélectionner votre application

### 3. Cliquer sur "⚙️ Settings" > "Secrets"

### 4. Ajouter votre clé Dropcontact dans le champ "Secrets"

Copiez-collez ce texte dans la zone "Secrets" :

```toml
DROPCONTACT_API_KEY = "H44QEt7aN97WYkwLkNjKm6WN7LYpM8"
```

**Important :** Respectez bien le format TOML avec les guillemets et le signe `=` (pas de `:`)

### 5. Cliquer sur "Save"

L'application va redémarrer automatiquement et Dropcontact sera activé !

---

## 🧪 Test rapide

Une fois configuré, lancez une prospection test avec 5-10 entreprises pour vérifier que Dropcontact fonctionne :

**Recherche test suggérée :**
```
"installateurs fenêtres Lyon"
Nombre : 10 entreprises
```

**Ce que vous devriez voir dans les logs :**
```
✅ Dropcontact activé
🔍 Enrichissement: Entreprise XYZ
  📊 Étape 1/2: API entreprise.data.gouv.fr...
  🎯 Étape 2/2: Dropcontact (décideur commercial)...
  🔍 Dropcontact: Recherche décideur pour Entreprise XYZ...
  ✅ Contact trouvé: Jean Dupont (Directeur Commercial)
     Email: jean.dupont@xyz.fr (vérifié)
     Sources: api_entreprise, dropcontact
```

---

## 📊 Vérifier votre consommation de crédits

Connectez-vous à votre dashboard Dropcontact pour suivre :
- Nombre de crédits utilisés
- Nombre de crédits restants
- Taux de succès de vos enrichissements

https://app.dropcontact.com/

---

## ⚠️ Sécurité

- ✅ Le fichier `.env` est dans `.gitignore` (votre clé ne sera jamais poussée sur GitHub)
- ✅ Sur Streamlit Cloud, utilisez les "Secrets" (jamais dans le code)
- ❌ Ne partagez JAMAIS votre clé API publiquement

---

## 🆘 Dépannage

**Message "DROPCONTACT_API_KEY non configurée" :**
- Vérifiez que le fichier `.env` existe avec la bonne clé
- Sur Streamlit Cloud : vérifiez les Secrets (Settings > Secrets)
- Redémarrez l'application après modification

**Message "Dropcontact API error: 401" :**
- La clé API est invalide ou expirée
- Vérifiez votre clé sur https://app.dropcontact.com/

**Message "Dropcontact API error: 429" :**
- Vous avez épuisé vos crédits mensuels
- Attendez le renouvellement ou changez de plan

**Taux de succès faible (<40%) :**
- Vérifiez que les entreprises ont bien un site web
- Vérifiez que vous scrapez des entreprises françaises (Dropcontact est optimisé pour la France)
- Certains secteurs ont moins de présence en ligne (taux normal)
