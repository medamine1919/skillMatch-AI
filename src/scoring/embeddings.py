"""
EMBEDDINGS — compréhension SÉMANTIQUE des textes (CV et offres).

Un "embedding" est un VECTEUR de nombres représentant le SENS d'un texte.
Deux textes proches par le sens ont des vecteurs proches. On mesure cette
proximité par la SIMILARITÉ COSINUS (1 = identique, 0 = sans rapport).

C'est ce qui permet au système de comprendre que "développeur web" et
"ingénieur front-end" sont proches, même sans mots identiques.

Modèle utilisé : sentence-transformers (all-MiniLM-L6-v2), léger et efficace.
"""
from __future__ import annotations

from functools import lru_cache

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity

from src.config import EMBEDDING_MODEL_NAME


@lru_cache(maxsize=1)
def get_embedding_model() -> SentenceTransformer:
    """Charge le modèle d'embeddings UNE SEULE FOIS (cache lru_cache).
    Le chargement est coûteux : on le garde en mémoire pour tout le programme."""
    return SentenceTransformer(EMBEDDING_MODEL_NAME)


def build_cv_semantic_text(cv_data: dict) -> str:
    """Assemble en UN seul texte les parties signifiantes du CV (résumé,
    compétences, projets, expériences) pour en calculer l'embedding global."""
    parts = [
        cv_data.get("summary", ""),
        " ".join(cv_data.get("skills_technical", [])),
        " ".join(cv_data.get("skills_soft", [])),
        " ".join(cv_data.get("projects", [])),
    ]
    for exp in cv_data.get("experience", []):
        parts.append(exp.get("job_title", ""))
        parts.append(exp.get("description", ""))
        parts.append(" ".join(exp.get("skills_used", [])))
    return " ".join(part for part in parts if part).strip()


def build_requirement_semantic_text(req_data: dict) -> str:
    """Assemble en UN seul texte les parties signifiantes de l'offre, pour
    comparer son sens à celui du CV."""
    parts = [
        req_data.get("job_title", ""),
        req_data.get("required_speciality", ""),
        " ".join(req_data.get("required_skills", [])),
        " ".join(req_data.get("preferred_skills", [])),
        " ".join(req_data.get("soft_skills", [])),
        " ".join(req_data.get("responsibilities", [])),
        " ".join(req_data.get("keywords", [])),
    ]
    return " ".join(part for part in parts if part).strip()


def compute_semantic_similarity(cv_text: str, req_text: str) -> float:
    """Renvoie la similarité de SENS entre deux textes, entre 0 et 1.
    1 = sens très proche, 0 = aucun rapport."""
    # Si un des textes est vide, aucune comparaison possible -> 0.
    if not cv_text.strip() or not req_text.strip():
        return 0.0

    model = get_embedding_model()
    # On transforme les 2 textes en vecteurs (embeddings)...
    embeddings = model.encode([cv_text, req_text])
    # ...puis on mesure l'angle entre eux (similarité cosinus).
    score = float(cosine_similarity([embeddings[0]], [embeddings[1]])[0][0])
    return max(0.0, min(1.0, score))   # borné [0,1] par sécurité
