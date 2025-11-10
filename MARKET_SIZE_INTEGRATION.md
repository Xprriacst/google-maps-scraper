# 📊 Intégration Market Size Estimator dans Streamlit

Guide pour intégrer l'estimation de taille de marché dans votre interface Streamlit.

---

## 🎯 Option 1 : Intégration Simple (Sidebar)

Ajoutez ce code dans `app_streamlit_pro.py`, dans la sidebar, **avant le bouton "Lancer la prospection"** :

```python
# ========== ESTIMATION TAILLE DE MARCHÉ ==========
st.sidebar.markdown("---")
st.sidebar.subheader("📊 Estimation du marché")

# Checkbox pour activer l'estimation
show_market_size = st.sidebar.checkbox(
    "Estimer la taille du marché avant scraping",
    value=False,
    help="Utilise Google Places API pour estimer le nombre total d'entreprises"
)

if show_market_size:
    # Extraire le mot-clé principal de la recherche
    estimate_keyword = st.sidebar.text_input(
        "Mot-clé pour estimation",
        value=search_query.split()[0] if search_query else "",
        help="Ex: véranda, boulangerie, restaurant",
        key='estimate_keyword'
    )

    # Bouton d'estimation
    if st.sidebar.button("🔍 Estimer le marché", use_container_width=True, key='estimate_button'):
        if not estimate_keyword:
            st.sidebar.error("Veuillez entrer un mot-clé")
        else:
            with st.spinner("⏳ Estimation en cours..."):
                try:
                    from market_size_estimator import MarketSizeEstimator

                    # Initialiser l'estimateur
                    estimator = MarketSizeEstimator()

                    if not estimator.enabled:
                        st.sidebar.warning("⚠️ GOOGLE_PLACES_API_KEY non configurée")
                        st.sidebar.info("Voir GOOGLE_PLACES_API_SETUP.md pour la configuration")
                    else:
                        # Estimer la taille du marché
                        result = estimator.estimate_market_size(
                            query=estimate_keyword,
                            location={'country': 'FR'},
                            method='aggregate'
                        )

                        # Afficher les résultats
                        if result['estimated_count'] > 0:
                            st.sidebar.success(f"**🎯 {result['estimated_count']:,}** entreprises estimées")
                            st.sidebar.info(f"📊 Confiance: {result['confidence']:.0%}")
                            st.sidebar.caption(f"Méthode: {result['method_used']}")

                            # Calculer le coût Apify estimé
                            estimated_cost = (result['estimated_count'] / 1000) * 2  # ~$2 per 1000 places
                            st.sidebar.caption(f"💰 Coût Apify estimé: ${estimated_cost:.2f}")

                            # Conseils selon la taille
                            if result['estimated_count'] > 5000:
                                st.sidebar.warning("⚠️ Marché très large. Considérez affiner votre recherche (région, spécialité)")
                            elif result['estimated_count'] > 1000:
                                st.sidebar.info("💡 Marché large. Vous pourriez cibler par régions.")
                            else:
                                st.sidebar.success("✅ Taille de marché optimale pour prospection exhaustive")

                        else:
                            st.sidebar.error("❌ Aucune estimation disponible")
                            st.sidebar.caption(result.get('details', ''))

                except Exception as e:
                    st.sidebar.error(f"❌ Erreur: {str(e)}")
                    st.sidebar.caption("Vérifiez que GOOGLE_PLACES_API_KEY est configurée")

    # Sauvegarder l'estimation dans session_state pour usage ultérieur
    if 'market_size_result' in locals():
        st.session_state.market_size_estimate = result

st.sidebar.markdown("---")
```

**Résultat :**
- Checkbox "Estimer la taille du marché avant scraping"
- Input pour le mot-clé
- Bouton "Estimer le marché"
- Affichage : nombre d'entreprises, confiance, coût estimé, conseils

---

## 🎯 Option 2 : Intégration Avancée (Expander)

Pour une interface plus riche avec comparaisons régionales :

