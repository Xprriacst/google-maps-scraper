"""
Configuration et constantes pour le scraper Google Maps
"""

# Configuration Apify
APIFY_ACTOR_ID = "compass/crawler-google-places"
DEFAULT_MAX_RESULTS = 50
DEFAULT_LANGUAGE = "fr"

# Configuration Google Sheets
SHEET_NAME = "Entreprises"
SHEET_HEADERS = [
    'Nom',
    'Adresse', 
    'Téléphone',
    'Site Web',
    'Note',
    'Nombre Avis',
    'Catégorie',
    'Nom Contact',
    'Email Contact',
    'Poste Contact',
    'Date Ajout',
    'URL Google Maps'
]

# Configuration GoHighLevel
GHL_API_URL = "https://rest.gohighlevel.com/v1/contacts/"
GHL_TAGS = ["Google Maps Scraper", "Lead"]

# Configuration Hunter.io
HUNTER_API_URL = "https://api.hunter.io/v2/domain-search"

# Rate limiting (en secondes)
RATE_LIMIT_GOOGLE_SHEETS = 0.5
RATE_LIMIT_GOHIGHLEVEL = 0.5
RATE_LIMIT_HUNTER = 1.0

# Patterns d'emails communs pour les entreprises
COMMON_EMAIL_PATTERNS = [
    "contact@{domain}",
    "info@{domain}",
    "hello@{domain}",
    "bonjour@{domain}"
]
