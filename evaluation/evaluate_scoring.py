"""
=============================================================================
 ÉVALUATION SCIENTIFIQUE DU MOTEUR DE SCORING — SkillMatch AI
-----------------------------------------------------------------------------
 Objectif : PROUVER, chiffres à l'appui, que le scoring adaptatif fonctionne.

 Méthode : on constitue un JEU DE TEST ANNOTÉ (« vérité terrain ») de paires
 (CV, offre) au format cv_data / req_data — ce qui ISOLE le modèle de scoring
 et rend l'évaluation 100 % REPRODUCTIBLE (aucun appel LLM, aucun fichier).

 Chaque cas porte deux étiquettes humaines :
   - relevant      : le candidat est-il PERTINENT pour l'offre ? (présélection)
   - out_of_domain : le CV relève-t-il d'un AUTRE domaine que l'offre ?

 On exécute compute_scoring() sur chaque paire, puis on compare la prédiction
 du modèle à la vérité terrain, sur DEUX axes :
   1) PRÉSÉLECTION  : le candidat est-il retenu (score >= seuil) ?
   2) HORS-DOMAINE  : le drapeau out_of_scope du modèle est-il correct ?

 Sorties : métriques (Précision / Rappel / F1 / Exactitude) + matrices de
 confusion, affichées à l'écran ET écrites dans evaluation/ (Markdown + CSV).

 Lancement :  python evaluation/evaluate_scoring.py
=============================================================================
"""
from __future__ import annotations

import csv
import os
import sys

# --- Rendre le package `src` importable quand on lance ce script directement ---
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from src.scoring.scoring_engine import compute_scoring          # noqa: E402
from src.config import SHORTLIST_THRESHOLDS                     # noqa: E402

# Seuil de PRÉSÉLECTION : un candidat est « retenu » si son score l'atteint.
SHORTLIST_MIN = SHORTLIST_THRESHOLDS["moderate"]                # 55/100 par défaut


# =============================================================================
#  Constructeurs compacts de profils (au format attendu par le moteur)
# =============================================================================
def cv(summary, tech=(), soft=(), years=0.0, projects=(), teaching=(),
       exp_title="", exp_desc="", exp_skills=()):
    experience = []
    if exp_title or exp_desc:
        experience = [{
            "job_title": exp_title, "company": "", "start_date": "", "end_date": "",
            "duration_months": int(years * 12), "description": exp_desc,
            "skills_used": list(exp_skills),
        }]
    return {
        "full_name": "Candidat Test", "email": "", "phone": "", "location": "",
        "summary": summary,
        "skills_technical": list(tech), "skills_soft": list(soft),
        "languages": [], "certifications": [], "education": [],
        "experience": experience, "projects": list(projects),
        "teaching_signals": list(teaching), "mentoring_signals": [],
        "youth_education_signals": [], "estimated_years_experience": years,
    }


def req(job_title, speciality="", required=(), preferred=(), soft=(), years=0.0,
        teaching=False, audience="", responsibilities=(), keywords=(),
        sector="IT / e-learning"):
    return {
        "input_mode": "", "job_title": job_title, "contract_type": "", "location": "",
        "target_sector": sector, "required_speciality": speciality,
        "required_skills": list(required), "preferred_skills": list(preferred),
        "soft_skills": list(soft), "languages_required": [],
        "experience_required_years": years, "education_requirements": [],
        "teaching_required": teaching, "mentoring_preferred": False,
        "audience_type": audience, "responsibilities": list(responsibilities),
        "keywords": list(keywords), "priority_criteria": [],
    }


