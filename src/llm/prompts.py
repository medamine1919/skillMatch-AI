from __future__ import annotations


def build_cv_parsing_prompt(cv_text: str) -> str:
    return f'''
Parse the following CV text and return ONLY valid JSON.
Do not add markdown, comments, or explanations.

Required JSON schema:
{{
  "full_name": "",
  "email": "",
  "phone": "",
  "location": "",
  "summary": "",
  "skills_technical": [],
  "skills_soft": [],
  "languages": [],
  "certifications": [],
  "education": [
    {{
      "degree": "",
      "field": "",
      "institution": "",
      "start_date": "",
      "end_date": ""
    }}
  ],
  "experience": [
    {{
      "job_title": "",
      "company": "",
      "start_date": "",
      "end_date": "",
      "duration_months": 0,
      "description": "",
      "skills_used": []
    }}
  ],
  "projects": [],
  "teaching_signals": [],
  "mentoring_signals": [],
  "youth_education_signals": [],
  "estimated_years_experience": 0
}}

Rules:
- projects must be a list of simple text descriptions only, NOT objects.
- Keep arrays empty if information is missing.
- Infer soft skills only if clearly supported by the CV.
- Teaching or youth education signals must be extracted only if there are textual clues.
- Return only JSON.

CV text:
"""
{cv_text[:15000]}
"""
'''


def build_requirement_parsing_prompt(requirement_text: str, input_mode: str) -> str:
    return f'''
Parse the following recruiter input into a structured requirement JSON.
The input can be a free hiring need or a pasted job offer.
Return ONLY valid JSON.

Required JSON schema:
{{
  "input_mode": "{input_mode}",
  "is_valid_job": true,
  "job_title": "",
  "contract_type": "",
  "location": "",
  "target_sector": "IT / e-learning",
  "required_speciality": "",
  "required_skills": [],
  "preferred_skills": [],
  "soft_skills": [],
  "languages_required": [],
  "experience_required_years": 0,
  "education_requirements": [],
  "teaching_required": false,
  "mentoring_preferred": false,
  "audience_type": "",
  "responsibilities": [],
  "keywords": [],
  "priority_criteria": []
}}

Rules:
- "is_valid_job": set to FALSE if the input is gibberish, random characters, or is
  clearly NOT a hiring need / job description. Set to TRUE only if it describes a real role.
- "job_title": copy the recruiter's actual need FAITHFULLY (e.g. "expert en agriculture").
  NEVER replace it with an IT job if the input is not about IT.
- "required_speciality": ONLY if the job is clearly an IT / e-learning tech role,
  set it to the most relevant among:
  AI/Data, Web Dev, Robotics/Embedded, Mobile, Cybersecurity, Programming for Kids.
  If the job is NOT in IT / e-learning (e.g. agriculture, mechanics, law, medicine,
  cooking, construction...), leave "required_speciality" EMPTY ("") and DO NOT force
  an IT speciality. Put the real domain words in "keywords" instead.
- Extract both technical and educational/tutoring expectations when present.
- If it is a regular IT job offer without tutoring expectations, set teaching_required to false.
- Return only JSON.

Recruiter input:
"""
{requirement_text[:12000]}
"""
'''


def build_test_generation_prompt(skills, speciality: str, job_title: str, num_questions: int = 10) -> str:
    """Construit le prompt pour générer un QCM technique adapté au profil.
    On demande un JSON STRICT : liste d'objets {question, options[4], correct, skill}."""
    skills_str = ", ".join(skills) if skills else (speciality or "informatique générale")
    return f'''
Tu es un expert technique RH. Génère un QCM de {num_questions} questions pour évaluer
un candidat sur les compétences suivantes : {skills_str}.
Spécialité / poste visé : {speciality or job_title or "IT"}.

Contraintes STRICTES :
- {num_questions} questions à choix multiple, en FRANÇAIS.
- Chaque question a EXACTEMENT 4 options.
- Une seule bonne réponse par question.
- Niveau de difficulté progressif (facile -> avancé).
- Questions concrètes et pertinentes pour les compétences listées.

Réponds UNIQUEMENT avec un tableau JSON valide, sans texte autour, au format :
[
  {{
    "question": "énoncé de la question",
    "options": ["option A", "option B", "option C", "option D"],
    "correct": 0,
    "skill": "compétence évaluée"
  }}
]
Le champ "correct" est l'INDEX (0 à 3) de la bonne réponse dans "options".
'''


def build_explanation_prompt(cv_json: dict, requirement_json: dict, scoring_summary: dict) -> str:
    return f'''
Using the structured CV, structured requirement, and scoring summary below, write:
1) a short recruiter-friendly explanation in 2-3 sentences
2) a detailed explanation in bullet style as plain text

Return ONLY valid JSON:
{{
  "short_explanation": "",
  "detailed_explanation": ""
}}

Structured CV:
{cv_json}

Structured requirement:
{requirement_json}

Scoring summary:
{scoring_summary}
'''