```python
# Dans la sidebar
with st.sidebar.expander("📊 Market Size Estimator", expanded=False):
    st.markdown("**Estimez la taille de votre marché cible**")

    # Choix de la méthode
    estimate_method = st.selectbox(
        "Méthode d'estimation",
        ['aggregate', 'text', 'regional'],
        format_func=lambda x: {
            'aggregate': '⚡ Rapide (Google Aggregate API)',
            'text': '📝 Standard (Text Search)',
            'regional': '🗺️ Par régions (exhaustif)'
        }[x],
        help="aggregate = 1 requête, regional = 101 requêtes (tous les départements)"
    )

    estimate_keyword = st.text_input(
        "Mot-clé",
        value=search_query.split()[0] if search_query else "",
        key='advanced_estimate_keyword'
    )

    # Options régionales si méthode régionale
    regions_to_check = []
    if estimate_method == 'regional':
        regional_scope = st.radio(
            "Scope régional",
            ['sample', 'full'],
            format_func=lambda x: {
                'sample': '5 grandes villes (rapide)',
                'full': '101 départements (exhaustif)'
            }[x]
        )

        if regional_scope == 'sample':
            regions_to_check = ['Paris', 'Lyon', 'Marseille', 'Toulouse', 'Nantes']
        else:
            from market_size_estimator import FRENCH_DEPARTMENTS
            regions_to_check = FRENCH_DEPARTMENTS

    if st.button("🔍 Lancer l'estimation", use_container_width=True, key='advanced_estimate_button'):
        if not estimate_keyword:
            st.error("Entrez un mot-clé")
        else:
            with st.spinner("Estimation en cours..."):
                try:
                    from market_size_estimator import MarketSizeEstimator

                    estimator = MarketSizeEstimator()

                    if not estimator.enabled:
                        st.warning("⚠️ API non configurée")
                    else:
                        # Estimer selon la méthode
                        if estimate_method == 'regional':
                            result = estimator.estimate_by_regions(
                                query=estimate_keyword,
                                regions=regions_to_check
                            )

                            # Afficher le total
                            st.success(f"**🎯 {result['estimated_count']:,}** entreprises")
                            st.info(f"📊 Confiance: {result['confidence']:.0%}")

                            # Afficher le top 10 des régions
                            if 'regional_breakdown' in result:
                                st.markdown("**Top 10 régions:**")
                                sorted_regions = sorted(
                                    result['regional_breakdown'].items(),
                                    key=lambda x: x[1],
                                    reverse=True
                                )[:10]

                                for i, (region, count) in enumerate(sorted_regions, 1):
                                    st.caption(f"{i}. {region}: {count}")

                        else:
                            result = estimator.estimate_market_size(
                                query=estimate_keyword,
                                location={'country': 'FR'},
                                method=estimate_method
                            )

                            st.success(f"**🎯 {result['estimated_count']:,}** entreprises")
                            st.info(f"📊 Confiance: {result['confidence']:.0%}")
                            st.caption(f"Méthode: {result['method_used']}")

                        # Sauvegarder dans session_state
                        st.session_state.market_size_result = result

                except Exception as e:
                    st.error(f"❌ Erreur: {str(e)}")
```

---

## 🎯 Option 3 : Page dédiée Market Research

Créer une nouvelle page Streamlit : `pages/2_📊_Market_Research.py`

