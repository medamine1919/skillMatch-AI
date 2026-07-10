"""
Business Context Resolver.

À partir de l'exigence de poste (texte libre déjà parsé en `req_data`), détecte
la FAMILLE DE POSTE la plus probable (Coach Robotique, Financier, RH, ...) puis
renvoie l'ontologie correspondante : pondérations adaptées + mots-clés métier.

Stratégie de détection (robuste) :
  1) Comptage de mots-clés métier dans le texte de l'offre (rapide, fiable).
  2) Si aucun mot-clé ne ressort, repli sémantique via embeddings
     (similarité cosinus entre l'offre et la "signature" de chaque famille).
  3) Si toujours rien, profil GÉNÉRIQUE (pondérations par défaut) — rétrocompatible.
"""
from __future__ import annotations

import re

from src.scoring.business_ontology import (
    DEFAULT_WEIGHTS,
    JOB_FAMILIES,
)
from src.utils import safe_lower


def _build_requirement_text(req_data: dict) -> str:
    parts = [
        req_data.get("job_title", ""),
        req_data.get("required_speciality", ""),
        req_data.get("target_sector", ""),
        req_data.get("audience_type", ""),
        " ".join(req_data.get("required_skills", [])),
        " ".join(req_data.get("preferred_skills", [])),
        " ".join(req_data.get("soft_skills", [])),
        " ".join(req_data.get("responsibilities", [])),
        " ".join(req_data.get("keywords", [])),
        " ".join(req_data.get("priority_criteria", [])),
    ]
    return safe_lower(" ".join(p for p in parts if p))


def _count_keyword_hits(text: str, keywords: list[str]) -> int:
    # Match par mots entiers : évite que "ia" matche dans "mécanicien", etc.
    hits = 0
    for kw in keywords:
        kw_l = safe_lower(kw)
        if re.search(r"\b" + re.escape(kw_l) + r"\b", text):
            hits += 1
    return hits


def _semantic_fallback(req_text: str) -> tuple[str, float, dict[str, float]]:
    """Repli sémantique si aucun mot-clé ne matche."""
    try:
        from src.scoring.embeddings import compute_semantic_similarity
        scores: dict[str, float] = {}
        for key, fam in JOB_FAMILIES.items():
            signature = fam["label"] + " " + " ".join(fam["keywords"])
            scores[key] = compute_semantic_similarity(req_text, signature)
        best = max(scores, key=scores.get)
        return best, scores[best], scores
    except Exception:
        return "", 0.0, {}