# =============================================================================
#  JEU DE TEST ANNOTÉ (vérité terrain)
#  relevant=True  -> le candidat DOIT être retenu (bon match)
#  out_of_domain=True -> le CV est d'un AUTRE métier -> DOIT être écrasé
# =============================================================================
DATASET = [
    # ---------- MATCHS PERTINENTS (même domaine, bon recouvrement) ----------
    {
        "id": "P1-dev_web",
        "cv": cv("Développeur web fullstack passionné",
                 tech=["HTML", "CSS", "JavaScript", "Angular", "Node.js"],
                 projects=["Plateforme e-commerce en Angular"], years=3,
                 exp_title="Développeur web", exp_desc="Développement front-end Angular",
                 exp_skills=["Angular", "JavaScript"]),
        "req": req("Coach Développement Web", speciality="Développement Web",
                   required=["JavaScript", "Angular", "HTML", "CSS"],
                   teaching=True, audience="adolescents"),
        "relevant": True, "out_of_domain": False,
    },
    {
        "id": "P2-ia_data",
        "cv": cv("Data scientist, machine learning et NLP",
                 tech=["Python", "Machine Learning", "NLP", "Pandas", "Scikit-learn"],
                 years=2, exp_title="Data scientist",
                 exp_desc="Modèles de machine learning", exp_skills=["Python", "Machine Learning"]),
        "req": req("Coach IA / Data", speciality="Intelligence Artificielle",
                   required=["Python", "Machine Learning", "Data"], teaching=True),
        "relevant": True, "out_of_domain": False,
    },
    {
        "id": "P3-robotique",
        "cv": cv("Passionné de robotique éducative",
                 tech=["Arduino", "Raspberry", "capteurs", "électronique", "robotique"],
                 years=1, exp_title="Animateur robotique",
                 exp_desc="Ateliers Arduino pour enfants", exp_skills=["Arduino", "robotique"]),
        "req": req("Coach Robotique", speciality="Robotique",
                   required=["Arduino", "robotique", "capteurs"], teaching=True),
        "relevant": True, "out_of_domain": False,
    },
    {
        "id": "P4-rh",
        "cv": cv("Chargé de recrutement en ressources humaines",
                 tech=["sourcing", "entretien", "SIRH", "recrutement"],
                 soft=["communication"], years=3, exp_title="Chargé de recrutement",
                 exp_desc="Sourcing et entretiens", exp_skills=["recrutement", "sourcing"]),
        "req": req("Recruteur RH", required=["recrutement", "sourcing", "entretien"],
                   soft=["communication"]),
        "relevant": True, "out_of_domain": False,
    },
    {
        "id": "P5-finance",
        "cv": cv("Comptable, audit et contrôle de gestion",
                 tech=["comptabilité", "audit", "ERP", "Sage", "fiscalité"],
                 years=4, exp_title="Comptable", exp_desc="Comptabilité et audit",
                 exp_skills=["comptabilité", "audit"]),
        "req": req("Financier / Comptable", required=["comptabilité", "audit", "ERP"]),
        "relevant": True, "out_of_domain": False,
    },
    {
        "id": "P6-marketing",
        "cv": cv("Community manager, réseaux sociaux et SEO",
                 tech=["SEO", "social media", "contenu", "communication"],
                 years=2, exp_title="Community manager",
                 exp_desc="Gestion des réseaux sociaux", exp_skills=["SEO", "social media"]),
        "req": req("Community Manager", required=["SEO", "réseaux sociaux", "contenu"]),
        "relevant": True, "out_of_domain": False,
    },
    {
        "id": "P7-reception",
        "cv": cv("Réceptionniste : accueil physique et téléphonique, secrétariat",
                 soft=["communication", "organisation", "accueil"], years=2,
                 exp_title="Réceptionniste", exp_desc="Accueil et standard téléphonique",
                 exp_skills=["accueil", "secrétariat"]),
        "req": req("Réceptionniste / Accueil", soft=["accueil", "communication"],
                   keywords=["réception", "accueil", "standard"]),
        "relevant": True, "out_of_domain": False,
    },
    {
        "id": "P8-ingenieur",
        "cv": cv("Ingénieur logiciel Java / Spring Boot",
                 tech=["Java", "Spring Boot", "API", "PostgreSQL", "DevOps"],
                 years=3, exp_title="Ingénieur logiciel",
                 exp_desc="Back-end Spring Boot", exp_skills=["Java", "Spring Boot"]),
        "req": req("Ingénieur / Développeur", speciality="Génie logiciel",
                   required=["Java", "Spring Boot", "API"], years=2),
        "relevant": True, "out_of_domain": False,
    },

    # ---------- HORS-DOMAINE (métier différent -> doit être écrasé) ----------
    {
        "id": "O1-devweb_vs_finance",
        "cv": cv("Développeur web fullstack",
                 tech=["HTML", "CSS", "JavaScript", "Angular", "Node.js"], years=3),
        "req": req("Financier / Comptable", required=["comptabilité", "audit", "ERP"]),
        "relevant": False, "out_of_domain": True,
    },
    {
        "id": "O2-finance_vs_devweb",
        "cv": cv("Comptable, audit et fiscalité",
                 tech=["comptabilité", "audit", "Sage", "fiscalité"], years=4),
        "req": req("Coach Développement Web", speciality="Développement Web",
                   required=["JavaScript", "Angular", "HTML"], teaching=True),
        "relevant": False, "out_of_domain": True,
    },
    {
        "id": "O3-avocat_vs_ingenieur",
        "cv": cv("Avocat spécialisé en droit des affaires et contentieux",
                 tech=["droit", "juridique", "contentieux"], years=5,
                 exp_title="Avocat", exp_desc="Droit des affaires et contentieux"),
        "req": req("Ingénieur / Développeur", speciality="Génie logiciel",
                   required=["Java", "Spring Boot", "API"]),
        "relevant": False, "out_of_domain": True,
    },
    {
        "id": "O4-mecanicien_vs_ia",
        "cv": cv("Mécanicien automobile, réparation moteur et carrosserie",
                 tech=["mécanique automobile", "réparation", "moteur thermique"], years=6,
                 exp_title="Mécanicien", exp_desc="Réparation automobile en garage"),
        "req": req("Coach IA / Data", speciality="Intelligence Artificielle",
                   required=["Python", "Machine Learning", "Data"], teaching=True),
        "relevant": False, "out_of_domain": True,
    },
    {
        "id": "O5-agriculteur_vs_marketing",
        "cv": cv("Agronome, gestion d'exploitation agricole et élevage",
                 tech=["agriculture", "agronomie", "élevage"], years=4,
                 exp_title="Agronome", exp_desc="Exploitation agricole et cultures"),
        "req": req("Community Manager", required=["SEO", "réseaux sociaux", "contenu"]),
        "relevant": False, "out_of_domain": True,
    },
    {
        "id": "O6-medecin_vs_devweb",
        "cv": cv("Médecin généraliste, suivi clinique des patients",
                 tech=["médecine", "clinique", "diagnostic"], years=8,
                 exp_title="Médecin", exp_desc="Consultations et suivi clinique"),
        "req": req("Coach Développement Web", speciality="Développement Web",
                   required=["JavaScript", "Angular", "HTML"], teaching=True),
        "relevant": False, "out_of_domain": True,
    },

    # ---------- CAS LIMITES (même GRAND domaine -> pertinent mais nuancé) ----------
    {
        "id": "B1-ia_vs_devweb",   # tech vs tech, sous-spécialité différente
        "cv": cv("Data scientist, machine learning et Python",
                 tech=["Python", "Machine Learning", "NLP", "Pandas"], years=2),
        "req": req("Coach Développement Web", speciality="Développement Web",
                   required=["JavaScript", "Angular", "HTML"], teaching=True),
        "relevant": True, "out_of_domain": False,
    },
    {
        "id": "B2-junior_vs_senior",   # bon domaine, gros écart d'expérience
        "cv": cv("Développeur junior Java débutant",
                 tech=["Java", "Spring Boot"], years=0.5),
        "req": req("Ingénieur / Développeur senior", speciality="Génie logiciel",
                   required=["Java", "Spring Boot", "API"], years=5),
        "relevant": True, "out_of_domain": False,
    },
    {
        "id": "B3-hybride_recruteur_it",   # poste hybride RH + tech
        "cv": cv("Ingénieur ayant développé une plateforme RH interne",
                 tech=["Java", "Angular", "recrutement", "RH", "SIRH"], years=3),
        "req": req("Recruteur IT", required=["recrutement", "IT"],
                   keywords=["it", "rh", "recrutement", "informatique"]),
        "relevant": True, "out_of_domain": False,
    },
]


