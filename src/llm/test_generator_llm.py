"""
Génération d'un QCM technique via le LLM (Groq), avec repli local.

Le LLM produit des questions ADAPTÉES aux compétences du candidat / au poste.
Si l'IA échoue (indisponible, JSON invalide), on renvoie un QCM générique de
secours pour ne jamais bloquer le service.
"""
from __future__ import annotations

from src.llm.groq_client import GroqClientWrapper
from src.llm.prompts import build_test_generation_prompt
from src.utils import extract_json_from_text


def _fallback_questions(num_questions: int) -> list[dict]:
    """QCM de secours (générique informatique) si le LLM est indisponible."""
    bank = [
        {"question": "Que signifie 'API' ?", "options": ["Application Programming Interface",
            "Advanced Programming Item", "Applied Process Integration", "Automatic Program Input"],
         "correct": 0, "skill": "Général"},
        {"question": "Quel langage est principalement utilisé pour styliser une page web ?",
         "options": ["HTML", "CSS", "SQL", "JSON"], "correct": 1, "skill": "Web"},
        {"question": "Quelle structure de données fonctionne en LIFO ?",
         "options": ["File (Queue)", "Pile (Stack)", "Arbre", "Graphe"], "correct": 1, "skill": "Algorithmique"},
        {"question": "Que fait la commande SQL SELECT ?",
         "options": ["Insérer des données", "Supprimer une table", "Lire des données", "Créer un index"],
         "correct": 2, "skill": "Bases de données"},
        {"question": "Git sert principalement à ...",
         "options": ["Compiler du code", "Gérer les versions", "Déployer un serveur", "Tester une API"],
         "correct": 1, "skill": "Outils"},
        {"question": "Quel protocole sécurise les échanges web ?",
         "options": ["HTTP", "FTP", "HTTPS", "SMTP"], "correct": 2, "skill": "Réseaux"},
        {"question": "Docker permet de ...",
         "options": ["Conteneuriser des applications", "Écrire du CSS", "Gérer une base SQL", "Dessiner des maquettes"],
         "correct": 0, "skill": "DevOps"},
        {"question": "Quelle est la complexité d'une recherche binaire ?",
         "options": ["O(n)", "O(log n)", "O(n²)", "O(1)"], "correct": 1, "skill": "Algorithmique"},
        {"question": "En POO, l'héritage permet ...",
         "options": ["De cacher des données", "De réutiliser une classe parente", "De trier une liste", "De compiler"],
         "correct": 1, "skill": "Programmation"},
        {"question": "Que renvoie une requête HTTP avec le code 404 ?",
         "options": ["Succès", "Redirection", "Ressource non trouvée", "Erreur serveur"],
         "correct": 2, "skill": "Web"},
    ]
    return bank[:num_questions]


def _is_valid_question(q: dict) -> bool:
    """Vérifie qu'une question générée est bien formée (4 options + index valide)."""
    return (
        isinstance(q, dict)
        and isinstance(q.get("question"), str) and q["question"].strip()
        and isinstance(q.get("options"), list) and len(q["options"]) == 4
        and isinstance(q.get("correct"), int) and 0 <= q["correct"] <= 3
    )


def generate_test_questions(skills, speciality: str, job_title: str, num_questions: int = 10) -> list[dict]:
    """Renvoie une liste de questions QCM (avec la bonne réponse). Repli si besoin."""
    try:
        client = GroqClientWrapper()
        prompt = build_test_generation_prompt(skills, speciality, job_title, num_questions)
        raw = client.complete(prompt=prompt, temperature=0.4)
        parsed = extract_json_from_text(raw)
        # On accepte une liste directe, ou un objet {"questions": [...]}.
        if isinstance(parsed, dict):
            parsed = parsed.get("questions", [])
        valid = [q for q in parsed if _is_valid_question(q)] if isinstance(parsed, list) else []
        if len(valid) >= 3:               # assez de questions exploitables
            return valid[:num_questions]
        raise ValueError("QCM IA insuffisant")
    except Exception:
        return _fallback_questions(num_questions)
