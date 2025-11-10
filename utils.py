#!/usr/bin/env python3
"""
Utilitaires pour gérer les variables d'environnement
Compatible avec .env (local) et Streamlit secrets (cloud)
"""

import os
from dotenv import load_dotenv

# Charger .env si disponible (mode local)
load_dotenv()

def get_env(key, default=None):
    """
    Récupère une variable d'environnement
    Essaie d'abord Streamlit secrets, puis .env, puis les variables d'environnement

    Args:
        key: Nom de la variable
        default: Valeur par défaut si non trouvée

    Returns:
        Valeur de la variable ou default
    """
    # Essayer Streamlit secrets (mode cloud)
    try:
        import streamlit as st
        if hasattr(st, 'secrets') and key in st.secrets:
            return st.secrets[key]
    except (ImportError, FileNotFoundError, KeyError):
        pass

    # Essayer .env ou variables d'environnement (mode local)
    return os.getenv(key, default)


def get_gcp_credentials():
    """
    Récupère les credentials Google Cloud
    Compatible avec credentials.json (local) et Streamlit secrets (cloud)

    Returns:
        Path vers credentials.json ou dict des credentials depuis Streamlit
    """
    # Mode Streamlit Cloud : utiliser les secrets
    try:
        import streamlit as st
        if hasattr(st, 'secrets') and 'gcp_service_account' in st.secrets:
            # Retourner les credentials depuis Streamlit secrets
            return dict(st.secrets['gcp_service_account'])
    except (ImportError, FileNotFoundError, KeyError):
        pass

    # Mode local : utiliser credentials.json
    if os.path.exists('credentials.json'):
        return 'credentials.json'

    return None
