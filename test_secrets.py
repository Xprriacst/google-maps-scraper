#!/usr/bin/env python3
"""
Script de debug pour tester la lecture des secrets Streamlit
"""

import streamlit as st

st.title("🔍 Test des Secrets")

st.write("## Secrets disponibles")

try:
    # Afficher tous les secrets (masqués)
    st.write("Clés disponibles dans st.secrets:")
    for key in st.secrets.keys():
        st.write(f"- `{key}`")

    st.write("\n## Test des clés spécifiques")

    # Test DROPCONTACT_API_KEY
    if "DROPCONTACT_API_KEY" in st.secrets:
        val = st.secrets["DROPCONTACT_API_KEY"]
        st.success(f"✅ DROPCONTACT_API_KEY trouvée (longueur: {len(val)})")
    else:
        st.error("❌ DROPCONTACT_API_KEY NOT FOUND")

    # Test OPENAI_API_KEY
    if "OPENAI_API_KEY" in st.secrets:
        val = st.secrets["OPENAI_API_KEY"]
        st.success(f"✅ OPENAI_API_KEY trouvée (longueur: {len(val)})")
    else:
        st.error("❌ OPENAI_API_KEY NOT FOUND")

    # Test avec utils.get_env
    st.write("\n## Test avec utils.get_env()")
    from utils import get_env

    dropcontact = get_env("DROPCONTACT_API_KEY")
    if dropcontact:
        st.success(f"✅ get_env('DROPCONTACT_API_KEY') = {dropcontact[:10]}... (longueur: {len(dropcontact)})")
    else:
        st.error("❌ get_env('DROPCONTACT_API_KEY') retourne None")

    openai = get_env("OPENAI_API_KEY")
    if openai:
        st.success(f"✅ get_env('OPENAI_API_KEY') = {openai[:10]}... (longueur: {len(openai)})")
    else:
        st.error("❌ get_env('OPENAI_API_KEY') retourne None")

except Exception as e:
    st.error(f"Erreur: {e}")
    import traceback
    st.code(traceback.format_exc())
