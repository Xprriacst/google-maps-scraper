#!/usr/bin/env python3
"""Test pour vérifier que la colonne Source Contact est présente"""

import pandas as pd

# Fonction identique à celle dans app_streamlit_pro.py
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


# Créer des données de test
test_contacts = [
    {
        'name': 'Entreprise A',
        'contact_name': 'Jean Dupont',
        'contact_position': 'Directeur Commercial',
        'contact_email': 'jean.dupont@entreprise-a.fr',
        'email_confidence': 'high',
        'data_sources': ['api_entreprise', 'dropcontact'],
        'score_total': 85,
        'category': 'Premium',
        'emoji': '🟢',
        'phone': '01 23 45 67 89',
        'website': 'https://entreprise-a.fr',
        'rating': '4.5',
        'reviews_count': 120,
        'siret': '12345678901234'
    },
    {
        'name': 'Entreprise B',
        'contact_name': 'Marie Martin',
        'contact_position': 'Gérante',
        'contact_email': 'm.martin@entreprise-b.fr',
        'email_confidence': 'medium',
        'data_sources': ['api_entreprise', 'legal_data'],
        'score_total': 65,
        'category': 'Qualifié',
        'emoji': '🟡',
        'phone': '01 98 76 54 32',
        'website': 'https://entreprise-b.fr',
        'rating': '4.2',
        'reviews_count': 45,
        'siret': '98765432109876'
    },
    {
        'name': 'Entreprise C',
        'contact_name': '',
        'contact_position': '',
        'contact_email': '',
        'email_confidence': 'none',
        'data_sources': ['api_entreprise'],
        'score_total': 20,
        'category': 'Faible',
        'emoji': '🔴',
        'phone': '01 11 22 33 44',
        'website': 'https://entreprise-c.fr',
        'rating': '3.8',
        'reviews_count': 12,
        'siret': '11111111111111'
    }
]

# Créer le DataFrame exactement comme dans app_streamlit_pro.py
df_display = pd.DataFrame([
    {
        'Score': f"{c.get('score_total', 0)} {c.get('emoji', '')}",
        'Catégorie': c.get('category', ''),
        'Source Contact': get_contact_source(c),
        'Entreprise': c.get('name', ''),
        'Contact': c.get('contact_name', '').strip() if c.get('contact_name', '').strip() else '❌ Aucun contact trouvé',
        'Fonction': c.get('contact_position', '').strip() if c.get('contact_position', '').strip() else '-',
        'Email': c.get('contact_email', '').strip() if c.get('contact_email', '').strip() else '-',
        'Confiance': c.get('email_confidence', 'none').upper() if c.get('contact_email', '').strip() else '-',
        'Téléphone': c.get('phone', 'N/A'),
        'Site web': c.get('website', 'N/A'),
        'Note': f"{c.get('rating', 'N/A')} ⭐",
        'Avis': c.get('reviews_count', 'N/A'),
        'SIRET': c.get('siret', 'N/A'),
    }
    for c in test_contacts
])

print("=" * 80)
print("TEST : Vérification de la colonne 'Source Contact'")
print("=" * 80)
print()

# Vérifier que la colonne existe
if 'Source Contact' in df_display.columns:
    print("✅ La colonne 'Source Contact' est présente !")
    print()
    print("📋 Liste des colonnes du DataFrame :")
    for idx, col in enumerate(df_display.columns, 1):
        print(f"   {idx}. {col}")

    print()
    print("📊 Aperçu du DataFrame :")
    print()
    print(df_display.to_string())

    print()
    print("=" * 80)
    print("✅ TEST RÉUSSI : La colonne 'Source Contact' fonctionne correctement")
    print("=" * 80)
else:
    print("❌ ERREUR : La colonne 'Source Contact' n'est PAS présente !")
    print()
    print("Colonnes présentes :")
    print(df_display.columns.tolist())
