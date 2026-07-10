"""
Business Ontology — DecliTech (startup e-learning, Tunisie).

Définit les familles de postes (départements) que les recruteurs peuvent
chercher, avec pour chacune :
  - label        : nom lisible (FR)
  - keywords     : mots-clés métier servant à (a) détecter le poste depuis
                   l'offre en texte libre et (b) affiner le score de spécialité
  - weights      : pondération ADAPTÉE des 6 critères de scoring (somme = 100)

Les 6 critères (clés) sont identiques au moteur de scoring :
  speciality_match, technical_skills, relevant_experience,
  pedagogy_tutoring, soft_skills, semantic_similarity

Principe : un coach pédagogique est jugé surtout sur la pédagogie, un
financier sur l'expérience/technique métier (pédagogie = 0), un(e)
réceptionniste sur les soft skills, etc.
"""
from __future__ import annotations

# Pondérations par défaut (profil générique, rétrocompatible avec l'ancien système)
DEFAULT_WEIGHTS = {
    "speciality_match": 25,
    "technical_skills": 25,
    "relevant_experience": 15,
    "pedagogy_tutoring": 15,
    "soft_skills": 10,
    "semantic_similarity": 10,
}

JOB_FAMILIES: dict[str, dict] = {
    # ===================== PÉDAGOGIE / COACHS E-LEARNING =====================
    "coach_robotique": {
        "label": "Coach Robotique",
        "keywords": [
            "robotique", "robotics", "arduino", "raspberry", "lego mindstorms",
            "lego", "capteurs", "microcontrôleur", "électronique", "embarqué",
            "mbot", "makeblock", "coach robotique", "animateur robotique",
        ],
        "weights": {
            "speciality_match": 20, "technical_skills": 25, "relevant_experience": 10,
            "pedagogy_tutoring": 25, "soft_skills": 10, "semantic_similarity": 10,
        },
    },
    "coach_ia_data": {
        "label": "Coach IA / Data",
        "keywords": [
            "intelligence artificielle", "ia", "ai", "machine learning",
            "deep learning", "data", "python", "data science", "nlp",
            "coach ia", "formateur ia", "data analyst",
        ],
        "weights": {
            "speciality_match": 20, "technical_skills": 30, "relevant_experience": 10,
            "pedagogy_tutoring": 20, "soft_skills": 10, "semantic_similarity": 10,
        },
    },
    "coach_dev_web": {
        "label": "Coach Développement Web",
        "keywords": [
            "développement web", "web", "html", "css", "javascript", "angular",
            "react", "node", "frontend", "backend", "fullstack", "coach web",
            "formateur web", "développeur",
        ],
        "weights": {
            "speciality_match": 20, "technical_skills": 30, "relevant_experience": 10,
            "pedagogy_tutoring": 20, "soft_skills": 10, "semantic_similarity": 10,
        },
    },
    "coach_programmation_enfants": {
        "label": "Coach Programmation (Enfants)",
        "keywords": [
            "scratch", "blockly", "code.org", "programmation enfants", "kids coding",
            "initiation", "atelier", "animateur", "enseignant", "tutorat",
            "pédagogie", "enfants", "adolescents", "ludique", "coach programmation",
        ],
        "weights": {
            "speciality_match": 15, "technical_skills": 20, "relevant_experience": 10,
            "pedagogy_tutoring": 30, "soft_skills": 15, "semantic_similarity": 10,
        },
    },
    "coach_soft_skills": {
        "label": "Coach Soft Skills",
        "keywords": [
            "soft skills", "communication", "leadership", "développement personnel",
            "confiance en soi", "coaching", "prise de parole", "travail en équipe",
            "coach soft skills", "facilitateur", "animation",
        ],
        "weights": {
            "speciality_match": 15, "technical_skills": 5, "relevant_experience": 15,
            "pedagogy_tutoring": 30, "soft_skills": 25, "semantic_similarity": 10,
        },
    },

    # ===================== TECHNIQUE / PRODUIT =====================
    "ingenieur_dev": {
        "label": "Ingénieur / Développeur",
        "keywords": [
            "ingénieur", "développeur", "software", "logiciel", "spring boot",
            "java", "python", "api", "devops", "architecture", "génie logiciel",
            "fullstack", "backend", "frontend", "base de données",
            "it", "informatique", "technologies de l'information", "tic",
            "technique", "tech",
        ],
        "weights": {
            "speciality_match": 20, "technical_skills": 40, "relevant_experience": 20,
            "pedagogy_tutoring": 0, "soft_skills": 10, "semantic_similarity": 10,
        },
    },

    # ===================== SUPPORT / GESTION =====================
    "finance": {
        "label": "Financier / Comptable",
        "keywords": [
            "finance", "financier", "comptabilité", "comptable", "audit",
            "fiscalité", "trésorerie", "budget", "contrôle de gestion",
            "erp", "sage", "facturation", "paie", "reporting financier",
        ],
        "weights": {
            "speciality_match": 20, "technical_skills": 30, "relevant_experience": 25,
            "pedagogy_tutoring": 0, "soft_skills": 15, "semantic_similarity": 10,
        },
    },
    "rh_recrutement": {
        "label": "Recruteur / RH",
        "keywords": [
            "ressources humaines", "rh", "recrutement", "recruteur", "talent",
            "sourcing", "entretien", "gestion du personnel", "paie", "sirh",
            "onboarding", "gestion des carrières",
        ],
        "weights": {
            "speciality_match": 20, "technical_skills": 20, "relevant_experience": 20,
            "pedagogy_tutoring": 5, "soft_skills": 25, "semantic_similarity": 10,
        },
    },
    "marketing": {
        "label": "Marketing / Community",
        "keywords": [
            "marketing", "community manager", "réseaux sociaux", "social media",
            "contenu", "seo", "publicité", "communication", "growth",
            "campagne", "digital marketing", "branding",
        ],
        "weights": {
            "speciality_match": 20, "technical_skills": 25, "relevant_experience": 15,
            "pedagogy_tutoring": 0, "soft_skills": 25, "semantic_similarity": 15,
        },
    },
    "admissions": {
        "label": "Conseiller Admissions",
        "keywords": [
            "admission", "admissions", "conseiller", "orientation", "inscription",
            "relation client", "accompagnement", "suivi des familles", "ventes",
            "conseiller pédagogique", "conseiller commercial",
        ],
        "weights": {
            "speciality_match": 15, "technical_skills": 10, "relevant_experience": 15,
            "pedagogy_tutoring": 10, "soft_skills": 35, "semantic_similarity": 15,
        },
    },
    "reception": {
        "label": "Réceptionniste / Accueil",
        "keywords": [
            "réception", "réceptionniste", "accueil", "standard", "secrétariat",
            "secrétaire", "front office", "accueil physique", "téléphonique",
            "agenda", "gestion administrative",
        ],
        "weights": {
            "speciality_match": 10, "technical_skills": 10, "relevant_experience": 10,
            "pedagogy_tutoring": 5, "soft_skills": 50, "semantic_similarity": 15,
        },
    },
    "management": {
        "label": "Manager / Coordinateur",
        "keywords": [
            "manager", "management", "coordinateur", "responsable", "chef de projet",
            "directeur", "supervision", "pilotage", "gestion d'équipe", "stratégie",
            "coordination pédagogique",
        ],
        "weights": {
            "speciality_match": 15, "technical_skills": 15, "relevant_experience": 30,
            "pedagogy_tutoring": 5, "soft_skills": 25, "semantic_similarity": 10,
        },
    },
    "sante_psy": {
        "label": "Psychologue / Suivi Enfants",
        "keywords": [
            "psychologue", "psychologie", "suivi", "bien-être", "santé",
            "accompagnement enfants", "orthopédagogie", "éducateur spécialisé",
            "médecin", "infirmier", "développement de l'enfant",
        ],
        "weights": {
            "speciality_match": 25, "technical_skills": 10, "relevant_experience": 20,
            "pedagogy_tutoring": 15, "soft_skills": 20, "semantic_similarity": 10,
        },
    },
}