```python
#!/usr/bin/env python3
"""
Page Streamlit pour la recherche de marché et estimation
"""

import streamlit as st
from market_size_estimator import MarketSizeEstimator, FRENCH_DEPARTMENTS
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="Market Research - Google Maps Scraper",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Market Research & Size Estimation")
st.markdown("Analysez la taille de votre marché cible avant de lancer le scraping")

# Initialiser l'estimateur
estimator = MarketSizeEstimator()

if not estimator.enabled:
    st.error("⚠️ Google Places API non configurée")
    st.info("Consultez `GOOGLE_PLACES_API_SETUP.md` pour la configuration")
    st.stop()

# Tabs pour différentes analyses
tab1, tab2, tab3 = st.tabs(["🎯 Estimation Simple", "🗺️ Analyse Régionale", "📈 Comparaison Secteurs"])

# ========== TAB 1: ESTIMATION SIMPLE ==========
with tab1:
    col1, col2 = st.columns([2, 1])

    with col1:
        st.subheader("Estimation rapide")
        keyword = st.text_input(
            "Mot-clé à analyser",
            placeholder="Ex: véranda, boulangerie, restaurant"
        )

    with col2:
        st.subheader("Méthode")
        method = st.selectbox(
            "API",
            ['aggregate', 'text'],
            format_func=lambda x: '⚡ Aggregate (rapide)' if x == 'aggregate' else '📝 Text Search'
        )

    if st.button("🔍 Estimer", type="primary"):
        if not keyword:
            st.warning("Entrez un mot-clé")
        else:
            with st.spinner("Estimation en cours..."):
                result = estimator.estimate_market_size(
                    query=keyword,
                    location={'country': 'FR'},
                    method=method
                )

                # Afficher les résultats
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Entreprises estimées", f"{result['estimated_count']:,}")
                with col2:
                    st.metric("Confiance", f"{result['confidence']:.0%}")
                with col3:
                    estimated_cost = (result['estimated_count'] / 1000) * 2
                    st.metric("Coût Apify estimé", f"${estimated_cost:.2f}")

                st.info(f"📊 Méthode: {result['method_used']}")
                st.caption(result.get('details', ''))

                # Insights
                st.subheader("💡 Insights")
                if result['estimated_count'] > 10000:
                    st.warning("🚨 Marché très large (10k+). Recommandation: Affiner par région ou spécialité")
                elif result['estimated_count'] > 5000:
                    st.info("📊 Marché large (5k-10k). Considérez un ciblage par régions prioritaires")
                elif result['estimated_count'] > 1000:
                    st.success("✅ Marché moyen (1k-5k). Taille idéale pour prospection complète")
                else:
                    st.success("✅ Marché niche (<1k). Prospection exhaustive possible facilement")


# ========== TAB 2: ANALYSE RÉGIONALE ==========
with tab2:
    st.subheader("🗺️ Analyse par régions")

    keyword_regional = st.text_input(
        "Mot-clé",
        placeholder="Ex: véranda",
        key='keyword_regional'
    )

    scope = st.radio(
        "Scope de l'analyse",
        ['sample', 'full'],
        format_func=lambda x: '⚡ 5 grandes villes (rapide, ~5s)' if x == 'sample' else '🗺️ 101 départements (exhaustif, ~3min)'
    )

    if st.button("🔍 Analyser par régions", type="primary"):
        if not keyword_regional:
            st.warning("Entrez un mot-clé")
        else:
            # Choisir les régions
            if scope == 'sample':
                regions = ['Paris', 'Lyon', 'Marseille', 'Toulouse', 'Nantes']
            else:
                regions = FRENCH_DEPARTMENTS

            with st.spinner(f"Analyse de {len(regions)} régions en cours..."):
                result = estimator.estimate_by_regions(
                    query=keyword_regional,
                    regions=regions
                )

                # Métriques globales
                st.metric("Total France", f"{result['estimated_count']:,} entreprises")
                st.caption(f"Confiance: {result['confidence']:.0%}")

                # Créer un DataFrame pour visualisation
                df = pd.DataFrame([
                    {'Région': region, 'Nombre': count}
                    for region, count in result['regional_breakdown'].items()
                ]).sort_values('Nombre', ascending=False)

                # Top 20
                col1, col2 = st.columns(2)

                with col1:
                    st.subheader("📊 Top 20 régions")
                    st.dataframe(
                        df.head(20),
                        use_container_width=True,
                        hide_index=True
                    )

                with col2:
                    st.subheader("📈 Distribution")
                    fig = px.bar(
                        df.head(20),
                        x='Région',
                        y='Nombre',
                        title=f"Top 20 régions pour '{keyword_regional}'"
                    )
                    fig.update_xaxes(tickangle=45)
                    st.plotly_chart(fig, use_container_width=True)

                # Download CSV
                csv = df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    "📥 Télécharger CSV",
                    csv,
                    f"market_size_{keyword_regional}.csv",
                    "text/csv"
                )


# ========== TAB 3: COMPARAISON SECTEURS ==========
with tab3:
    st.subheader("📈 Comparaison multi-secteurs")

    sectors_input = st.text_area(
        "Secteurs à comparer (un par ligne)",
        value="véranda\npiscine\npergola\nfenêtre\nporte",
        height=150
    )

    if st.button("📊 Comparer les secteurs", type="primary"):
        sectors = [s.strip() for s in sectors_input.split('\n') if s.strip()]

        if not sectors:
            st.warning("Entrez au moins un secteur")
        else:
            with st.spinner(f"Analyse de {len(sectors)} secteurs..."):
                results = []

                # Progress bar
                progress_bar = st.progress(0)
                for i, sector in enumerate(sectors):
                    result = estimator.estimate_market_size(
                        query=sector,
                        location={'country': 'FR'},
                        method='aggregate'
                    )
                    results.append({
                        'Secteur': sector.capitalize(),
                        'Nombre': result['estimated_count'],
                        'Confiance': f"{result['confidence']:.0%}"
                    })
                    progress_bar.progress((i + 1) / len(sectors))

                progress_bar.empty()

                # Créer DataFrame
                df_comp = pd.DataFrame(results).sort_values('Nombre', ascending=False)

                # Afficher
                col1, col2 = st.columns(2)

                with col1:
                    st.subheader("📊 Résultats")
                    st.dataframe(
                        df_comp,
                        use_container_width=True,
                        hide_index=True
                    )

                with col2:
                    st.subheader("📈 Graphique")
                    fig = px.bar(
                        df_comp,
                        x='Secteur',
                        y='Nombre',
                        title="Comparaison des tailles de marché"
                    )
                    st.plotly_chart(fig, use_container_width=True)

                # Insights
                st.subheader("💡 Insights")
                max_sector = df_comp.iloc[0]
                min_sector = df_comp.iloc[-1]
                st.info(f"🏆 Marché le plus large: **{max_sector['Secteur']}** ({max_sector['Nombre']:,} entreprises)")
                st.info(f"🎯 Marché le plus niche: **{min_sector['Secteur']}** ({min_sector['Nombre']:,} entreprises)")

# Footer
st.markdown("---")
st.caption("💡 Utilisez ces données pour optimiser votre stratégie de prospection avant le scraping")
```

