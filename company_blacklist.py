#!/usr/bin/env python3
"""
Gestion de la blacklist d'entreprises
Permet d'exclure certaines entreprises récurrentes (ex: grandes chaînes présentes partout)
"""

import os
import json
from typing import List, Set
from pathlib import Path


class CompanyBlacklist:
    """Gère la liste des entreprises à exclure du scraping"""

    def __init__(self, blacklist_file: str = None):
        """
        Initialise la blacklist

        Args:
            blacklist_file: Chemin vers le fichier de blacklist (JSON)
        """
        self.blacklist_file = blacklist_file or 'company_blacklist.json'
        self.blacklist: Set[str] = set()
        self.load()

    def load(self):
        """Charge la blacklist depuis le fichier"""
        if os.path.exists(self.blacklist_file):
            try:
                with open(self.blacklist_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Normaliser les noms (minuscules, sans espaces superflus)
                    self.blacklist = {self._normalize(name) for name in data.get('blacklist', [])}
                print(f"✅ Blacklist chargée: {len(self.blacklist)} entreprise(s)")
            except Exception as e:
                print(f"⚠️  Erreur lecture blacklist: {e}")
                self.blacklist = set()
        else:
            print(f"ℹ️  Aucune blacklist trouvée, création de {self.blacklist_file}")
            self.save()

    def save(self):
        """Sauvegarde la blacklist dans le fichier"""
        try:
            data = {
                'blacklist': sorted(list(self.blacklist)),
                'description': 'Liste des entreprises à exclure du scraping',
                'last_updated': str(Path(self.blacklist_file).stat().st_mtime) if os.path.exists(self.blacklist_file) else None
            }
            with open(self.blacklist_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"✅ Blacklist sauvegardée: {len(self.blacklist)} entreprise(s)")
        except Exception as e:
            print(f"❌ Erreur sauvegarde blacklist: {e}")

    def _normalize(self, company_name: str) -> str:
        """Normalise un nom d'entreprise pour la comparaison"""
        if not company_name:
            return ""
        # Minuscules, suppression espaces multiples, trim
        return ' '.join(company_name.lower().strip().split())

    def is_blacklisted(self, company_name: str) -> bool:
        """
        Vérifie si une entreprise est dans la blacklist

        Args:
            company_name: Nom de l'entreprise

        Returns:
            True si blacklistée, False sinon
        """
        normalized = self._normalize(company_name)
        return normalized in self.blacklist

    def add(self, company_name: str):
        """
        Ajoute une entreprise à la blacklist

        Args:
            company_name: Nom de l'entreprise
        """
        if not company_name:
            return

        normalized = self._normalize(company_name)
        if normalized not in self.blacklist:
            self.blacklist.add(normalized)
            print(f"✅ Ajouté à la blacklist: {company_name}")
            self.save()
        else:
            print(f"ℹ️  Déjà dans la blacklist: {company_name}")

    def add_multiple(self, company_names: List[str]):
        """
        Ajoute plusieurs entreprises à la blacklist

        Args:
            company_names: Liste de noms d'entreprises
        """
        added = 0
        for name in company_names:
            normalized = self._normalize(name)
            if normalized and normalized not in self.blacklist:
                self.blacklist.add(normalized)
                added += 1

        if added > 0:
            print(f"✅ Ajouté {added} entreprise(s) à la blacklist")
            self.save()

    def remove(self, company_name: str):
        """
        Retire une entreprise de la blacklist

        Args:
            company_name: Nom de l'entreprise
        """
        normalized = self._normalize(company_name)
        if normalized in self.blacklist:
            self.blacklist.remove(normalized)
            print(f"✅ Retiré de la blacklist: {company_name}")
            self.save()
        else:
            print(f"ℹ️  Pas dans la blacklist: {company_name}")

    def filter_companies(self, companies: List[dict], name_key: str = 'name') -> List[dict]:
        """
        Filtre une liste d'entreprises en excluant celles de la blacklist

        Args:
            companies: Liste d'entreprises (dicts)
            name_key: Clé du nom d'entreprise dans les dicts

        Returns:
            Liste filtrée sans les entreprises blacklistées
        """
        before = len(companies)
        filtered = [c for c in companies if not self.is_blacklisted(c.get(name_key, ''))]
        after = len(filtered)

        if before > after:
            print(f"🚫 Filtrage blacklist: {before - after} entreprise(s) exclue(s)")

        return filtered

    def get_all(self) -> List[str]:
        """Retourne la liste complète de la blacklist"""
        return sorted(list(self.blacklist))

    def clear(self):
        """Vide complètement la blacklist"""
        self.blacklist.clear()
        self.save()
        print("🗑️  Blacklist vidée")


# Exemple de blacklist pour les vérandas (grandes chaînes nationales)
VERANDA_BLACKLIST_EXAMPLE = [
    "Véranda Rideau",
    "Akena Véranda",
    "Vie & Véranda",
    "Gustave Rideau",
    "Technal",
    "Tryba",
    "Point.P",
    "Leroy Merlin",
]


if __name__ == "__main__":
    # Test du système de blacklist
    print("\n" + "="*60)
    print("🧪 TEST: Système de blacklist")
    print("="*60)

    bl = CompanyBlacklist('test_blacklist.json')

    # Ajouter des entreprises
    bl.add_multiple(VERANDA_BLACKLIST_EXAMPLE)

    # Tester le filtrage
    companies = [
        {'name': 'Véranda Concept', 'city': 'Paris'},
        {'name': 'AKENA VERANDA', 'city': 'Lyon'},  # Devrait être filtré
        {'name': 'Véranda Premium', 'city': 'Marseille'},
        {'name': 'Vie & Véranda', 'city': 'Toulouse'},  # Devrait être filtré
    ]

    print("\n📋 Entreprises avant filtrage:")
    for c in companies:
        print(f"  - {c['name']}")

    filtered = bl.filter_companies(companies)

    print("\n✅ Entreprises après filtrage:")
    for c in filtered:
        print(f"  - {c['name']}")

    # Nettoyage
    if os.path.exists('test_blacklist.json'):
        os.remove('test_blacklist.json')
