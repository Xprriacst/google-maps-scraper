#!/usr/bin/env python3
"""
Interface Streamlit pour le scraper en 2 étapes
Étape 1 : Scraper les entreprises
Étape 2 : Chercher les contacts
"""

import streamlit as st
from scraper_two_step import TwoStepScraper
from company_blacklist import CompanyBlacklist


def main():
    st.set_page_config(
        page_title="Google Maps Scraper 2.0",
        page_icon="🗺️",
        layout="wide"
    )

    st.title("🗺️ Google Maps Scraper 2.0")
    st.markdown("### Workflow en 2 étapes : **Entreprises → People**")

    # Sidebar : Configuration
    with st.sidebar:
        st.header("⚙️ Configuration")

        # Blacklist management
        st.subheader("🚫 Blacklist Entreprises")
        blacklist = CompanyBlacklist()

        st.write(f"**{len(blacklist.get_all())} entreprise(s) blacklistée(s)**")

        with st.expander("Voir/Modifier la blacklist"):
            current_blacklist = "\n".join(blacklist.get_all())
            st.text_area("Entreprises à exclure (une par ligne)", current_blacklist, height=150, key="blacklist_view")

            new_company = st.text_input("Ajouter une entreprise")
            if st.button("➕ Ajouter"):
                if new_company:
                    blacklist.add(new_company)
                    st.success(f"✅ Ajouté: {new_company}")
                    st.rerun()

    # Main content : 2 colonnes pour les 2 étapes
    col1, col2 = st.columns(2)

    # === ÉTAPE 1 : ENTREPRISES ===
    with col1:
        st.header("1️⃣ Scraper les Entreprises")
        st.markdown("Recherche sur **Google Maps** + enrichissement")

        with st.form("form_companies"):
            search_query = st.text_input(
                "🔍 Recherche Google Maps",
                placeholder="ex: fabricants de vérandas à Paris",
                key="search_companies"
            )

            max_results = st.slider(
                "Nombre max d'entreprises",
                min_value=10,
                max_value=200,
                value=50,
                step=10,
                key="max_companies"
            )

            location = st.text_input(
                "📍 Localisation (optionnel)",
                placeholder="ex: Paris, Île-de-France",
                key="location_filter"
            )

            submit_companies = st.form_submit_button(
                "🏢 Lancer le scraping ENTREPRISES",
                type="primary",
                use_container_width=True
            )

        if submit_companies:
            if not search_query:
                st.error("❌ Veuillez entrer une recherche")
            else:
                with st.spinner(f"🔄 Scraping de {max_results} entreprises..."):
                    try:
                        scraper = TwoStepScraper()
                        companies = scraper.scrape_companies(
                            search_query=search_query,
                            max_results=max_results,
                            location=location if location else None
                        )

                        st.success(f"✅ {len(companies)} entreprises scrapées !")
                        st.balloons()

                        # Afficher un aperçu
                        with st.expander("📊 Aperçu des entreprises"):
                            st.write(companies[:5])

                        st.info("👉 Consultez l'onglet **'Entreprises'** dans Google Sheets")

                    except Exception as e:
                        st.error(f"❌ Erreur: {e}")

    # === ÉTAPE 2 : PEOPLE ===
    with col2:
        st.header("2️⃣ Chercher les Contacts")
        st.markdown("Recherche multi-sources pour **chaque entreprise**")

        with st.form("form_people"):
            st.info("ℹ️ Cette étape utilise les entreprises de l'onglet 'Entreprises'")

            job_titles_input = st.text_area(
                "🎯 Titres de poste à cibler (un par ligne)",
                value="CEO\nFondateur\nGérant\nDirecteur Commercial\nDirecteur Général",
                height=150,
                key="job_titles"
            )

            max_contacts = st.slider(
                "Nombre max de contacts par entreprise",
                min_value=1,
                max_value=10,
                value=3,
                key="max_contacts"
            )

            st.markdown("**Sources utilisées** :")
            st.markdown("""
            - 🔵 **Apollo.io** (via Apify) - Prioritaire
            - 🟢 **Dropcontact** - Fallback
            - 🟡 **Email Finder** - Construction d'emails
            - 🟠 **Website Scraping** - Extraction depuis sites web
            """)

            submit_people = st.form_submit_button(
                "👥 Lancer la recherche de CONTACTS",
                type="primary",
                use_container_width=True
            )

        if submit_people:
            job_titles = [title.strip() for title in job_titles_input.split('\n') if title.strip()]

            if not job_titles:
                st.error("❌ Veuillez entrer au moins un titre de poste")
            else:
                with st.spinner(f"🔄 Recherche de contacts pour les entreprises..."):
                    try:
                        scraper = TwoStepScraper()
                        contacts = scraper.scrape_people(
                            job_titles=job_titles,
                            max_contacts_per_company=max_contacts
                        )

                        st.success(f"✅ {len(contacts)} contacts trouvés !")
                        st.balloons()

                        # Afficher un aperçu
                        with st.expander("📊 Aperçu des contacts"):
                            st.write(contacts[:5])

                        st.info("👉 Consultez l'onglet **'People'** dans Google Sheets")

                        # Stats par source
                        st.subheader("📈 Statistiques par source")
                        sources = {}
                        for contact in contacts:
                            source = contact.get('source_principale', 'unknown')
                            sources[source] = sources.get(source, 0) + 1

                        for source, count in sources.items():
                            emoji = {
                                'apollo': '🔵',
                                'dropcontact': '🟢',
                                'constructed': '🟡',
                                'scraped': '🟠'
                            }.get(source, '⚪')
                            st.write(f"{emoji} **{source.capitalize()}**: {count} contact(s)")

                    except Exception as e:
                        st.error(f"❌ Erreur: {e}")

    # Footer
    st.markdown("---")
    st.markdown("""
    ### 📝 Comment ça marche ?

    **Étape 1 - Entreprises** :
    1. Scraping Google Maps
    2. Filtrage avec la blacklist (exclut les grosses chaînes)
    3. Enrichissement (SIRET, effectifs, CA)
    4. Export vers l'onglet **'Entreprises'**

    **Étape 2 - People** :
    1. Lecture des entreprises depuis l'onglet
    2. Recherche de contacts via **4 sources** différentes
    3. **Colonnes séparées par source** (Apollo, Dropcontact, EmailFinder, Website)
    4. Export vers l'onglet **'People'**

    💡 **Avantage** : Ne recherchez les contacts qu'une seule fois !
    """)


if __name__ == "__main__":
    main()