---

## 🎯 Résumé des 3 options

| Option | Complexité | Emplacement | Fonctionnalités |
|--------|------------|-------------|-----------------|
| **1. Simple** | ⭐ | Sidebar | Estimation rapide, conseils |
| **2. Avancée** | ⭐⭐ | Expander | Méthodes multiples, comparaison régionale |
| **3. Page dédiée** | ⭐⭐⭐ | Page séparée | Analyse complète, visualisations, export |

---

## 🚀 Quelle option choisir ?

### Option 1 - Si vous voulez :
- ✅ Intégration simple et rapide
- ✅ Juste une estimation avant scraping
- ✅ Garder l'interface actuelle légère

### Option 2 - Si vous voulez :
- ✅ Plus de flexibilité
- ✅ Comparaisons régionales
- ✅ Garder tout dans la page principale

### Option 3 - Si vous voulez :
- ✅ Outil d'analyse de marché complet
- ✅ Visualisations avancées
- ✅ Page dédiée à la recherche de marché
- ✅ Export des données

---

## ✅ Prochaine étape

1. **Choisissez une option** (je recommande Option 1 pour commencer)
2. **Copiez le code** dans votre fichier
3. **Testez** avec `streamlit run app_streamlit_pro.py`
4. **Ajustez** selon vos besoins

Voulez-vous que j'implémente directement une de ces options dans votre code ?
