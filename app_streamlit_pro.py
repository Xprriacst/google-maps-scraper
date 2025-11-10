#!/usr/bin/env python3
"""
Interface Streamlit pour le Scraper Pro - Prospection B2B
Application web moderne avec visualisation en temps réel
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import time
import os
from dotenv import load_dotenv

# Import des modules
from scraper_pro import GoogleMapsScraperPro
from contact_scorer import ContactScorer
from utils import get_env
from google_sheets_exporter import GoogleSheetsExporter

# Charger les variables d'environnement
load_dotenv()

# Configuration de la page
st.set_page_config(
    page_title="Scraper Pro - Prospection B2B",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Styles CSS personnalisés
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        padding: 1rem 0;
    }
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        text-align: center;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .status-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-weight: bold;
        font-size: 0.9rem;
    }
    .badge-premium {
        background-color: #4caf50;
        color: white;
    }
    .badge-qualified {
        background-color: #ff9800;
        color: white;
    }
    .badge-verify {
        background-color: #ff5722;
        color: white;
    }
    .badge-weak {
        background-color: #9e9e9e;
        color: white;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialiser l'état de la session
if 'results' not in st.session_state:
    st.session_state.results = None
if 'running' not in st.session_state:
    st.session_state.running = False
if 'stop_requested' not in st.session_state:
    st.session_state.stop_requested = False

def render_header():
    """Affiche l'en-tête de l'application"""
    st.markdown('<h1 class="main-header">🎯 Scraper Pro - Prospection B2B</h1>', unsafe_allow_html=True)
    st.markdown("""
    <p style="text-align: center; color: #666; font-size: 1.2rem; margin-bottom: 2rem;">
        Enrichissement intelligent et scoring automatique pour vos prospections
    </p>
    """, unsafe_allow_html=True)

def render_sidebar():
    """Affiche la barre latérale avec les paramètres"""
    st.sidebar.title("⚙️ Configuration")

    # Vérifier la configuration
    with st.sidebar.expander("🔑 Vérifier la configuration", expanded=False):
        apify_ok = bool(get_env('APIFY_API_TOKEN'))
        sheets_ok = bool(get_env('GOOGLE_SHEET_ID'))
        # Vérifier credentials (local ou Streamlit Cloud)
        creds_ok = os.path.exists('credentials.json')
        try:
            if 'gcp_service_account' in st.secrets:
                creds_ok = True
        except:
            pass

        st.write("**APIFY_API_TOKEN:**", "✅" if apify_ok else "❌")
        st.write("**GOOGLE_SHEET_ID:**", "✅" if sheets_ok else "❌")
        st.write("**credentials.json:**", "✅" if creds_ok else "❌")

        if not (apify_ok and sheets_ok):
            st.warning("⚠️ Configuration incomplète. Consultez le README.")

    st.sidebar.markdown("---")

    # Configuration Google Sheets Export
    with st.sidebar.expander("📊 Export Google Sheets", expanded=False):
        enable_export = st.checkbox(
            "Activer l'export automatique",
            value=True,
            help="Sauvegarder toutes les prospections dans un Google Sheet"
        )

        if enable_export:
            # Vérifier si les credentials sont configurés
            gs_creds = get_env('GOOGLE_SHEETS_CREDENTIALS_JSON')
            if gs_creds:
                st.success("✅ Credentials configurés")

                # Nom du spreadsheet
                gs_name = st.text_input(
                    "Nom du spreadsheet",
                    value="Prospection B2B - Historique",
                    help="Le spreadsheet sera créé s'il n'existe pas"
                )

                # Stocker dans session state
                st.session_state.gs_export_enabled = True
                st.session_state.gs_spreadsheet_name = gs_name
            else:
                st.warning("⚠️ Configurez GOOGLE_SHEETS_CREDENTIALS_JSON dans les secrets")
                st.session_state.gs_export_enabled = False
        else:
            st.session_state.gs_export_enabled = False

    st.sidebar.markdown("---")

    # Paramètres de prospection
    st.sidebar.subheader("🔍 Paramètres de recherche")

    search_query = st.sidebar.text_input(
        "Recherche Google Maps",
        placeholder="Ex: fabricants vérandas Lyon",
        help="Soyez précis pour de meilleurs résultats"
    )

    max_results = st.sidebar.slider(
        "Nombre d'entreprises à scraper",
        min_value=10,
        max_value=200,
        value=50,
        step=10,
        help="Plus vous scrapez, plus vous aurez de contacts qualifiés (ratio ~25%)"
    )

    st.sidebar.markdown("---")

    # Paramètres de ciblage des contacts
    st.sidebar.subheader("🎯 Ciblage des contacts")

    use_adaptive_targeting = st.sidebar.checkbox(
        "Ciblage adaptatif automatique",
        value=True,
        help="Adapte le type de contact recherché selon la taille de l'entreprise (CEO pour TPE/PME, directeurs opérationnels pour ETI/GE)"
    )

    target_role = None
    if not use_adaptive_targeting:
        target_role = st.sidebar.selectbox(
            "Type de contact recherché",
            options=[
                "Dirigeant (CEO, Gérant, Président)",
                "Direction commerciale",
                "Direction achats",
                "Direction marketing",
                "Direction des opérations",
                "Direction technique",
                "Direction financière"
            ],
            help="Rechercher systématiquement ce type de contact, quelle que soit la taille de l'entreprise"
        )

    # Stocker dans session state
    st.session_state.use_adaptive_targeting = use_adaptive_targeting
    st.session_state.target_role = target_role

    st.sidebar.markdown("---")

    # Bouton de lancement
    start_button = st.sidebar.button(
        "🚀 Lancer la prospection",
        type="primary",
        disabled=st.session_state.running or not search_query,
        use_container_width=True
    )

    # Informations
    with st.sidebar.expander("💡 Conseils d'utilisation", expanded=False):
        st.markdown("""
        **Recherches efficaces:**
        - ✅ "fabricants vérandas Lyon"
        - ✅ "installateurs fenêtres Paris"
        - ❌ "vérandas" (trop large)

        **Estimation des résultats:**
        - 50 entreprises → ~12 qualifiés
        - 100 entreprises → ~25 qualifiés
        - 200 entreprises → ~50 qualifiés

        **Temps d'exécution:**
        - Scraping: 2-5 min
        - Enrichissement: 30-60 min
        """)

    with st.sidebar.expander("📊 Système de scoring", expanded=False):
        st.markdown("""
        **Score Total: 0-100 points**

        - 📧 Email (40 pts)
        - 👤 Contact (30 pts)
        - 🏢 Entreprise (30 pts)

        **Catégories:**
        - 🟢 Premium (80-100)
        - 🟡 Qualifié (50-79)
        - 🟠 À vérifier (20-49)
        - 🔴 Faible (0-19)
        """)

    return search_query, max_results, start_button

def run_prospection(search_query, max_results):
    """Lance la prospection et affiche la progression"""
    st.session_state.running = True
    st.session_state.stop_requested = False

    # Conteneur pour les messages de progression
    progress_container = st.container()

    with progress_container:
        st.info(f"🚀 Lancement de la prospection: **{search_query}**")

        # Message d'information pour arrêter
        st.caption("💡 Pour arrêter le processus, rechargez la page (Ctrl+R ou Cmd+R) ou cliquez sur 'Stop' en haut à droite de Streamlit.")

        # Barre de progression
        progress_bar = st.progress(0)
        status_text = st.empty()

        try:
            # Phase 1: Initialisation
            status_text.text("Phase 1/3: Initialisation...")
            progress_bar.progress(10)

            # Récupérer les paramètres de ciblage
            use_adaptive = st.session_state.get('use_adaptive_targeting', True)
            target_role = st.session_state.get('target_role', None)

            scraper = GoogleMapsScraperPro(
                min_score=0,
                use_adaptive_targeting=use_adaptive,
                target_role=target_role
            )

            # Phase 2: Scraping
            status_text.text(f"Phase 2/3: Scraping de {max_results} entreprises...")
            progress_bar.progress(20)

            raw_results = scraper.scrape_google_maps(search_query, max_results)

            if not raw_results:
                st.error("❌ Aucun résultat trouvé")
                st.session_state.running = False
                return

            progress_bar.progress(40)

            # Phase 3: Enrichissement
            status_text.text(f"Phase 3/3: Enrichissement de {len(raw_results)} entreprises...")

            enriched = []
            for idx, result in enumerate(raw_results):
                # Vérifier si l'arrêt a été demandé
                if st.session_state.stop_requested:
                    st.warning(f"⏹️ Prospection arrêtée par l'utilisateur après {idx}/{len(raw_results)} entreprises enrichies.")
                    break

                # Mise à jour de la progression
                progress = 40 + int((idx / len(raw_results)) * 50)
                progress_bar.progress(progress)
                status_text.text(f"Phase 3/3: Enrichissement {idx+1}/{len(raw_results)}...")

                # Enrichir (simplifié pour la démo - en prod on utiliserait scraper.enrich_and_score)
                company_name = result.get('title', '')
                base_data = {
                    'name': company_name,
                    'address': result.get('address', ''),
                    'phone': result.get('phone', ''),
                    'website': result.get('website', ''),
                    'rating': result.get('totalScore', ''),
                    'reviews_count': result.get('reviewsCount', ''),
                    'category': result.get('categoryName', ''),
                    'url': result.get('url', ''),
                }

                # Enrichir et scorer (version simplifiée pour la démo)
                enriched_data = scraper.enricher.enrich_contact(
                    company_name,
                    base_data['website'],
                    base_data['address']
                )

                full_data = {**base_data, **enriched_data}
                scoring = scraper.scorer.score_contact(full_data)
                full_data.update(scoring)

                enriched.append(full_data)

            progress_bar.progress(90)

            # Récupérer tous les contacts (pas de filtrage par score)
            qualified = enriched
            qualified.sort(key=lambda x: x.get('score_total', 0), reverse=True)

            # Calculer les statistiques
            scorer = ContactScorer()
            stats = scorer.get_stats(enriched)

            progress_bar.progress(100)
            status_text.text("✅ Prospection terminée !")

            # Stocker les résultats
            st.session_state.results = {
                'raw_count': len(raw_results),
                'enriched': enriched,
                'qualified': qualified,
                'stats': stats
            }

            st.success(f"✅ **{len(qualified)}** contacts qualifiés trouvés sur {len(enriched)} entreprises enrichies !")

            # Export vers Google Sheets si activé
            if st.session_state.get('gs_export_enabled', False):
                try:
                    status_text.text("📊 Export vers Google Sheets...")
                    gs_creds = get_env('GOOGLE_SHEETS_CREDENTIALS_JSON')
                    gs_name = st.session_state.get('gs_spreadsheet_name', 'Prospection B2B - Historique')

                    exporter = GoogleSheetsExporter(gs_creds, gs_name)
                    exporter.get_or_create_spreadsheet()

                    # Exporter les résultats
                    success = exporter.export_prospection(search_query, qualified)

                    if success:
                        sheet_url = exporter.get_spreadsheet_url()
                        st.success(f"📊 Export Google Sheets réussi ! [Voir le spreadsheet]({sheet_url})")

                        # Afficher les stats
                        gs_stats = exporter.get_stats()
                        st.info(f"📈 Total lignes sauvegardées: {gs_stats.get('total_rows', 0)}")
                    else:
                        st.warning("⚠️ L'export vers Google Sheets a échoué (voir logs)")

                except Exception as gs_error:
                    st.warning(f"⚠️ Erreur lors de l'export Google Sheets: {gs_error}")
                    import traceback
                    with st.expander("Détails de l'erreur"):
                        st.code(traceback.format_exc())

        except Exception as e:
            st.error(f"❌ Erreur: {str(e)}")
            import traceback
            st.code(traceback.format_exc())

        finally:
            st.session_state.running = False

def render_statistics(stats, enriched_contacts):
    """Affiche les statistiques sous forme de métriques"""
    st.subheader("📊 Statistiques globales")

    # Calculer le nombre d'entreprises avec/sans contact
    contacts_found = sum(1 for c in enriched_contacts if c.get('contact_name', '').strip())
    no_contacts = len(enriched_contacts) - contacts_found

    col1, col2, col3, col4, col5, col6, col7 = st.columns(7)

    with col1:
        st.metric("Total scrapé", stats['total'])
    with col2:
        st.metric("✅ Avec contact", contacts_found, f"{contacts_found/stats['total']*100:.0f}%")
    with col3:
        st.metric("❌ Sans contact", no_contacts, f"{no_contacts/stats['total']*100:.0f}%")
    with col4:
        st.metric("🟢 Premium", stats['premium'], f"{stats['premium_pct']}%")
    with col5:
        st.metric("🟡 Qualifiés", stats['qualified'], f"{stats['qualified_pct']}%")
    with col6:
        st.metric("🟠 À vérifier", stats['verify'])
    with col7:
        st.metric("Score moyen", f"{stats['avg_score']}/100")

def render_charts(enriched_contacts):
    """Affiche les graphiques de distribution"""
    st.subheader("📈 Visualisations")

    col1, col2 = st.columns(2)

    # Préparer les données
    df = pd.DataFrame(enriched_contacts)

    with col1:
        # Distribution des scores
        fig_scores = px.histogram(
            df,
            x='score_total',
            nbins=20,
            title="Distribution des scores",
            labels={'score_total': 'Score total', 'count': 'Nombre de contacts'},
            color_discrete_sequence=['#667eea']
        )
        fig_scores.update_layout(showlegend=False)
        st.plotly_chart(fig_scores, use_container_width=True)

    with col2:
        # Répartition par catégorie
        category_counts = df['category'].value_counts()

        colors = {
            'Premium': '#4caf50',
            'Qualifié': '#ff9800',
            'À vérifier': '#ff5722',
            'Faible': '#9e9e9e'
        }

        fig_categories = go.Figure(data=[go.Pie(
            labels=category_counts.index,
            values=category_counts.values,
            marker=dict(colors=[colors.get(cat, '#999') for cat in category_counts.index]),
            hole=0.4
        )])
        fig_categories.update_layout(title="Répartition par catégorie")
        st.plotly_chart(fig_categories, use_container_width=True)

def render_contacts_table(contacts):
    """Affiche le tableau des contacts avec filtres"""
    st.subheader("📋 Liste complète des entreprises")

    # Fonction pour déterminer la source du contact
    def get_contact_source(contact):
        """Détermine la source d'où vient le contact"""
        data_sources = contact.get('data_sources', [])
        has_contact = bool(contact.get('contact_name', '').strip())

        if not has_contact:
            return '❌ Non trouvé'

        if 'dropcontact' in data_sources:
            return '🎯 Dropcontact'
        elif 'legal_data' in data_sources:
            return '🏛️ Dirigeant légal (API gouv)'
        elif 'website_team' in data_sources:
            return '🌐 Site web'
        elif 'api_entreprise' in data_sources:
            return '📊 API entreprise.gouv'
        else:
            return '🔍 Autre source'

    # Fonction pour déterminer la taille de l'entreprise
    def get_company_size(contact):
        """Détermine la catégorie de taille de l'entreprise"""
        employees_str = str(contact.get('employees', ''))
        data_sources = contact.get('data_sources', [])
        is_ai_estimated = 'ai_estimated' in data_sources

        if not employees_str or employees_str == 'N/A':
            return '❓ Inconnu'

        try:
            # Extraire le nombre (peut être "50" ou "10-20")
            employees = int(employees_str.split('-')[0].strip())
            ai_marker = ' 🤖' if is_ai_estimated else ''

            if employees <= 10:
                return f'🏪 TPE (≤10){ai_marker}'
            elif employees <= 250:
                return f'🏢 PME (11-250){ai_marker}'
            elif employees <= 5000:
                return f'🏭 ETI (251-5000){ai_marker}'
            else:
                return f'🏰 GE (5000+){ai_marker}'
        except:
            return '❓ Inconnu'

    # Filtres
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        filter_category = st.multiselect(
            "Filtrer par catégorie",
            options=['Premium', 'Qualifié', 'À vérifier', 'Faible'],
            default=['Premium', 'Qualifié', 'À vérifier', 'Faible'],
            key='filter_cat'
        )

    with col2:
        filter_min_score = st.number_input(
            "Score minimum",
            min_value=0,
            max_value=100,
            value=0,
            step=10,
            key='filter_score'
        )

    with col3:
        filter_confidence = st.multiselect(
            "Confiance email",
            options=['high', 'medium', 'low', 'none'],
            default=['high', 'medium', 'low', 'none'],
            key='filter_conf'
        )

    with col4:
        filter_source = st.multiselect(
            "Source contact",
            options=['🎯 Dropcontact', '🏛️ Dirigeant légal (API gouv)', '🌐 Site web', '📊 API entreprise.gouv', '❌ Non trouvé', '🔍 Autre source'],
            default=['🎯 Dropcontact', '🏛️ Dirigeant légal (API gouv)', '🌐 Site web', '📊 API entreprise.gouv', '❌ Non trouvé', '🔍 Autre source'],
            key='filter_source'
        )

    # Filtrer les contacts
    filtered_contacts = [
        c for c in contacts
        if c.get('category') in filter_category
        and c.get('score_total', 0) >= filter_min_score
        and c.get('email_confidence', 'none').lower() in filter_confidence
        and get_contact_source(c) in filter_source
    ]

    st.info(f"📊 **{len(filtered_contacts)}** contacts affichés sur {len(contacts)}")

    if not filtered_contacts:
        st.warning("Aucun contact ne correspond aux filtres")
        return

    # Préparer le DataFrame
    df_display = pd.DataFrame([
        {
            'Score': f"{c.get('score_total', 0)} {c.get('emoji', '')}",
            'Catégorie': c.get('category', ''),
            'Source Contact': get_contact_source(c),
            'Taille': get_company_size(c),
            'Entreprise': c.get('name', ''),
            # Contact 1 (principal)
            'Contact 1': c.get('contact_1_name', '').strip() if c.get('contact_1_name', '').strip() else '❌',
            'Fonction 1': c.get('contact_1_position', '').strip() if c.get('contact_1_position', '').strip() else '-',
            'Email 1': c.get('contact_1_email', '').strip() if c.get('contact_1_email', '').strip() else '-',
            # Contact 2
            'Contact 2': c.get('contact_2_name', '').strip() if c.get('contact_2_name', '').strip() else '-',
            'Fonction 2': c.get('contact_2_position', '').strip() if c.get('contact_2_position', '').strip() else '-',
            'Email 2': c.get('contact_2_email', '').strip() if c.get('contact_2_email', '').strip() else '-',
            # Contact 3
            'Contact 3': c.get('contact_3_name', '').strip() if c.get('contact_3_name', '').strip() else '-',
            'Fonction 3': c.get('contact_3_position', '').strip() if c.get('contact_3_position', '').strip() else '-',
            'Email 3': c.get('contact_3_email', '').strip() if c.get('contact_3_email', '').strip() else '-',
            # Autres infos
            'Téléphone': c.get('phone', 'N/A'),
            'Site web': c.get('website', 'N/A'),
            'Note': f"{c.get('rating', 'N/A')} ⭐",
            'Avis': c.get('reviews_count', 'N/A'),
            'Effectifs': c.get('employees', 'N/A'),
            'SIRET': c.get('siret', 'N/A'),
        }
        for c in filtered_contacts
    ])

    # Afficher le tableau
    st.dataframe(
        df_display,
        use_container_width=True,
        height=400
    )

    # Bouton d'export CSV
    # Stocker le timestamp pour éviter qu'il change à chaque re-run
    if 'csv_timestamp' not in st.session_state:
        st.session_state.csv_timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')

    csv = df_display.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="📥 Télécharger en CSV",
        data=csv,
        file_name=f"contacts_{st.session_state.csv_timestamp}.csv",
        mime="text/csv",
        use_container_width=True,
        key='download_csv'
    )