def resolve_business_context(req_data: dict) -> dict:
    """
    Retourne un dict :
      {
        "family_key": str | "",          # "" => générique
        "family_label": str,
        "weights": dict,                 # pondérations à appliquer
        "keywords": list[str],
        "confidence": float,             # 0..1 indicatif
        "method": "keywords"|"semantic"|"default",
        "family_scores": dict,
      }
    """
    req_text = _build_requirement_text(req_data)

    # --- 1) Détection par mots-clés ---
    keyword_scores = {
        key: _count_keyword_hits(req_text, fam["keywords"])
        for key, fam in JOB_FAMILIES.items()
    }
    best_key = max(keyword_scores, key=keyword_scores.get) if keyword_scores else ""
    best_hits = keyword_scores.get(best_key, 0)

    if best_key and best_hits > 0:
        fam = JOB_FAMILIES[best_key]
        total_hits = sum(keyword_scores.values()) or 1
        confidence = round(min(1.0, best_hits / total_hits + 0.15), 3)

        # ===== Détection HYBRIDE =====
        # Un poste peut couvrir PLUSIEURS familles (ex: "recruteur IT" = RH + tech).
        # On retient comme familles secondaires celles ayant un nombre de hits
        # significatif (au moins la moitié du meilleur, et >= 1).
        secondary = [
            k for k, v in keyword_scores.items()
            if k != best_key and v >= max(1, best_hits * 0.5)
        ]
        # Fusion des mots-clés (le CV peut matcher sur n'importe quelle facette)
        merged_keywords = list(fam["keywords"])
        for k in secondary:
            merged_keywords += [kw for kw in JOB_FAMILIES[k]["keywords"]
                                if kw not in merged_keywords]
        # Fusion des pondérations : moyenne pondérée par les hits, renormalisée à 100.
        if secondary:
            contributors = [(best_key, best_hits)] + [(k, keyword_scores[k]) for k in secondary]
            total_w = sum(h for _, h in contributors)
            blended = {}
            for crit in fam["weights"]:
                blended[crit] = sum(JOB_FAMILIES[k]["weights"][crit] * h for k, h in contributors) / total_w
            norm = 100.0 / (sum(blended.values()) or 1)
            weights = {c: round(v * norm, 2) for c, v in blended.items()}
            label = fam["label"] + " + " + " + ".join(JOB_FAMILIES[k]["label"] for k in secondary)
        else:
            weights = fam["weights"]
            label = fam["label"]

        return {
            "family_key": best_key,
            "family_label": label,
            "secondary_families": secondary,
            "weights": weights,
            "keywords": merged_keywords,
            "confidence": confidence,
            "method": "keywords",
            "family_scores": keyword_scores,
        }

    # --- 2) Repli sémantique (seuil strict pour éviter de forcer un métier
    #         hors-domaine, ex: "mécanicien voiture", dans une famille DecliTech) ---
    if req_text.strip():
        sem_key, sem_score, sem_scores = _semantic_fallback(req_text)
        if sem_key and sem_score >= 0.55:
            fam = JOB_FAMILIES[sem_key]
            return {
                "family_key": sem_key,
                "family_label": fam["label"],
                "secondary_families": [],
                "weights": fam["weights"],
                "keywords": fam["keywords"],
                "confidence": round(sem_score, 3),
                "method": "semantic",
                "family_scores": {k: round(v, 3) for k, v in sem_scores.items()},
            }

    # --- 3) Profil générique (rétrocompatible) ---
    return {
        "family_key": "",
        "family_label": "Générique",
        "secondary_families": [],
        "weights": DEFAULT_WEIGHTS,
        "keywords": [],
        "confidence": 0.0,
        "method": "default",
        "family_scores": keyword_scores,
    }


def detect_family_from_text(text: str) -> tuple[str, int]:
    """
    Détecte la famille de poste la plus représentée dans un texte libre
    (utilisé pour deviner le DOMAINE du CV). Retourne (clé_famille, nb_hits).
    Renvoie ("", 0) si aucun mot-clé ne ressort.
    """
    lowered = safe_lower(text)
    scores = {
        key: _count_keyword_hits(lowered, fam["keywords"])
        for key, fam in JOB_FAMILIES.items()
    }
    best = max(scores, key=scores.get) if scores else ""
    return (best, scores.get(best, 0)) if scores.get(best, 0) > 0 else ("", 0)


def detect_domains_from_text(text: str) -> set[str]:
    """
    Détecte TOUS les domaines larges présents dans un texte (CV).
    Un CV peut être hybride (ex: ingénieur ayant développé une plateforme RH).
    Un domaine est retenu si une de ses familles a >= 2 hits (ou 1 pour la meilleure).
    """
    from src.scoring.business_ontology import domain_of as _dom
    lowered = safe_lower(text)
    scores = {
        key: _count_keyword_hits(lowered, fam["keywords"])
        for key, fam in JOB_FAMILIES.items()
    }
    domains: set[str] = set()
    best = max(scores, key=scores.get) if scores else ""
    if best and scores[best] > 0:
        domains.add(_dom(best))
    for k, v in scores.items():
        if v >= 2:
            domains.add(_dom(k))
    domains.discard("")
    return domains


def family_keyword_ratio(text: str, keywords: list[str]) -> float:
    """
    Ratio 0..1 de présence des mots-clés d'une famille dans un texte (ex: le CV).
    Sert à calculer l'adéquation de spécialité APRÈS résolution du poste.
    """
    if not keywords:
        return 0.0
    lowered = safe_lower(text)
    hits = sum(1 for kw in keywords if safe_lower(kw) in lowered)
    # Saturation : 4 mots-clés présents suffisent pour un ratio plein.
    return min(1.0, hits / 4.0)