# =============================================================================
#  Métriques
# =============================================================================
def prf(tp, fp, fn):
    """Précision, Rappel, F1 à partir des comptes de confusion."""
    precision = tp / (tp + fp) if (tp + fp) else 0.0
    recall = tp / (tp + fn) if (tp + fn) else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) else 0.0
    return precision, recall, f1


def confusion(pairs):
    """pairs = liste de (y_true, y_pred) booléens. Positif = True."""
    tp = sum(1 for yt, yp in pairs if yt and yp)
    fp = sum(1 for yt, yp in pairs if (not yt) and yp)
    fn = sum(1 for yt, yp in pairs if yt and (not yp))
    tn = sum(1 for yt, yp in pairs if (not yt) and (not yp))
    return tp, fp, fn, tn


def summarize(name, pairs):
    tp, fp, fn, tn = confusion(pairs)
    precision, recall, f1 = prf(tp, fp, fn)
    total = tp + fp + fn + tn
    accuracy = (tp + tn) / total if total else 0.0
    return {
        "name": name, "tp": tp, "fp": fp, "fn": fn, "tn": tn,
        "precision": precision, "recall": recall, "f1": f1, "accuracy": accuracy,
    }


# =============================================================================
#  Exécution
# =============================================================================
def evaluate():
    """Exécute le moteur sur tout le jeu de test et renvoie un dict
    JSON-sérialisable (SANS effet de bord : ni print ni écriture de fichier).
    Utilisé par l'API pour afficher l'évaluation dans l'espace admin."""
    rows = []
    relevance_pairs = []   # (y_true relevant, y_pred retenu)
    domain_pairs = []      # (y_true hors-domaine, y_pred out_of_scope)
    scores_relevant, scores_not = [], []

    for case in DATASET:
        res = compute_scoring(case["cv"], case["req"])
        score = res["final_score"]
        pred_shortlist = score >= SHORTLIST_MIN
        pred_ood = bool(res["out_of_scope"])

        relevance_pairs.append((case["relevant"], pred_shortlist))
        domain_pairs.append((case["out_of_domain"], pred_ood))
        (scores_relevant if case["relevant"] else scores_not).append(score)

        rows.append({
            "id": case["id"],
            "attendu_pertinent": case["relevant"],
            "attendu_hors_domaine": case["out_of_domain"],
            "score": round(score, 1),
            "decision": res["decision_label"],
            "predit_retenu": pred_shortlist,
            "predit_hors_domaine": pred_ood,
            "famille_detectee": res["business_context"]["family_label"],
            "domain_fit": res["domain_fit"],
            "ok_pertinence": case["relevant"] == pred_shortlist,
            "ok_hors_domaine": case["out_of_domain"] == pred_ood,
        })

    relevance = summarize("Présélection (pertinent vs non)", relevance_pairs)
    domain = summarize("Détection hors-domaine", domain_pairs)

    mean = lambda xs: round(sum(xs) / len(xs), 1) if xs else 0.0
    stats = {
        "n": len(DATASET),
        "seuil": SHORTLIST_MIN,
        "score_moyen_pertinents": mean(scores_relevant),
        "score_moyen_non_pertinents": mean(scores_not),
    }
    return {"rows": rows, "relevance": relevance, "domain": domain, "stats": stats}


