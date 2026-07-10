"""
Évaluation de la capacité PÉDAGOGIQUE / d'ENCADREMENT d'un candidat.

POURQUOI ce critère ? DecliTech est une startup e-learning : beaucoup de postes
(coachs, formateurs, animateurs) exigent de savoir enseigner, accompagner ou
encadrer. Ce module mesure à quel point le CV montre de tels signaux.

DEUX SOURCES de signaux :
  1) Signaux STRUCTURÉS extraits par le LLM (teaching_signals, mentoring_signals,
     youth_education_signals) — les plus fiables.
  2) REPLI par mots-clés : si le LLM n'a rien rempli, on cherche nous-mêmes des
     mots-clés de pédagogie dans le texte du CV.
"""
from __future__ import annotations

# Mots-clés de pédagogie/encadrement servant de repli si le LLM n'a pas
# rempli les signaux structurés. Couvre FR + EN et les variantes sans accent.
_PEDAGOGY_KEYWORDS = [
    "pédagogie", "pedagogie", "pedagogy", "enseignement", "enseignant",
    "formation", "formateur", "formatrice", "coach", "coaching", "tutorat",
    "tuteur", "mentorat", "mentoring", "encadrement", "animation", "animateur",
    "atelier", "workshop", "teaching", "tutoring", "éducation", "education",
    "cours", "élèves", "eleves", "étudiants", "etudiants", "enfants", "kids",
]


def _keyword_signals_from_cv(cv_data: dict) -> list[str]:
    """Repli : détecte des signaux pédagogiques via mots-clés dans le CV."""
    # On agrège les zones de texte où la pédagogie peut apparaître.
    parts = [
        cv_data.get("summary", ""),
        " ".join(cv_data.get("skills_soft", [])),
        " ".join(cv_data.get("projects", [])),
    ]
    for exp in cv_data.get("experience", []):
        parts.append(exp.get("job_title", ""))
        parts.append(exp.get("description", ""))
    lowered = " ".join(p for p in parts if p).lower()
    # On renvoie la liste des mots-clés effectivement trouvés.
    return [kw for kw in _PEDAGOGY_KEYWORDS if kw in lowered]


def compute_pedagogy_match(cv_data: dict, req_data: dict) -> dict:
    # 1) On rassemble d'abord les signaux STRUCTURÉS fournis par le LLM.
    signals = (
        cv_data.get("teaching_signals", [])
        + cv_data.get("mentoring_signals", [])
        + cv_data.get("youth_education_signals", [])
    )

    # 2) Repli : si aucun signal structuré, on déduit des mots-clés du CV.
    if not signals:
        signals = _keyword_signals_from_cv(cv_data)

    raw_count = len(signals)                                    # nb de signaux trouvés
    has_teaching_requirement = bool(req_data.get("teaching_required", False))
    mentoring_preferred = bool(req_data.get("mentoring_preferred", False))
    audience_type = (req_data.get("audience_type", "") or "").lower()

    # Ratio de base : 4 signaux suffisent pour atteindre le maximum (saturation).
    base_ratio = min(raw_count / 4.0, 1.0)

    # Ajustements selon les attentes de l'offre :
    # - Si l'offre EXIGE l'enseignement mais le CV n'a AUCUN signal -> on écrase.
    if has_teaching_requirement and raw_count == 0:
        base_ratio = 0.15
    # - Si le mentorat est un plus et le candidat en a -> petit bonus.
    if mentoring_preferred and raw_count >= 1:
        base_ratio = min(base_ratio + 0.15, 1.0)
    # - Si le public visé est jeune (enfants/ados) et le candidat a une
    #   expérience auprès des jeunes -> bonus de pertinence.
    if "child" in audience_type or "teen" in audience_type or "young" in audience_type or "children" in audience_type:
        if cv_data.get("youth_education_signals"):
            base_ratio = min(base_ratio + 0.2, 1.0)

    return {
        "ratio": max(0.0, min(1.0, base_ratio)),   # borné [0,1]
        "signals_found": signals,
    }
