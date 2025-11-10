#!/usr/bin/env python3
"""
Module d'estimation de taille de marché via Google Places Aggregate API
Permet d'estimer le nombre total d'entreprises pour une recherche donnée
"""

import requests
from typing import Dict, List, Optional
from utils import get_env


class MarketSizeEstimator:
    """Estime la taille du marché pour une recherche Google Maps"""

    def __init__(self, api_key: str = None):
        """
        Initialise l'estimateur de taille de marché

        Args:
            api_key: Clé API Google Places (si None, charge depuis env)
        """
        self.api_key = api_key or get_env('GOOGLE_PLACES_API_KEY')

        if not self.api_key:
            print("⚠️  GOOGLE_PLACES_API_KEY non configurée")
            self.enabled = False
        else:
            self.enabled = True
            print("✅ Market Size Estimator activé")

    def estimate_market_size(self, query: str, location: Dict = None,
                            method: str = 'aggregate') -> Dict:
        """
        Estime la taille du marché pour une requête donnée

        Args:
            query: Requête de recherche (ex: "véranda", "boulangerie")
            location: Localisation (ex: {'country': 'FR'}, {'region': 'Île-de-France'})
            method: Méthode d'estimation ('aggregate', 'nearby', 'text')

        Returns:
            Dict avec 'estimated_count', 'confidence', 'method_used', 'details'
        """
        if not self.enabled:
            return {
                'estimated_count': 0,
                'confidence': 0.0,
                'method_used': 'disabled',
                'details': 'API key non configurée'
            }

        print(f"\n📊 Estimation taille de marché pour: '{query}'")

        # Définir la localisation par défaut (France)
        if location is None:
            location = {'country': 'FR'}

        # Choisir la méthode d'estimation
        if method == 'aggregate':
            result = self._estimate_with_aggregate_api(query, location)
        elif method == 'nearby':
            result = self._estimate_with_nearby_search(query, location)
        elif method == 'text':
            result = self._estimate_with_text_search(query, location)
        else:
            result = {
                'estimated_count': 0,
                'confidence': 0.0,
                'method_used': 'unknown',
                'details': f"Méthode '{method}' inconnue"
            }

        print(f"✅ Estimation: {result['estimated_count']} entreprises (confiance: {result['confidence']:.0%})")

        return result

    def _estimate_with_aggregate_api(self, query: str, location: Dict) -> Dict:
        """
        Estime via Places Aggregate API (nouvelle API Google)

        Args:
            query: Requête de recherche
            location: Localisation

        Returns:
            Dict avec estimation
        """
        try:
            # Places Aggregate API endpoint
            url = "https://places.googleapis.com/v1/places:aggregate"

            headers = {
                'Content-Type': 'application/json',
                'X-Goog-Api-Key': self.api_key,
                'X-Goog-FieldMask': 'count'
            }

            # Construire le body de la requête
            body = {
                'textQuery': query,
            }

            # Ajouter les contraintes de localisation
            if 'country' in location:
                body['locationRestriction'] = {
                    'region': {
                        'place': f"country:{location['country']}"
                    }
                }
            elif 'region' in location:
                body['textQuery'] = f"{query} {location['region']}"

            # Appel API
            response = requests.post(url, json=body, headers=headers, timeout=30)

            if response.status_code == 200:
                data = response.json()
                count = data.get('count', 0)

                # Si count > 100, Google ne retourne qu'une estimation
                if count > 100:
                    confidence = 0.7  # Estimation Google
                else:
                    confidence = 0.95  # Compte exact

                return {
                    'estimated_count': count,
                    'confidence': confidence,
                    'method_used': 'places_aggregate_api',
                    'details': 'Estimation officielle Google Places Aggregate API',
                    'is_exact': count <= 100
                }
            else:
                error_msg = f"API error: {response.status_code}"
                if response.status_code == 403:
                    error_msg = "Places Aggregate API non activée ou quota dépassé"
                elif response.status_code == 400:
                    error_msg = f"Requête invalide: {response.text}"

                print(f"  ⚠️  Erreur Places Aggregate API: {error_msg}")

                # Fallback sur Text Search
                return self._estimate_with_text_search(query, location)

        except Exception as e:
            print(f"  ⚠️  Erreur estimation: {e}")
            # Fallback sur Text Search
            return self._estimate_with_text_search(query, location)

    def _estimate_with_text_search(self, query: str, location: Dict) -> Dict:
        """
        Estime via Places Text Search (fallback)
        Fait plusieurs recherches avec pagination pour estimer le total

        Args:
            query: Requête de recherche
            location: Localisation

        Returns:
            Dict avec estimation
        """
        try:
            url = "https://places.googleapis.com/v1/places:searchText"

            headers = {
                'Content-Type': 'application/json',
                'X-Goog-Api-Key': self.api_key,
                'X-Goog-FieldMask': 'places.id,nextPageToken'
            }

            # Construire la requête avec localisation
            text_query = query
            if 'country' in location:
                text_query = f"{query} in {location['country']}"
            elif 'region' in location:
                text_query = f"{query} in {location['region']}"

            body = {
                'textQuery': text_query,
                'maxResultCount': 20  # Max par requête
            }

            # Première requête
            response = requests.post(url, json=body, headers=headers, timeout=30)

            if response.status_code != 200:
                print(f"  ⚠️  Erreur Text Search: {response.status_code}")
                return {
                    'estimated_count': 0,
                    'confidence': 0.0,
                    'method_used': 'text_search_failed',
                    'details': f"Erreur API: {response.status_code}"
                }

            data = response.json()
            places = data.get('places', [])
            total_count = len(places)
            next_page_token = data.get('nextPageToken')

            # Paginer jusqu'à 100 résultats pour estimer
            pages_checked = 1
            max_pages = 5  # Limiter à 5 pages (100 résultats) pour économiser

            while next_page_token and pages_checked < max_pages:
                body['pageToken'] = next_page_token
                response = requests.post(url, json=body, headers=headers, timeout=30)

                if response.status_code == 200:
                    data = response.json()
                    places = data.get('places', [])
                    total_count += len(places)
                    next_page_token = data.get('nextPageToken')
                    pages_checked += 1
                else:
                    break

            # Si on a atteint la limite de pages, extrapoler
            if next_page_token:
                # Il y a encore des résultats, extrapoler
                estimated_count = int(total_count * 1.5)  # Extrapolation conservative
                confidence = 0.6
                details = f"Estimation basée sur {total_count} résultats paginés (plus de résultats disponibles)"
            else:
                # On a tout récupéré
                estimated_count = total_count
                confidence = 0.9
                details = f"Compte basé sur {pages_checked} page(s) de résultats"

            return {
                'estimated_count': estimated_count,
                'confidence': confidence,
                'method_used': 'places_text_search',
                'details': details,
                'pages_checked': pages_checked
            }

        except Exception as e:
            print(f"  ⚠️  Erreur Text Search: {e}")
            return {
                'estimated_count': 0,
                'confidence': 0.0,
                'method_used': 'text_search_error',
                'details': str(e)
            }

    def _estimate_with_nearby_search(self, query: str, location: Dict) -> Dict:
        """
        Estime via Nearby Search (nécessite des coordonnées)

        Args:
            query: Requête de recherche
            location: Doit contenir 'lat', 'lng', 'radius'

        Returns:
            Dict avec estimation
        """
        if 'lat' not in location or 'lng' not in location:
            return {
                'estimated_count': 0,
                'confidence': 0.0,
                'method_used': 'nearby_search_invalid',
                'details': 'Nearby Search nécessite lat/lng'
            }

        try:
            url = "https://places.googleapis.com/v1/places:searchNearby"

            headers = {
                'Content-Type': 'application/json',
                'X-Goog-Api-Key': self.api_key,
                'X-Goog-FieldMask': 'places.id'
            }

            body = {
                'includedTypes': [query],
                'maxResultCount': 20,
                'locationRestriction': {
                    'circle': {
                        'center': {
                            'latitude': location['lat'],
                            'longitude': location['lng']
                        },
                        'radius': location.get('radius', 50000)  # 50km par défaut
                    }
                }
            }

            response = requests.post(url, json=body, headers=headers, timeout=30)

            if response.status_code == 200:
                data = response.json()
                places = data.get('places', [])
                count = len(places)

                return {
                    'estimated_count': count,
                    'confidence': 0.8,
                    'method_used': 'places_nearby_search',
                    'details': f"Résultats dans un rayon de {location.get('radius', 50000)}m"
                }
            else:
                print(f"  ⚠️  Erreur Nearby Search: {response.status_code}")
                return {
                    'estimated_count': 0,
                    'confidence': 0.0,
                    'method_used': 'nearby_search_failed',
                    'details': f"Erreur API: {response.status_code}"
                }

        except Exception as e:
            print(f"  ⚠️  Erreur Nearby Search: {e}")
            return {
                'estimated_count': 0,
                'confidence': 0.0,
                'method_used': 'nearby_search_error',
                'details': str(e)
            }

    def estimate_by_regions(self, query: str, regions: List[str]) -> Dict:
        """
        Estime en découpant par régions/départements

        Args:
            query: Requête de recherche
            regions: Liste de régions/départements (ex: ['Paris', 'Lyon', ...])

        Returns:
            Dict avec estimation totale et détails par région
        """
        print(f"\n📊 Estimation par régions pour: '{query}'")
        print(f"   Nombre de régions à scraper: {len(regions)}")

        total_count = 0
        regional_breakdown = {}

        for i, region in enumerate(regions, 1):
            print(f"  [{i}/{len(regions)}] {region}...", end=' ')

            result = self.estimate_market_size(
                query=query,
                location={'region': region},
                method='text'
            )

            count = result['estimated_count']
            total_count += count
            regional_breakdown[region] = count

            print(f"{count} résultats")

        print(f"\n✅ Total estimé: {total_count} entreprises")

        return {
            'estimated_count': total_count,
            'confidence': 0.85,  # Bonne confiance avec découpage régional
            'method_used': 'regional_aggregation',
            'details': f"Agrégation de {len(regions)} régions",
            'regional_breakdown': regional_breakdown
        }


