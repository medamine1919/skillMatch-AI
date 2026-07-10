"""
Talent Search (RAG) — recherche sémantique sur le vivier de candidats.

Le recruteur tape une requête en langage naturel
(ex: "coach qui connaît Arduino et bon avec les enfants").
On classe TOUS les candidats déjà analysés par pertinence, via une approche
HYBRIDE :
  - Sémantique : similarité cosinus entre l'embedding de la requête et celui
    du profil de chaque candidat (sentence-transformers all-MiniLM-L6-v2).
  - Lexicale   : recouvrement de mots-clés (capte les termes précis comme
    "Arduino", "Scratch", un nom de techno, etc.).
Score final = 0.6 * sémantique + 0.4 * lexical.
(Le poids lexical a été porté à 0.4 pour mieux respecter les critères précis
 tapés par le recruteur — compétences, niveaux de langue, technos.)
"""
from __future__ import annotations

import re

from src.scoring.embeddings import get_embedding_model
# Le dictionnaire de synonymes est désormais CENTRALISÉ dans synonyms.py
# (partagé entre le RAG et le matching exigence ↔ CV).
from src.scoring.synonyms import SYNONYMS as _SYNONYMS, term_in_text as _term_in_text

# Mots vides à ignorer dans le matching lexical de la requête.
_STOPWORDS = {
    "un", "une", "des", "de", "du", "le", "la", "les", "qui", "que", "et",
    "ou", "avec", "pour", "dans", "en", "est", "bon", "bonne", "trouve",
    "moi", "cherche", "je", "veux", "ayant", "sur", "au", "aux", "a", "à",
    "connait", "connaît", "maitrise", "maîtrise", "experience", "expérience",
    "profil", "candidat", "candidats", "the", "and", "with", "who", "good",
}




def _tokenize(text: str) -> list[str]:
    tokens = re.findall(r"[a-zA-ZÀ-ÿ0-9\+#\.]+", (text or "").lower())
    # On garde les tokens de 2+ caractères pour capter les niveaux de langue
    # (b2, c1, a2...) tout en filtrant les mots vides.
    return [t for t in tokens if len(t) >= 2 and t not in _STOPWORDS]


def _term_in_text(term: str, text: str) -> bool:
    """Vrai si `term` apparaît comme MOT ENTIER (pas en sous-chaîne)."""
    return re.search(r"(?<![\wÀ-ÿ])" + re.escape(term) + r"(?![\wÀ-ÿ])", text) is not None


def _lexical_overlap(query_tokens: list[str], profile_text: str) -> float:
    """
    Recouvrement lexical INTELLIGENT :
      - match par mots entiers (évite "ia" dans "stagiaire")
      - expansion par synonymes (IA → intelligence artificielle, machine learning...)
    """
    if not query_tokens:
        return 0.0
    profile_l = (profile_text or "").lower()
    hits = 0
    for tok in query_tokens:
        variants = _SYNONYMS.get(tok, [tok])
        if any(_term_in_text(v, profile_l) for v in variants):
            hits += 1
    return hits / len(query_tokens)


def search_candidates(
    query: str,
    candidates: list[dict],
    top_k: int = 50,
    min_score: float = 0.0,
) -> list[dict]:
    """
    query       : requête en langage naturel.
    candidates  : [{ "id": str, "text": str }, ...] (texte = profil du candidat).
    Retourne    : [{ "id", "score", "semantic", "lexical" }, ...] trié décroissant.
    """
    query = (query or "").strip()
    if not query or not candidates:
        return []

    query_tokens = _tokenize(query)

    # --- Embeddings (batch unique : requête + tous les profils) ---
    model = get_embedding_model()
    texts = [query] + [c.get("text", "") or " " for c in candidates]
    embeddings = model.encode(texts, normalize_embeddings=True)
    query_vec = embeddings[0]
    profile_vecs = embeddings[1:]

    results = []
    for cand, vec in zip(candidates, profile_vecs):
        # cosinus = produit scalaire (vecteurs normalisés)
        semantic = float(sum(q * p for q, p in zip(query_vec, vec)))
        semantic = max(0.0, min(1.0, semantic))
        lexical = _lexical_overlap(query_tokens, cand.get("text", ""))
        # 0.6 sémantique + 0.4 lexical : équilibre entre compréhension du sens
        # et critères concrets (compétences, niveaux de langue, technos précises).
        final = round((0.6 * semantic) + (0.4 * lexical), 4)
        results.append({
            "id": str(cand.get("id", "")),
            "score": final,
            "semantic": round(semantic, 4),
            "lexical": round(lexical, 4),
        })

    results.sort(key=lambda r: r["score"], reverse=True)
    filtered = [r for r in results if r["score"] >= min_score]
    return filtered[:top_k]
