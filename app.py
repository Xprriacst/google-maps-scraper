#!/usr/bin/env python3
"""Interface Streamlit pour lancer le scraper Google Maps"""

import streamlit as st

from scraper import GoogleMapsScraper


def run_scraper(search_query: str, max_results: int) -> None:
    """Exécute le scraper avec les paramètres fournis."""

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
        - Rechercher automatiquement les emails des entreprises
        - Ajouter les données à Google Sheets
        - Envoyer vers GoHighLevel (si configuré)
        """
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

        submitted = st.form_submit_button("🚀 Lancer le scraping")

    if submitted:
        if not search_query.strip():
            st.error("Veuillez saisir une recherche valide.")
            return

        with st.spinner(f"Scraping en cours… {search_query}"):
            try:
                run_scraper(search_query, max_results)
                st.success("✅ Scraping terminé. Consultez Google Sheets pour voir les résultats.")
            except Exception as exc:
                st.error(f"❌ Erreur lors du scraping: {exc}")


if __name__ == "__main__":
    main()
