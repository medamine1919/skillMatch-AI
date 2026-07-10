"""
=============================================================================
 FastAPI Server — SkillMatch AI  (microservice IA Python)
-----------------------------------------------------------------------------
 Ce serveur est le "cerveau IA" appelé par le backend Java (Spring Boot).
 Il expose une API REST qui réalise le PIPELINE COMPLET d'analyse d'un CV :

   1. Réception du fichier (PDF/Word/image) + l'exigence du poste (texte).
   2. Extraction du texte brut (avec OCR si image).
   3. Validation : est-ce bien un CV ?
   4. Parsing par LLM (Groq Llama) -> données structurées (cv_data, req_data).
      Repli sur des règles locales si le LLM est indisponible.
   5. Scoring multi-critères adaptatif (compute_scoring).
   6. Renvoi d'un JSON riche (scores, explications, recommandations).

 Il expose aussi l'endpoint de Talent Search (RAG) pour la recherche de profils.

 Le découpage en "Helpers" (fonctions de mise en forme) + "Endpoints"
 (routes HTTP) garde le code lisible.
=============================================================================
"""

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import logging
from pathlib import Path
from typing import Optional, Dict, Any, List
import json

from src.config import GROQ_API_KEY, ensure_directories
from src.ingestion.file_handler import save_uploaded_file
from src.ingestion.text_extractor import extract_text
from src.llm.cv_parser_llm import parse_cv_with_llm
from src.llm.requirement_parser_llm import parse_requirement_with_llm
from src.parsing.cv_document_validator import validate_cv_text, validate_parsed_cv_data
from src.parsing.requirement_validator import validate_requirement_text
from src.parsing.local_parsers import parse_cv_text_locally, parse_requirement_text_locally
from src.parsing.validators import validate_cv_json
from src.scoring.scoring_engine import compute_scoring
from src.scoring.criteria_explainer import build_criteria_explanations
from src.scoring.talent_search import search_candidates
from src.llm.test_generator_llm import generate_test_questions
from pydantic import ValidationError, BaseModel


# ── Helpers ────────────────────────────────────────────────────────────────────

def _experience_duration(exp: Dict[str, Any]) -> str:
    """Construit un libellé de durée lisible pour une expérience.
    Priorité aux dates début/fin ; sinon convertit duration_months en
    "X an(s) Y mois". Renvoie une chaîne vide si rien n'est exploitable."""
    start = str(exp.get("start_date", "")).strip()
    end   = str(exp.get("end_date",   "")).strip()
    if start and end:
        return f"{start} – {end}"
    if start:
        return start
    if end:
        return end
    months = exp.get("duration_months")
    if isinstance(months, (int, float)) and months > 0:
        years = int(months) // 12
        rem   = int(months) % 12
        if years and rem:
            return f"{years} an{'s' if years>1 else ''} {rem} mois"
        if years:
            return f"{years} an{'s' if years>1 else ''}"
        return f"{int(months)} mois"
    return ""


