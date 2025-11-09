#!/usr/bin/env python3
"""
Système de scoring de contacts pour la prospection B2B
Score de 0 à 100 basé sur la qualité email, contact et entreprise
"""

from typing import Dict


class ContactScorer:
    """
    Calcule un score de qualité pour chaque contact
    Score total: 0-100 points
    - Email: 40 points max
    - Contact: 30 points max
    - Entreprise: 30 points max
    """

    # Seuils de classification
    SCORE_PREMIUM = 80      # 🟢 Contact premium
    SCORE_QUALIFIED = 50    # 🟡 Contact qualifié
    SCORE_VERIFY = 20       # 🟠 Contact à vérifier
    # < 20               # 🔴 Contact faible

    def __init__(self):
        """Initialise le scorer"""
        pass

    def calculate_email_score(self, contact_data: Dict) -> int:
        """
        Calcule le score de qualité de l'email (40 points max)

        Critères:
        - Email HIGH confidence + nom vérifié: 40 points
        - Email MEDIUM + nom probable: 25 points
        - Email LOW générique: 10 points
        - Pas d'email: 0 points

        Args:
            contact_data: Dict avec email, email_confidence, contact_name

        Returns:
            Score sur 40 points
        """
        email = contact_data.get('contact_email', '')
        confidence = contact_data.get('email_confidence', 'none').lower()
        has_name = bool(contact_data.get('contact_name', '').strip())

        if not email:
            return 0

        # Vérifier si l'email est personnalisé (pas générique)
        generic_emails = ['contact', 'info', 'hello', 'bonjour', 'commercial', 'accueil']
        is_generic = any(gen in email.lower() for gen in generic_emails)

        # Calcul du score
        if confidence == 'high' and has_name and not is_generic:
            # Email trouvé sur le site + nom identifié + email personnalisé
            return 40
        elif confidence == 'high' and has_name:
            # Email trouvé + nom, mais peut-être générique
            return 35
        elif confidence == 'high':
            # Email trouvé mais pas de nom
            return 30
        elif confidence == 'medium' and has_name and not is_generic:
            # Email reconstruit + nom confirmé + personnalisé
            return 25
        elif confidence == 'medium' and has_name:
            # Email reconstruit + nom confirmé
            return 20
        elif confidence == 'medium':
            # Email reconstruit sans nom
            return 15
        elif confidence == 'low' and not is_generic:
            # Email généré mais essai de personnalisation
            return 10
        else:
            # Email générique type contact@
            return 5

    def calculate_contact_score(self, contact_data: Dict) -> int:
        """
        Calcule le score de qualité du contact (30 points max)

        Critères:
        - Nom + Fonction exacte trouvés: 30 points
        - Nom trouvé, fonction estimée: 20 points
        - Fonction seulement (pas de nom): 10 points
        - Rien: 5 points

        Args:
            contact_data: Dict avec contact_name, contact_position, data_sources

        Returns:
            Score sur 30 points
        """
        name = contact_data.get('contact_name', '').strip()
        position = contact_data.get('contact_position', '').strip()
        sources = contact_data.get('data_sources', [])
        linkedin = contact_data.get('contact_linkedin', '').strip()

        # Vérifier si c'est un vrai décideur
        decision_titles = [
            'directeur commercial', 'directrice commerciale',
            'directeur général', 'directrice générale',
            'gérant', 'gérante',
            'président', 'présidente', 'pdg',
            'ceo', 'directeur', 'directrice'
        ]

        is_decision_maker = any(title in position.lower() for title in decision_titles)

        # Calcul du score
        if name and position and is_decision_maker:
            # Nom + Fonction de décideur confirmée
            score = 30

            # Bonus si trouvé sur le site web (pas juste API)
            if 'website_team' in sources:
                score += 0  # Déjà au max

            # Bonus si LinkedIn trouvé
            if linkedin:
                score = min(score + 5, 30)  # Cap à 30

            return score

        elif name and position:
            # Nom + Fonction mais pas décideur
            return 20

        elif name and not position:
            # Nom seulement
            return 15

        elif position and is_decision_maker:
            # Fonction de décideur mais pas de nom
            return 15

        elif position:
            # Fonction seulement (non décideur)
            return 10

        else:
            # Rien de pertinent
            return 5

    def calculate_company_score(self, company_data: Dict) -> int:
        """
        Calcule le score de qualité de l'entreprise (30 points max)

        Critères:
        - Note > 4.5 + 50+ avis + site pro: 30 points
        - Note > 4.0 + 20+ avis + site: 20 points
        - Note > 3.5 + site basique: 10 points
        - Autres: 5 points

        Args:
            company_data: Dict avec rating, reviews_count, website, employees, etc.

        Returns:
            Score sur 30 points
        """
        rating = float(company_data.get('rating', 0) or 0)
        reviews = int(company_data.get('reviews_count', 0) or 0)
        website = company_data.get('website', '').strip()
        employees = company_data.get('employees', '')
        siret = company_data.get('siret', '').strip()

        score = 0

        # Score basé sur la note et les avis (20 points max)
        if rating >= 4.5 and reviews >= 50:
            score += 20
        elif rating >= 4.5 and reviews >= 20:
            score += 18
        elif rating >= 4.0 and reviews >= 50:
            score += 16
        elif rating >= 4.0 and reviews >= 20:
            score += 14
        elif rating >= 4.0 and reviews >= 10:
            score += 12
        elif rating >= 3.5 and reviews >= 20:
            score += 10
        elif rating >= 3.5 and reviews >= 10:
            score += 8
        elif rating >= 3.0:
            score += 5
        else:
            score += 2

        # Bonus pour site web (5 points max)
        if website:
            if any(ext in website for ext in ['.fr', '.com', '.net']):
                score += 5
            else:
                score += 3

        # Bonus pour SIRET trouvé (3 points max)
        if siret:
            score += 3

        # Bonus pour infos employés (2 points max)
        if employees:
            score += 2

        return min(score, 30)  # Cap à 30

    def get_final_score(self, contact_data: Dict, company_data: Dict) -> Dict:
        """
        Calcule le score final et la catégorie

        Args:
            contact_data: Données du contact
            company_data: Données de l'entreprise

        Returns:
            Dict avec scores détaillés, score total, catégorie, emoji
        """
        # Calculer les scores individuels
        email_score = self.calculate_email_score(contact_data)
        contact_score = self.calculate_contact_score(contact_data)
        company_score = self.calculate_company_score(company_data)

        # Score total
        total_score = email_score + contact_score + company_score

        # Déterminer la catégorie
        if total_score >= self.SCORE_PREMIUM:
            category = 'Premium'
            emoji = '🟢'
            priority = 1
            recommendation = 'Prospecter en priorité'
        elif total_score >= self.SCORE_QUALIFIED:
            category = 'Qualifié'
            emoji = '🟡'
            priority = 2
            recommendation = 'Prospecter ensuite'
        elif total_score >= self.SCORE_VERIFY:
            category = 'À vérifier'
            emoji = '🟠'
            priority = 3
            recommendation = 'Vérification manuelle recommandée'
        else:
            category = 'Faible'
            emoji = '🔴'
            priority = 4
            recommendation = 'Skip ou vérifier manuellement'

        return {
            'score_email': email_score,
            'score_contact': contact_score,
            'score_company': company_score,
            'score_total': total_score,
            'category': category,
            'emoji': emoji,
            'priority': priority,
            'recommendation': recommendation,
            'breakdown': {
                'email': f"{email_score}/40",
                'contact': f"{contact_score}/30",
                'company': f"{company_score}/30"
            }
        }

    def score_contact(self, full_data: Dict) -> Dict:
        """
        Score un contact complet (méthode simplifiée)

        Args:
            full_data: Dict contenant toutes les données (contact + entreprise)

        Returns:
            Dict avec le scoring complet
        """
        return self.get_final_score(full_data, full_data)

    def filter_by_score(self, contacts: list, min_score: int = 50) -> list:
        """
        Filtre les contacts par score minimum

        Args:
            contacts: Liste de contacts avec leurs scores
            min_score: Score minimum requis

        Returns:
            Liste filtrée et triée par score décroissant
        """
        filtered = [c for c in contacts if c.get('score_total', 0) >= min_score]
        filtered.sort(key=lambda x: x.get('score_total', 0), reverse=True)
        return filtered

    def get_stats(self, contacts: list) -> Dict:
        """
        Calcule les statistiques d'une liste de contacts

        Args:
            contacts: Liste de contacts scorés

        Returns:
            Dict avec statistiques
        """
        if not contacts:
            return {
                'total': 0,
                'premium': 0,
                'qualified': 0,
                'verify': 0,
                'weak': 0,
                'avg_score': 0
            }

        total = len(contacts)
        premium = sum(1 for c in contacts if c.get('score_total', 0) >= self.SCORE_PREMIUM)
        qualified = sum(1 for c in contacts if self.SCORE_QUALIFIED <= c.get('score_total', 0) < self.SCORE_PREMIUM)
        verify = sum(1 for c in contacts if self.SCORE_VERIFY <= c.get('score_total', 0) < self.SCORE_QUALIFIED)
        weak = sum(1 for c in contacts if c.get('score_total', 0) < self.SCORE_VERIFY)
        avg_score = sum(c.get('score_total', 0) for c in contacts) / total if total > 0 else 0

        return {
            'total': total,
            'premium': premium,
            'qualified': qualified,
            'verify': verify,
            'weak': weak,
            'avg_score': round(avg_score, 1),
            'premium_pct': round(premium / total * 100, 1) if total > 0 else 0,
            'qualified_pct': round(qualified / total * 100, 1) if total > 0 else 0
        }