# Domaine LARGE de chaque famille — utilisé par le "gate" de compatibilité.
# Deux familles du MÊME domaine sont compatibles (ex: Coach Dev Web & Ingénieur),
# deux familles de domaines DIFFÉRENTS sont incompatibles (ex: Dev & Finance).
FAMILY_DOMAIN = {
    "coach_robotique": "tech",
    "coach_ia_data": "tech",
    "coach_dev_web": "tech",
    "coach_programmation_enfants": "tech",
    "ingenieur_dev": "tech",
    "coach_soft_skills": "people",
    "rh_recrutement": "people",
    "admissions": "people",
    "reception": "people",
    "finance": "business",
    "marketing": "business",
    "management": "business",
    "sante_psy": "health",
}


def domain_of(family_key: str) -> str:
    """Retourne le domaine large d'une famille ('' si inconnue)."""
    return FAMILY_DOMAIN.get(family_key, "")


# ===================== DOMAINES HORS-PÉRIMÈTRE =====================
# DecliTech est une startup e-learning / IT. Un poste (ou un CV) relevant
# clairement d'un de ces métiers est HORS de son périmètre. On les détecte
# explicitement pour pouvoir signaler "Profil hors domaine" et écraser le score
# quand l'exigence et le CV ne partagent AUCUN domaine (dans les deux sens).
EXTERNAL_DOMAINS: dict[str, list[str]] = {
    "agriculture": [
        "agriculture", "agricole", "agronome", "agronomie", "élevage", "elevage",
        "maraîchage", "maraichage", "agroalimentaire", "ferme", "récolte", "recolte",
        "irrigation", "cultures", "exploitation agricole", "horticulture", "vétérinaire",
    ],
    "mecanique_auto": [
        "mécanicien", "mecanicien", "mécanique automobile", "garagiste", "carrosserie",
        "vidange", "moteur thermique", "réparation automobile", "pneumatique", "diéséliste",
    ],
    "batiment_btp": [
        "maçon", "macon", "btp", "chantier", "plomberie", "plombier", "menuiserie",
        "menuisier", "soudure", "soudeur", "peintre en bâtiment", "électricien bâtiment",
        "génie civil", "gros œuvre", "carrelage",
    ],
    "cuisine_restauration": [
        "cuisinier", "chef de cuisine", "pâtissier", "patissier", "boulanger",
        "restauration", "serveur", "barman", "commis de cuisine", "traiteur",
    ],
    "droit_juridique": [
        "avocat", "juriste", "juridique", "notaire", "huissier", "droit des affaires",
        "contentieux", "magistrat", "greffier",
    ],
    "medical_clinique": [
        "médecin", "medecin", "chirurgien", "infirmier", "pharmacien", "dentiste",
        "kinésithérapeute", "radiologue", "sage-femme", "anesthésiste",
    ],
    "transport_logistique": [
        "chauffeur", "livreur", "cariste", "routier", "conducteur poids lourd",
        "manutentionnaire",
    ],
}


def detect_external_domain(text: str) -> str:
    """
    Détecte si un texte (exigence ou CV) relève clairement d'un métier
    HORS-PÉRIMÈTRE DecliTech. Match par MOT ENTIER pour éviter les faux positifs.
    Retourne la clé du domaine externe le plus représenté, ou '' si aucun.
    """
    import re
    lowered = (text or "").lower()
    best_key, best_hits = "", 0
    for key, kws in EXTERNAL_DOMAINS.items():
        hits = 0
        for kw in kws:
            if re.search(r"(?<![\wà-ÿ])" + re.escape(kw.lower()) + r"(?![\wà-ÿ])", lowered):
                hits += 1
        if hits > best_hits:
            best_key, best_hits = key, hits
    return best_key if best_hits > 0 else ""


def get_family(key: str) -> dict | None:
    """Retourne la définition d'une famille de poste, ou None."""
    return JOB_FAMILIES.get(key)


def all_family_labels() -> dict[str, str]:
    """Mapping clé -> label lisible, utile pour le frontend."""
    return {key: fam["label"] for key, fam in JOB_FAMILIES.items()}
