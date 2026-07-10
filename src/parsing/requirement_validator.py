"""
=============================================================================
 VALIDATION DE L'EXIGENCE DU POSTE  (anti "garbage in")
-----------------------------------------------------------------------------
 Problème résolu : si le recruteur tape du charabia ("hbuybhuburbybyub..."),
 le LLM peut quand même HALLUCINER un poste plausible -> le CV obtient un score
 élevé alors que l'entrée n'a aucun sens. C'est un trou de fiabilité grave pour
 un produit RH.

 Ce module fait un CONTRÔLE LEXICAL rapide et déterministe (sans appeler l'IA) :
 il vérifie que le texte contient de VRAIS mots (structure linguistique
 plausible), avant d'autoriser le scoring. C'est la 1re barrière de défense ;
 le flag `is_valid_job` du LLM (dans le prompt) en est la 2e.
=============================================================================
"""
from __future__ import annotations

import re

# Voyelles (FR + EN, accents inclus). 'y' est traité comme voyelle.
_VOWELS = set("aeiouyàâäéèêëïîôöùûü")


def _looks_like_word(word: str) -> bool:
    """Un mot a-t-il une STRUCTURE plausible (vs charabia clavier) ?

    Règles linguistiques simples :
      - au moins 2 caractères ;
      - contient au moins une VOYELLE (un mot sans voyelle = suspect) ;
      - pas de longue suite de CONSONNES (>= 4 d'affilée = charabia, ex: "hbrb") ;
      - pas de caractère répété 4+ fois ("aaaaa").
    """
    w = word.lower()
    if len(w) < 2:
        return False
    if not any(c in _VOWELS for c in w):
        return False
    # Détecte une suite de 4 consonnes consécutives (signe fort de charabia).
    consonant_run = 0
    for c in w:
        if c in _VOWELS:
            consonant_run = 0
        else:
            consonant_run += 1
            if consonant_run >= 4:
                return False
    # Répétition excessive du même caractère (ex: "aaaa", "zzzz").
    if re.search(r"(.)\1\1\1", w):
        return False
    return True


def validate_requirement_text(text: str) -> tuple[bool, str]:
    """
    Valide que `text` ressemble à une vraie exigence de poste.

    Retourne (is_valid, message_erreur) :
      - (True,  "")        si le texte est exploitable ;
      - (False, "raison")  sinon (message destiné à l'utilisateur).
    """
    t = (text or "").strip()

    # 1) Trop court pour décrire un poste.
    if len(t) < 10:
        return False, ("L'exigence du poste est trop courte. Décrivez le poste, "
                       "les compétences et l'expérience attendues.")

    # 2) On extrait les "mots" (suites de lettres d'au moins 2 caractères).
    words = re.findall(r"[A-Za-zÀ-ÿ]{2,}", t)
    if not words:
        return False, ("Cette description ne contient aucun mot exploitable. "
                       "Veuillez saisir une exigence de poste valide.")

    # 3) Un seul "mot" très long et collé (ex: "hbuybhuburbybyub") = charabia.
    if len(words) < 2 and len(t.replace(" ", "")) > 12:
        return False, ("Cette description ne semble pas être une offre d'emploi valide. "
                       "Précisez le poste, les compétences et l'expérience attendues.")

    # 4) Proportion de mots à structure plausible.
    plausible = [w for w in words if _looks_like_word(w)]
    ratio = len(plausible) / len(words)
    if ratio < 0.5 or len(plausible) < 2:
        return False, ("Cette description ne semble pas être une offre d'emploi valide. "
                       "Précisez le poste, les compétences et l'expérience attendues.")

    # Sinon : texte exploitable.
    return True, ""