def run():
    """Version ligne de commande : calcule, affiche et écrit les rapports."""
    print("Exécution du moteur sur", len(DATASET), "cas annotés...\n")
    data = evaluate()
    rows, relevance, domain, stats = data["rows"], data["relevance"], data["domain"], data["stats"]
    _print_report(rows, relevance, domain, stats)
    _write_csv(rows)
    _write_markdown(rows, relevance, domain, stats)
    return data


def _fmt_pct(x):
    return f"{100 * x:.1f}%"


def _print_report(rows, relevance, domain, stats):
    print("=" * 70)
    print(" RÉSULTATS PAR CAS")
    print("=" * 70)
    print(f"{'ID':<26}{'Score':>6} {'Retenu':>7} {'HorsDom':>8}  OK")
    for r in rows:
        ok = "OK" if (r["ok_pertinence"] and r["ok_hors_domaine"]) else "X"
        print(f"{r['id']:<26}{r['score']:>6} {str(r['predit_retenu']):>7} "
              f"{str(r['predit_hors_domaine']):>8}  {ok}")

    for m in (relevance, domain):
        print("\n" + "=" * 70)
        print(f" MÉTRIQUES — {m['name']}")
        print("=" * 70)
        print(f"  Matrice de confusion : VP={m['tp']}  FP={m['fp']}  "
              f"FN={m['fn']}  VN={m['tn']}")
        print(f"  Exactitude (accuracy) : {_fmt_pct(m['accuracy'])}")
        print(f"  Précision             : {_fmt_pct(m['precision'])}")
        print(f"  Rappel (recall)       : {_fmt_pct(m['recall'])}")
        print(f"  F1-score              : {_fmt_pct(m['f1'])}")

    print("\n" + "=" * 70)
    print(" SÉPARATION DES SCORES")
    print("=" * 70)
    print(f"  Score moyen des profils PERTINENTS      : {stats['score_moyen_pertinents']}/100")
    print(f"  Score moyen des profils NON pertinents  : {stats['score_moyen_non_pertinents']}/100")
    print(f"  (seuil de présélection : {stats['seuil']}/100)\n")