def main():
    """Fonction principale de l'application"""
    render_header()

    # Sidebar
    search_query, max_results, start_button = render_sidebar()

    # Si le bouton est cliqué
    if start_button:
        run_prospection(search_query, max_results)

    # Afficher les résultats s'ils existent
    if st.session_state.results:
        results = st.session_state.results

        # Onglets
        tab1, tab2, tab3 = st.tabs(["📊 Statistiques", "📋 Toutes les entreprises", "📈 Graphiques"])

        with tab1:
            render_statistics(results['stats'], results['enriched'])

            # Breakdown détaillé
            st.markdown("---")
            col1, col2, col3 = st.columns(3)

            with col1:
                st.markdown("### 📧 Score Email")
                st.info(f"Moyenne: {sum(c.get('score_email', 0) for c in results['enriched']) / len(results['enriched']):.1f}/40")

            with col2:
                st.markdown("### 👤 Score Contact")
                st.info(f"Moyenne: {sum(c.get('score_contact', 0) for c in results['enriched']) / len(results['enriched']):.1f}/30")

            with col3:
                st.markdown("### 🏢 Score Entreprise")
                st.info(f"Moyenne: {sum(c.get('score_company', 0) for c in results['enriched']) / len(results['enriched']):.1f}/30")

            # Statistiques par source de contact
            st.markdown("---")
            st.markdown("### 📊 Statistiques par source de contact")

            # Fonction pour déterminer la source (même que dans render_contacts_table)
            def get_contact_source(contact):
                data_sources = contact.get('data_sources', [])
                has_contact = bool(contact.get('contact_name', '').strip())
                if not has_contact:
                    return '❌ Non trouvé'
                if 'dropcontact' in data_sources:
                    return '🎯 Dropcontact'
                elif 'legal_data' in data_sources:
                    return '🏛️ Dirigeant légal'
                elif 'website_team' in data_sources:
                    return '🌐 Site web'
                elif 'api_entreprise' in data_sources:
                    return '📊 API gouv'
                else:
                    return '🔍 Autre'

            # Compter par source
            sources_count = {}
            for c in results['enriched']:
                source = get_contact_source(c)
                sources_count[source] = sources_count.get(source, 0) + 1

            # Afficher dans des colonnes
            cols = st.columns(len(sources_count))
            for idx, (source, count) in enumerate(sorted(sources_count.items(), key=lambda x: x[1], reverse=True)):
                with cols[idx]:
                    pct = (count / len(results['enriched']) * 100)
                    st.metric(source, count, f"{pct:.0f}%")

        with tab2:
            render_contacts_table(results['enriched'])

        with tab3:
            render_charts(results['enriched'])

    else:
        # Message d'accueil
        st.info("👈 Configurez votre prospection dans la barre latérale et cliquez sur **Lancer la prospection**")

        # Guide rapide
        with st.expander("📖 Guide rapide", expanded=True):
            st.markdown("""
            ### 🎯 Comment utiliser le Scraper Pro

            1. **Configurez votre recherche** dans la barre latérale
               - Entrez une recherche précise (ex: "fabricants vérandas Lyon")
               - Choisissez le nombre d'entreprises à scraper
               - Définissez le score minimum

            2. **Lancez la prospection**
               - Cliquez sur "🚀 Lancer la prospection"
               - Attendez que le scraping et l'enrichissement se terminent

            3. **Analysez les résultats**
               - Consultez les statistiques
               - Filtrez les contacts par score/catégorie
               - Téléchargez en CSV

            ### 💡 Conseils

            - **Soyez précis** : "fabricants vérandas Lyon" > "vérandas"
            - **Scrapez plus** : 200 entreprises → ~50 contacts qualifiés
            - **Ajustez le score** : Score 50 = bon équilibre qualité/quantité

            ### ⚡ Temps d'exécution

            - Scraping: 2-5 minutes
            - Enrichissement: 30-60 minutes (selon nombre)
            """)

if __name__ == "__main__":
    main()