def _normalize_experience(cv: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Met les expériences du CV dans un format uniforme et stable pour le
    frontend (title/company/duration/description), peu importe comment le LLM
    a nommé les champs (job_title vs title...)."""
    result = []
    for exp in cv.get("experience", []) or []:
        if not isinstance(exp, dict):
            continue
        result.append({
            "title":       exp.get("job_title", exp.get("title", "")),
            "company":     exp.get("company", ""),
            "duration":    _experience_duration(exp),
            "description": exp.get("description", ""),
        })
    return result


def _normalize_education(cv: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Met les formations dans un format uniforme (degree/field/institution/year)
    pour un affichage cohérent côté frontend."""
    result = []
    for edu in cv.get("education", []) or []:
        if not isinstance(edu, dict):
            continue
        result.append({
            "degree":      edu.get("degree", ""),
            "field":       edu.get("field",  ""),
            "institution": edu.get("institution", ""),
            "year":        edu.get("end_date", "") or edu.get("start_date", ""),
        })
    return result


def _generate_recommendations(scores: Dict[str, Any], cv: Dict[str, Any]) -> List[str]:
    """Generate actionable, French-language recommendations from scoring data."""
    recs: List[str] = []
    final = scores.get("final_score", 0)
    ws    = scores.get("weighted_scores", {})

    # Profil hors périmètre : message prioritaire et explicite.
    if scores.get("out_of_scope"):
        ext = scores.get("requirement_external_domain") or scores.get("cv_external_domain") or ""
        recs.append(
            "🚫 Profil hors domaine — l'exigence du poste et le CV relèvent de "
            "domaines différents" + (f" (domaine détecté : {ext})" if ext else "")
            + ". Le score est volontairement très bas."
        )

    # Global decision
    if final >= 85:
        recs.append("✅ Profil excellent — candidat fortement recommandé pour entretien")
    elif final >= 70:
        recs.append("👍 Profil solide — candidat recommandé pour entretien")
    elif final >= 55:
        recs.append("📋 Profil modéré — à examiner avec attention")
    else:
        recs.append("⚠️ Profil insuffisant — ne correspond pas aux critères minimums")

    # Per-criteria feedback — on utilise les POIDS RÉELLEMENT APPLIQUÉS
    # (adaptatifs selon le poste), sinon les poids par défaut.
    DEFAULT_MAX = {
        "speciality_match":   25,
        "technical_skills":   25,
        "relevant_experience": 15,
        "pedagogy_tutoring":  15,
        "soft_skills":        10,
        "semantic_similarity": 10,
    }
    applied = scores.get("applied_weights") or {}
    MAX = {k: (applied.get(k) or DEFAULT_MAX[k]) for k in DEFAULT_MAX}
    LABELS = {
        "speciality_match":   "Spécialité",
        "technical_skills":   "Compétences techniques",
        "relevant_experience": "Expérience",
        "pedagogy_tutoring":  "Formation",
        "soft_skills":        "Soft Skills",
        "semantic_similarity": "Similarité sémantique",
    }
    GOOD = {
        "speciality_match":   "La spécialité du candidat correspond au poste",
        "technical_skills":   "Les compétences techniques sont bien adaptées",
        "relevant_experience": "L'expérience professionnelle est pertinente",
        "pedagogy_tutoring":  "Le parcours académique est adapté",
        "soft_skills":        "Les soft skills sont bien développés",
        "semantic_similarity": "Le profil global est cohérent avec l'offre",
    }
    WEAK = {
        "speciality_match":   "La spécialité du candidat diverge du profil recherché",
        "technical_skills":   "Les compétences techniques sont insuffisantes ou incomplètes",
        "relevant_experience": "L'expérience professionnelle est limitée par rapport aux attentes",
        "pedagogy_tutoring":  "La formation académique ne correspond pas pleinement",
        "soft_skills":        "Les soft skills sont peu présents ou non détaillés",
        "semantic_similarity": "Le profil global présente peu de cohérence avec l'offre",
    }

    for key, max_pts in MAX.items():
        score = ws.get(key, 0)
        ratio = score / max_pts if max_pts else 0
        if ratio >= 0.75:
            recs.append(f"✅ {LABELS[key]} : {GOOD[key]} ({score:.1f}/{max_pts} pts)")
        elif ratio >= 0.50:
            recs.append(f"📋 {LABELS[key]} : Niveau satisfaisant mais perfectible ({score:.1f}/{max_pts} pts)")
        else:
            recs.append(f"❌ {LABELS[key]} : {WEAK[key]} ({score:.1f}/{max_pts} pts)")

    # Speciality matching note
    cv_spe  = scores.get("cv_speciality", "")
    req_spe = scores.get("requirement_speciality", "")
    if cv_spe and req_spe:
        if cv_spe == req_spe:
            recs.append(f"🎯 Spécialité exacte : {cv_spe} ↔ {req_spe}")
        else:
            recs.append(f"⚡ Spécialité candidate ({cv_spe}) ≠ poste ({req_spe}) — vérifier l'adéquation")

    return recs


# ── App setup ──────────────────────────────────────────────────────────────────

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="SkillMatch AI — CV Analysis API",
    description="Analyse intelligente de CVs par NLP et scoring multi-critères",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:4200", "http://localhost:8080",
                   "http://localhost:3000", "http://localhost:8082"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

ensure_directories()


# ── Endpoints ──────────────────────────────────────────────────────────────────

@app.get("/health")
async def health_check():
    # Endpoint de "santé" : permet à Docker / au backend de vérifier que le
    # service tourne et de savoir si le LLM (Groq) est bien configuré.
    return {
        "status": "ok",
        "service": "SkillMatch AI — CV Analysis API",
        "version": "2.0.0",
        "llm_configured": bool(GROQ_API_KEY),
        "model": "llama-3.3-70b-versatile" if GROQ_API_KEY else "local_rules",
    }


@app.post("/score")
async def score_cv(
    file: UploadFile = File(...),
    requirements: Optional[str] = Form(None)
) -> Dict[str, Any]:
    """
    Full CV analysis pipeline:
    1. Save & validate file
    2. Extract text (PDF/DOCX/OCR)
    3. Validate CV document structure
    4. Parse CV and requirements with Groq or local rules
    5. Schema validation
    6. Multi-criteria scoring (100 pts)
    7. Return structured JSON
    """
    try:
        # ÉTAPE 0 — VALIDATION DE L'EXIGENCE (anti "garbage in" / anti-hallucination).
        # Si une exigence est fournie mais qu'elle est du charabia, on refuse AVANT
        # tout traitement (rapide) : un texte sans sens ne doit jamais produire de score.
        if requirements and requirements.strip():
            req_ok, req_reason = validate_requirement_text(requirements)
            if not req_ok:
                raise HTTPException(400, {"message": req_reason, "reason": "invalid_requirement"})

        # ÉTAPE 1 — Lecture du fichier uploadé en mémoire (octets bruts).
        logger.info(f"📥 Processing: {file.filename}")
        file_content = await file.read()

        # Petite classe "fichier temporaire" : adapte l'upload FastAPI à
        # l'interface attendue par save_uploaded_file (name/size/getbuffer).
        class TempFile:
            def __init__(self, name: str, content: bytes):
                self.name = name
                self.size = len(content)
                self._content = content

            def getbuffer(self):
                return self._content

        # On enregistre le fichier sur disque (avec contrôle du format/taille).
        try:
            file_path = save_uploaded_file(TempFile(file.filename, file_content))
        except ValueError as e:
            raise HTTPException(400, str(e))

        # ÉTAPE 2 & 3 — Extraction du texte (OCR si besoin) puis validation
        # que le document ressemble bien à un CV (sinon on refuse proprement).
        try:
            cv_text = extract_text(file_path)
            if not cv_text or len(cv_text.strip()) < 20:
                raise ValueError("Texte insuffisant extrait du fichier")

            validation = validate_cv_text(cv_text)
            if not validation.is_cv:
                raise HTTPException(400, {
                    "message": f"Ce document ne ressemble pas à un CV (confiance: {int(validation.confidence * 100)}%). Merci de vérifier le fichier.",
                    "reasons": validation.reasons,
                    "score": validation.score,
                })
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(400, f"Erreur extraction texte: {e}")

        # ÉTAPE 4 — Parsing du CV par le LLM (Groq Llama) vers une structure JSON.
        # En cas d'échec du LLM, on bascule sur un parser local à base de règles
        # (bloc except plus bas) : le service reste fonctionnel sans IA externe.
        cv_data: Dict[str, Any]
        try:
            parsed = parse_cv_with_llm(cv_text)
            cv_data = validate_cv_json(parsed)
            cv_data["raw_text"] = cv_text
            data_val = validate_parsed_cv_data(cv_data)
            if not data_val.is_cv:
                raise HTTPException(400, {
                    "message": f"Données extraites non conformes à un CV (confiance: {int(data_val.confidence * 100)}%).",
                    "reasons": data_val.reasons,
                    "score": data_val.score,
                })
        except HTTPException:
            raise
        except Exception as e:
            logger.warning(f"CV parsing fallback error: {e}")
            cv_data = validate_cv_json(parse_cv_text_locally(cv_text))

        # Parsing de l'EXIGENCE DU POSTE (texte libre du recruteur) vers une
        # structure JSON. Même principe : LLM d'abord, repli local sinon.
        try:
            if requirements and requirements.strip():
                try:
                    req_data = parse_requirement_with_llm(requirements, input_mode="text")
                except Exception as e:
                    logger.warning(f"Requirement parsing fallback error: {e}")
                    req_data = parse_requirement_text_locally(requirements, input_mode="text")
                # GARDE-FOU ANTI-HALLUCINATION : si le LLM lui-même juge que ce
                # n'est pas une vraie offre (is_valid_job=false), on refuse.
                if req_data.get("is_valid_job") is False:
                    raise HTTPException(400, {
                        "message": "Cette description ne semble pas être une offre d'emploi valide. "
                                   "Précisez le poste, les compétences et l'expérience attendues.",
                        "reason": "invalid_requirement"})
            else:
                # Aucune exigence fournie : on part d'un gabarit vide (le scoring
                # s'adaptera et restera neutre sur les critères non renseignés).
                req_data = {
                    "input_mode": "text",
                    "job_title": "",
                    "contract_type": "",
                    "location": "",
                    "target_sector": "IT / e-learning",
                    "required_speciality": "",
                    "required_skills": [],
                    "preferred_skills": [],
                    "soft_skills": [],
                    "languages_required": [],
                    "experience_required_years": 0.0,
                    "education_requirements": [],
                    "teaching_required": False,
                    "mentoring_preferred": False,
                    "audience_type": "",
                    "responsibilities": [],
                    "keywords": [],
                    "priority_criteria": [],
                }

            req_data["raw_text"] = requirements or ""

            # ÉTAPE 5 & 6 — SCORING multi-critères adaptatif (le cœur IA).
            scores = compute_scoring(cv_data, req_data)
        except HTTPException:
            # Erreur métier volontaire (ex: exigence invalide) -> on la laisse remonter
            # telle quelle (sinon le filet ci-dessous la transformerait en score 50).
            raise
        except Exception as e:
            # Filet de sécurité : si le scoring plante, on renvoie un résultat
            # neutre (50/100) plutôt que de faire échouer toute la requête.
            logger.warning(f"Scoring error: {e}")
            scores = {
                "final_score": 50.0,
                "decision_key": "moderate",
                "decision_label": "Modéré",
                "recommendation_key": "review",
                "recommendation_label": "À examiner",
                "weighted_scores": {k: 0.0 for k in [
                    "speciality_match",
                    "technical_skills",
                    "relevant_experience",
                    "pedagogy_tutoring",
                    "soft_skills",
                    "semantic_similarity",
                ]},
                "cv_speciality": "",
                "requirement_speciality": "",
                "semantic_similarity_ratio": 0.0,
            }

        # ÉTAPE 7 — Construction de la RÉPONSE JSON renvoyée au backend Java,
        # qui la stockera puis la transmettra au frontend Angular.
        ws = scores.get("weighted_scores", {})   # notes pondérées par critère
        response = {
            "id": None,
            "candidateName": cv_data.get("full_name", "Candidat"),
            "email": cv_data.get("email", ""),
            "phone": cv_data.get("phone", ""),
            "scores": {
                "overallScore": round(scores.get("final_score", 50.0), 2),
                # Vraie note ÉDUCATION /100 (niveau diplôme + domaine + exigences)
                "educationScore": round(scores.get("education_result", {}).get("score", 0.0), 1),
                "experienceScore": round(ws.get("relevant_experience", 0.0), 2),
                "skillsScore": round(ws.get("technical_skills", 0.0), 2),
                "softSkillsScore": round(ws.get("soft_skills", 0.0), 2),
                "pedagogyScore": round(ws.get("pedagogy_tutoring", 0.0), 2),
            },
            "matchPercentage": round(scores.get("final_score", 50.0), 2),
            "analysis": {
                "skills": cv_data.get("skills_technical", []),
                "softSkills": cv_data.get("skills_soft", []),
                "experience": _normalize_experience(cv_data),
                "education": _normalize_education(cv_data),
                "languages": cv_data.get("languages", []),
                "certifications": cv_data.get("certifications", []),
                "projects": cv_data.get("projects", []),
                "summary": cv_data.get("summary", ""),
                "location": cv_data.get("location", ""),
                "specialityCv": scores.get("cv_speciality", ""),
                "specialityRequirement": scores.get("requirement_speciality", ""),
                "educationScore": round(scores.get("education_result", {}).get("score", 0.0), 1),
                "educationLevel": scores.get("education_result", {}).get("level_label", ""),
                "educationExplanation": scores.get("education_result", {}).get("explanation", ""),
                "detectedJobProfile": scores.get("business_context", {}).get("family_label", ""),
                "detectedJobProfileConfidence": scores.get("business_context", {}).get("confidence", 0.0),
                "appliedWeights": scores.get("applied_weights", {}),
                "activeCriteria": scores.get("active_criteria", {}),
                "outOfScope": scores.get("out_of_scope", False),
                "cvExternalDomain": scores.get("cv_external_domain", ""),
                "requirementExternalDomain": scores.get("requirement_external_domain", ""),
                "decisionLabel": scores.get("decision_label", ""),
                "recommendationLabel": scores.get("recommendation_label", ""),
                "semanticSimilarityRatio": round(scores.get("semantic_similarity_ratio", 0.0), 4),
                "weightedScores": {k: round(v, 2) for k, v in ws.items()},
                "criteriaExplanations": build_criteria_explanations(scores),
                "extractedTextPreview": cv_text[:1500],
            },
            "recommendations": _generate_recommendations(scores, cv_data),
            "fullText": cv_text[:20000],  # texte complet du CV (pour Talent Search)
            "timestamp": None,
        }

        logger.info(f"✅ Analysis done — score: {response['scores']['overallScore']}/100")
        return response

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        raise HTTPException(500, f"Erreur serveur: {e}")


# ── Génération de test technique (QCM par IA) ───────────────────────────────

class GenerateTestRequest(BaseModel):
    """Corps de la demande de génération de QCM."""
    skills: List[str] = []
    speciality: str = ""
    job_title: str = ""
    num_questions: int = 10


@app.post("/generate-test")
async def generate_test(payload: GenerateTestRequest):
    """Génère un QCM technique adapté aux compétences/à la spécialité.
    Renvoie {questions: [{question, options[4], correct, skill}, ...]}."""
    try:
        questions = generate_test_questions(
            skills=payload.skills,
            speciality=payload.speciality,
            job_title=payload.job_title,
            num_questions=payload.num_questions,
        )
        return {"count": len(questions), "questions": questions}
    except Exception as e:
        logger.error(f"generate-test error: {e}")
        raise HTTPException(500, f"Erreur génération test: {e}")


# ── Talent Search (RAG) ─────────────────────────────────────────────────────
# Recherche de profils en langage naturel. Pydantic (BaseModel) valide
# automatiquement le corps JSON reçu (types, champs obligatoires).

class TalentCandidate(BaseModel):
    """Un candidat à classer : son identifiant + le texte de son profil (CV)."""
    id: str
    text: str


class TalentSearchRequest(BaseModel):
    """Corps de la requête de recherche de talents."""
    query: str                          # requête du recruteur en langage naturel
    candidates: List[TalentCandidate]   # vivier à classer
    top_k: int = 50                     # nb max de résultats renvoyés
    min_score: float = 0.0              # seuil minimal de pertinence


@app.post("/talent-search")
async def talent_search(payload: TalentSearchRequest):
    """
    Classe le vivier de candidats par pertinence sémantique (RAG hybride)
    vis-à-vis d'une requête en langage naturel.
    """
    try:
        candidates = [{"id": c.id, "text": c.text} for c in payload.candidates]
        ranked = search_candidates(
            query=payload.query,
            candidates=candidates,
            top_k=payload.top_k,
            min_score=payload.min_score,
        )
        return {"query": payload.query, "count": len(ranked), "results": ranked}
    except Exception as e:
        logger.error(f"Talent search error: {e}", exc_info=True)
        raise HTTPException(500, f"Erreur recherche: {e}")


@app.get("/")
async def root():
    return {
        "service": "SkillMatch AI — CV Analysis API",
        "version": "2.0.0",
        "docs":    "/docs",
        "health":  "/health",
        "score":   "POST /score"
    }


if __name__ == "__main__":
    logger.info("🚀 Starting SkillMatch AI FastAPI on http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
