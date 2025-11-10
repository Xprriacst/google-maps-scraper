#!/usr/bin/env python3
"""Interface Streamlit pour lancer le scraper Google Maps"""

import streamlit as st

from scraper import GoogleMapsScraper
from scraper_pro import GoogleMapsScraperPro


def run_scraper(search_query: str, max_results: int, mode: str = 'simple',
                min_score: int = 70, use_adaptive_targeting: bool = True) -> None:
    """Exécute le scraper avec les paramètres fournis."""

    if mode == 'pro':
        scraper = GoogleMapsScraperPro(min_score=min_score, use_adaptive_targeting=use_adaptive_targeting)
    else:
        scraper = GoogleMapsScraper()

    scraper.run(search_query, max_results)


def main() -> None:
    st.set_page_config(
        page_title="Google Maps Scraper",
        page_icon="🗺️",
        layout="centered"
    )

    st.title("🗺️ Google Maps Scraper")
    st.markdown(
        """
        Cet outil permet de :

        - Scraper des entreprises depuis Google Maps via Apify
        - **3 types de contacts** : Email Pattern, Email Site, Contact Décideur
        - **Mode PRO** : Enrichissement + Scoring qualité
        - Ajouter les données à Google Sheets
        - Envoyer vers GoHighLevel (si configuré)
        """
    )

    # Choix du mode
    mode = st.radio(
        "Mode de scraping",
        options=['simple', 'pro'],
        format_func=lambda x: '🚀 Mode Simple (Contacts 1 & 2)' if x == 'simple' else '🎯 Mode PRO (3 contacts + Scoring)',
        horizontal=True
    )

    with st.form("scraper_form"):
        search_query = st.text_input(
            "Recherche Google Maps",
            placeholder="ex: restaurants à Paris"
        )
        max_results = st.slider(
            "Nombre d'entreprises",
            min_value=10,
            max_value=200,
            value=50,
            step=10
        )

        # Options Mode PRO
        min_score = 70
        use_adaptive_targeting = True

        if mode == 'pro':
            min_score = st.slider(
                "Score minimum (qualification)",
                min_value=0,
                max_value=100,
                value=70,
                step=5,
                help="Filtrer les entreprises avec un score ≥ à cette valeur"
            )

            use_adaptive_targeting = st.checkbox(
                "🎯 Cibler uniquement les décideurs (CEO, Directeurs, etc.)",
                value=True,
                help="Si décoché, trouve TOUS les contacts de l'équipe, peu importe leur poste"
            )

        # Bouton selon le mode
        if mode == 'pro':
            submitted = st.form_submit_button("🎯 Lancer le scraping PRO", type="primary")
        else:
            submitted = st.form_submit_button("🚀 Lancer le scraping", type="primary")

    if submitted:
        if not search_query.strip():
            st.error("Veuillez saisir une recherche valide.")
            return

        spinner_text = f"🎯 Scraping PRO en cours… {search_query} (Score ≥ {min_score})" if mode == 'pro' else f"🚀 Scraping en cours… {search_query}"

        with st.spinner(spinner_text):
            try:
                run_scraper(search_query, max_results, mode, min_score, use_adaptive_targeting)
                if mode == 'pro':
                    st.success("✅ Scraping PRO terminé ! Consultez l'onglet 'Prospection' dans Google Sheets.")
                else:
                    st.success("✅ Scraping terminé. Consultez l'onglet 'Entreprises' dans Google Sheets.")
            except Exception as exc:
                st.error(f"❌ Erreur lors du scraping: {exc}")


if __name__ == "__main__":
    main()