# Départements français pour estimation exhaustive
FRENCH_DEPARTMENTS = [
    'Ain', 'Aisne', 'Allier', 'Alpes-de-Haute-Provence', 'Hautes-Alpes',
    'Alpes-Maritimes', 'Ardèche', 'Ardennes', 'Ariège', 'Aube', 'Aude',
    'Aveyron', 'Bouches-du-Rhône', 'Calvados', 'Cantal', 'Charente',
    'Charente-Maritime', 'Cher', 'Corrèze', 'Corse-du-Sud', 'Haute-Corse',
    'Côte-d\'Or', 'Côtes-d\'Armor', 'Creuse', 'Dordogne', 'Doubs', 'Drôme',
    'Eure', 'Eure-et-Loir', 'Finistère', 'Gard', 'Haute-Garonne', 'Gers',
    'Gironde', 'Hérault', 'Ille-et-Vilaine', 'Indre', 'Indre-et-Loire',
    'Isère', 'Jura', 'Landes', 'Loir-et-Cher', 'Loire', 'Haute-Loire',
    'Loire-Atlantique', 'Loiret', 'Lot', 'Lot-et-Garonne', 'Lozère',
    'Maine-et-Loire', 'Manche', 'Marne', 'Haute-Marne', 'Mayenne',
    'Meurthe-et-Moselle', 'Meuse', 'Morbihan', 'Moselle', 'Nièvre', 'Nord',
    'Oise', 'Orne', 'Pas-de-Calais', 'Puy-de-Dôme', 'Pyrénées-Atlantiques',
    'Hautes-Pyrénées', 'Pyrénées-Orientales', 'Bas-Rhin', 'Haut-Rhin',
    'Rhône', 'Haute-Saône', 'Saône-et-Loire', 'Sarthe', 'Savoie',
    'Haute-Savoie', 'Paris', 'Seine-Maritime', 'Seine-et-Marne', 'Yvelines',
    'Deux-Sèvres', 'Somme', 'Tarn', 'Tarn-et-Garonne', 'Var', 'Vaucluse',
    'Vendée', 'Vienne', 'Haute-Vienne', 'Vosges', 'Yonne',
    'Territoire de Belfort', 'Essonne', 'Hauts-de-Seine', 'Seine-Saint-Denis',
    'Val-de-Marne', 'Val-d\'Oise'
]


