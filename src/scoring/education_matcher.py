"""
Évaluation de la FORMATION (éducation) d'un candidat.

PRINCIPE DU SCORE ÉDUCATION (0 à 100), moyenne pondérée de 3 axes :

  1) Niveau de diplôme (50%) — le plus haut diplôme détecté :
        Doctorat / PhD .................. 100
        Master / Ingénieur / Mastère ....  85
        Licence / Bachelor ..............  70
        BTS / DUT / Technicien ..........  55
        Baccalauréat ....................  40
        Aucun diplôme identifié .........  20

  2) Pertinence du domaine d'études (30%) — le domaine du diplôme
     correspond-il au secteur / poste visé ? (informatique, gestion,
     éducation, etc.)

  3) Exigences explicites de l'offre (20%) — si l'offre précise des
     diplômes requis, taux de correspondance ; sinon axe neutre (plein).
"""
from __future__ import annotations

# Niveaux de diplôme -> (score/100, libellé). Ordre = du plus élevé au plus bas.
_DEGREE_LEVELS = [
    (["doctorat", "doctorate", "phd", "ph.d", "thèse", "these"], 100, "Doctorat"),
    (["master", "mastère", "mastere", "ingénieur", "ingenieur", "engineering degree",
      "msc", "m.sc", "magistère", "bac+5", "diplôme d'ingénieur"], 85, "Master / Ingénieur"),
    (["licence", "bachelor", "bsc", "b.sc", "bac+3", "license"], 70, "Licence"),
    (["bts", "dut", "technicien supérieur", "deug", "bac+2", "associate"], 55, "BTS / DUT"),
    (["baccalauréat", "baccalaureat", "bac ", "high school", "secondaire"], 40, "Baccalauréat"),
]

# Domaines d'études fréquents -> mots-clés (pour la pertinence)
_FIELD_HINTS = [
    "informatique", "computer", "software", "génie logiciel", "data", "réseaux",
    "télécommunications", "électronique", "mécanique", "gestion", "management",
    "finance", "comptabilité", "marketing", "ressources humaines", "économie",
    "éducation", "pédagogie", "psychologie", "design", "robotique", "intelligence artificielle",
    "business intelligence", "erp", "mathématiques", "statistiques", "commerce",
]


def _detect_degree_level(education_text: str) -> tuple[int, str]:
    """Détecte le plus HAUT diplôme du candidat via mots-clés.
    _DEGREE_LEVELS est trié du plus élevé au plus bas : on renvoie le premier
    niveau dont un mot-clé apparaît (donc le diplôme le plus élevé trouvé)."""
    text = education_text.lower()
    for keywords, score, label in _DEGREE_LEVELS:
        if any(kw in text for kw in keywords):
            return score, label
    return 20, "Non identifié"     # aucun diplôme reconnu


def _field_relevance(education_text: str, req_text: str) -> float:
    """Mesure si le DOMAINE d'études colle au poste (retourne un ratio 0..1)."""
    edu = education_text.lower()
    req = req_text.lower()
    # Domaines d'études détectés dans la formation du candidat
    edu_fields = [f for f in _FIELD_HINTS if f in edu]
    if not edu_fields:
        return 0.5  # domaine inconnu -> note neutre (ni bonus ni malus)
    if not req.strip():
        return 0.8  # pas d'exigence -> on valorise la présence d'un domaine clair
    # Le domaine de la formation apparaît-il aussi dans l'offre ? -> alignement
    overlap = [f for f in edu_fields if f in req]
    return 1.0 if overlap else 0.45   # 1.0 si aligné, 0.45 si domaine différent


def compute_education_score(cv_data: dict, req_data: dict) -> dict:
    education_items = cv_data.get("education", []) or []
    education_text = " ".join(
        f"{item.get('degree', '')} {item.get('field', '')} {item.get('institution', '')}"
        for item in education_items
    ).strip()

    # --- Axe 1 : niveau de diplôme ---
    level_score, level_label = _detect_degree_level(education_text)

    # --- Axe 2 : pertinence du domaine ---
    req_text = " ".join([
        req_data.get("job_title", ""),
        req_data.get("required_speciality", ""),
        req_data.get("target_sector", ""),
        " ".join(req_data.get("keywords", []) or []),
        " ".join(req_data.get("responsibilities", []) or []),
    ])
    field_ratio = _field_relevance(education_text, req_text)

    # --- Axe 3 : exigences explicites de l'offre ---
    requirements = [r.lower() for r in (req_data.get("education_requirements", []) or [])]
    if requirements:
        matched = [r for r in requirements if r in education_text.lower()]
        missing = [r for r in requirements if r not in education_text.lower()]
        req_ratio = len(matched) / len(requirements)
    else:
        matched, missing = [], []
        req_ratio = 1.0  # neutre si rien d'exigé

    # --- Score global pondéré (0..100) ---
    final = (0.50 * level_score) + (0.30 * field_ratio * 100) + (0.20 * req_ratio * 100)
    final = round(max(0.0, min(100.0, final)), 1)

    # Explication lisible
    explanation = (
        f"Niveau de diplôme détecté : {level_label} ({level_score}/100). "
        f"Pertinence du domaine d'études : {int(field_ratio * 100)}%. "
    )
    if requirements:
        explanation += (
            f"Exigences de l'offre satisfaites : {len(matched)}/{len(requirements)}."
        )
    else:
        explanation += "Aucune exigence de diplôme précisée dans l'offre."

    return {
        "score": final,          # 0..100
        "ratio": round(final / 100.0, 4),
        "level_label": level_label,
        "level_score": level_score,
        "field_ratio": round(field_ratio, 3),
        "requirements_matched": matched,
        "requirements_missing": missing,
        "explanation": explanation,
    }


# Rétrocompatibilité (ancienne API)
def compute_education_alignment(cv_data: dict, req_data: dict) -> dict:
    res = compute_education_score(cv_data, req_data)
    return {
        "ratio": res["ratio"],
        "matched": res["requirements_matched"],
        "missing": res["requirements_missing"],
    }