def _write_csv(rows):
    path = os.path.join(_ROOT, "evaluation", "results.csv")
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()), delimiter=";")
        writer.writeheader()
        writer.writerows(rows)
    print("CSV écrit  ->", path)


def _md_metrics_block(m):
    return (
        f"**{m['name']}**\n\n"
        f"| Métrique | Valeur |\n|---|---|\n"
        f"| Exactitude | {_fmt_pct(m['accuracy'])} |\n"
        f"| Précision | {_fmt_pct(m['precision'])} |\n"
        f"| Rappel | {_fmt_pct(m['recall'])} |\n"
        f"| F1-score | {_fmt_pct(m['f1'])} |\n\n"
        f"Matrice de confusion : VP={m['tp']}, FP={m['fp']}, FN={m['fn']}, VN={m['tn']}\n"
    )


def _write_markdown(rows, relevance, domain, stats):
    path = os.path.join(_ROOT, "evaluation", "rapport_evaluation.md")
    lines = []
    lines.append("# Évaluation du moteur de scoring — SkillMatch AI\n")
    lines.append(f"Jeu de test annoté : **{stats['n']} paires (CV, offre)**. "
                 f"Seuil de présélection : **{stats['seuil']}/100**.\n")
    lines.append("## Méthodologie\n")
    lines.append("Chaque paire est annotée manuellement (vérité terrain) selon deux axes : "
                 "*pertinence* du candidat pour l'offre et *appartenance hors-domaine*. "
                 "Le moteur `compute_scoring` est exécuté sur des données structurées "
                 "(`cv_data`/`req_data`), ce qui isole le modèle de scoring et rend "
                 "l'évaluation reproductible.\n")

    lines.append("## Résultats détaillés par cas\n")
    lines.append("| Cas | Score | Décision | Retenu | Hors-domaine | Famille détectée |")
    lines.append("|---|---|---|---|---|---|")
    for r in rows:
        lines.append(f"| {r['id']} | {r['score']} | {r['decision']} | "
                     f"{'oui' if r['predit_retenu'] else 'non'} | "
                     f"{'oui' if r['predit_hors_domaine'] else 'non'} | "
                     f"{r['famille_detectee']} |")
    lines.append("")

    lines.append("## Métriques\n")
    lines.append(_md_metrics_block(relevance))
    lines.append("")
    lines.append(_md_metrics_block(domain))

    lines.append("## Séparation des scores\n")
    lines.append(f"- Score moyen des profils **pertinents** : "
                 f"**{stats['score_moyen_pertinents']}/100**")
    lines.append(f"- Score moyen des profils **non pertinents** : "
                 f"**{stats['score_moyen_non_pertinents']}/100**")
    lines.append("\n> Un écart net entre ces deux moyennes démontre le pouvoir "
                 "discriminant du modèle.\n")

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print("Rapport écrit ->", path)


if __name__ == "__main__":
    run()