if __name__ == "__main__":
    # Test du module
    print("=== Test Market Size Estimator ===\n")

    try:
        estimator = MarketSizeEstimator()

        if not estimator.enabled:
            print("⚠️  Google Places API non configurée")
            print("💡 Ajoutez GOOGLE_PLACES_API_KEY dans votre .env")
        else:
            # Test 1: Estimation simple avec Aggregate API
            print("\n--- Test 1: Estimation vérandas France ---")
            result = estimator.estimate_market_size(
                query="véranda",
                location={'country': 'FR'},
                method='aggregate'
            )

            print(f"\nRésultat:")
            print(f"  Nombre estimé: {result['estimated_count']}")
            print(f"  Confiance: {result['confidence']:.0%}")
            print(f"  Méthode: {result['method_used']}")
            print(f"  Détails: {result['details']}")

            # Test 2: Estimation par régions (échantillon)
            print("\n--- Test 2: Estimation par échantillon de régions ---")
            sample_regions = ['Paris', 'Lyon', 'Marseille', 'Toulouse', 'Nantes']
            result2 = estimator.estimate_by_regions(
                query="véranda",
                regions=sample_regions
            )

            print(f"\nRésultat régional:")
            print(f"  Total: {result2['estimated_count']}")
            print(f"  Confiance: {result2['confidence']:.0%}")
            print(f"  Détail par région:")
            for region, count in result2['regional_breakdown'].items():
                print(f"    - {region}: {count}")

    except Exception as e:
        print(f"❌ Erreur: {e}")