if __name__ == "__main__":
    # Test du module
    import json

    scorer = ContactScorer()

    print("\n" + "="*60)
    print("🧪 TEST DU SYSTÈME DE SCORING")
    print("="*60)

    # Test Case 1: Contact premium
    test_contact_premium = {
        'contact_name': 'Jean Dupont',
        'contact_position': 'Directeur Commercial',
        'contact_email': 'jean.dupont@veranda-concept.fr',
        'email_confidence': 'high',
        'contact_linkedin': 'https://linkedin.com/in/jean-dupont',
        'data_sources': ['website_team', 'linkedin'],
        'rating': 4.7,
        'reviews_count': 85,
        'website': 'https://veranda-concept.fr',
        'siret': '123456789',
        'employees': '8'
    }

    print("\n📊 Test 1: Contact Premium")
    print(f"Contact: {test_contact_premium['contact_name']} - {test_contact_premium['contact_position']}")
    result = scorer.score_contact(test_contact_premium)
    print(json.dumps(result, indent=2, ensure_ascii=False))

    # Test Case 2: Contact qualifié
    test_contact_qualified = {
        'contact_name': '',
        'contact_position': 'Gérant',
        'contact_email': 'contact@entreprise.fr',
        'email_confidence': 'medium',
        'contact_linkedin': '',
        'data_sources': ['legal_data'],
        'rating': 4.2,
        'reviews_count': 25,
        'website': 'https://entreprise.fr',
        'siret': '987654321',
        'employees': ''
    }

    print("\n📊 Test 2: Contact Qualifié")
    print(f"Contact: {test_contact_qualified['contact_position']}")
    result = scorer.score_contact(test_contact_qualified)
    print(json.dumps(result, indent=2, ensure_ascii=False))

    # Test Case 3: Contact faible
    test_contact_weak = {
        'contact_name': '',
        'contact_position': '',
        'contact_email': 'contact@site.fr',
        'email_confidence': 'low',
        'contact_linkedin': '',
        'data_sources': [],
        'rating': 3.2,
        'reviews_count': 5,
        'website': '',
        'siret': '',
        'employees': ''
    }

    print("\n📊 Test 3: Contact Faible")
    result = scorer.score_contact(test_contact_weak)
    print(json.dumps(result, indent=2, ensure_ascii=False))

    # Test statistiques
    print("\n📊 Statistiques globales")
    all_contacts = [
        {**test_contact_premium, **scorer.score_contact(test_contact_premium)},
        {**test_contact_qualified, **scorer.score_contact(test_contact_qualified)},
        {**test_contact_weak, **scorer.score_contact(test_contact_weak)}
    ]

    stats = scorer.get_stats(all_contacts)
    print(json.dumps(stats, indent=2, ensure_ascii=False))

    print("\n" + "="*60)
    print("✅ Tests terminés")
    print("="*60)
