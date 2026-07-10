"""
=============================================================================
 SYNONYMES — dictionnaire métier PARTAGÉ + helpers de correspondance.
-----------------------------------------------------------------------------
 Source UNIQUE des synonymes, utilisée par :
   - le Talent Search (RAG)            -> retrouver des candidats ;
   - le matching exigence ↔ CV          -> noter selon ce que le recruteur demande.

 Objectif : qu'un terme tapé par le recruteur retrouve son équivalent dans le
 CV même s'il est écrit autrement (autre langue, abréviation, synonyme métier).
 Ex : "français" ≡ "french", "programmation" ≡ "coding", "bdd" ≡ "database".

 Chaque clé (en minuscule) pointe vers TOUTES ses variantes équivalentes.
=============================================================================
"""
from __future__ import annotations

import re
import unicodedata
from rapidfuzz.distance import DamerauLevenshtein

SYNONYMS = {
    # ----- Domaines IA / Data -----
    "ia": ["ia", "intelligence artificielle", "artificial intelligence", "ai",
           "machine learning", "deep learning", "réseaux de neurones"],
    "ai": ["ai", "ia", "intelligence artificielle", "machine learning", "deep learning"],
    "ml": ["ml", "machine learning", "apprentissage automatique", "scikit-learn"],
    "deeplearning": ["deep learning", "réseaux de neurones", "neural networks", "cnn", "rnn"],
    "data": ["data", "données", "data science", "data analyst", "analyse de données",
             "big data", "datawarehouse", "power bi", "sql"],
    "datascience": ["data science", "data scientist", "données", "data analyst"],
    "nlp": ["nlp", "traitement du langage", "natural language processing", "text mining"],
    "bi": ["bi", "business intelligence", "power bi", "tableau", "reporting", "datawarehouse"],
    "datawarehouse": ["datawarehouse", "data warehouse", "entrepôt de données", "etl"],

    # ----- Web / Mobile / Logiciel -----
    "web": ["web", "frontend", "front-end", "backend", "back-end", "fullstack", "full stack"],
    "frontend": ["frontend", "front-end", "front", "interface", "ui"],
    "backend": ["backend", "back-end", "serveur", "api"],
    "fullstack": ["fullstack", "full stack", "full-stack"],
    "mobile": ["mobile", "android", "ios", "flutter", "react native", "application mobile"],
    "api": ["api", "rest", "restful", "web service", "microservices"],

    # ----- DevOps / Cloud -----
    "devops": ["devops", "ci/cd", "docker", "kubernetes", "jenkins", "intégration continue"],
    "cloud": ["cloud", "aws", "azure", "gcp", "google cloud", "infonuagique"],
    "bdd": ["bdd", "base de données", "database", "sql", "mysql", "postgresql", "mongodb"],
    "database": ["database", "base de données", "bdd", "sql"],

    # ----- Cybersécurité -----
    "securite": ["securite", "sécurité", "cybersécurité", "cybersecurity", "security", "pentest"],
    "cybersecurite": ["cybersécurité", "cybersecurity", "sécurité informatique", "security"],

    # ----- Langues parlées (FR <-> EN) -----
    "francais": ["francais", "français", "french", "langue française"],
    "french": ["french", "francais", "français"],
    "anglais": ["anglais", "english", "langue anglaise"],
    "english": ["english", "anglais"],
    "arabe": ["arabe", "arabic"],
    "arabic": ["arabic", "arabe"],
    "espagnol": ["espagnol", "spanish", "español"],
    "spanish": ["spanish", "espagnol"],
    "allemand": ["allemand", "german", "deutsch"],
    "german": ["german", "allemand"],
    "italien": ["italien", "italian"],
    "bilingue": ["bilingue", "bilingual", "multilingue", "multilingual"],

    # ----- Programmation (concept) -----
    "programmation": ["programmation", "programming", "coding", "développement", "developpement", "code"],
    "programming": ["programming", "programmation", "coding", "code"],
    "coding": ["coding", "programmation", "programming", "code"],
    "développement": ["développement", "developpement", "development", "développeur", "developer"],
    "developpement": ["developpement", "développement", "development"],

    # ----- Langages & frameworks (variantes d'écriture) -----
    "python": ["python", "django", "flask", "fastapi", "pandas"],
    "java": ["java", "spring", "spring boot", "springboot", "j2ee"],
    "javascript": ["javascript", "js", "node", "nodejs", "node.js", "typescript", "ts"],
    "angular": ["angular", "angularjs"],
    "react": ["react", "reactjs", "react.js"],
    "csharp": ["c#", "csharp", ".net", "dotnet", "asp.net"],
    "php": ["php", "laravel", "symfony"],

    # ----- Métiers / rôles -----
    "developpeur": ["developpeur", "développeur", "developer", "dev", "programmeur"],
    "developer": ["developer", "développeur", "developpeur", "programmer"],
    "ingenieur": ["ingenieur", "ingénieur", "engineer"],
    "engineer": ["engineer", "ingénieur", "ingenieur"],
    "formateur": ["formateur", "formatrice", "trainer", "enseignant", "coach", "instructeur"],
    "coach": ["coach", "formateur", "trainer", "mentor", "tuteur", "accompagnateur"],
    "enseignant": ["enseignant", "enseignante", "teacher", "professeur", "formateur"],
    "manager": ["manager", "responsable", "chef", "lead", "gestionnaire", "encadrant"],
    "designer": ["designer", "ux", "ui", "ux/ui", "graphiste", "design"],

    # ----- Soft skills (FR <-> EN) -----
    "communication": ["communication", "communicant", "communiquer", "relationnel"],
    "equipe": ["equipe", "équipe", "team", "teamwork", "travail en équipe", "collaboration"],
    "teamwork": ["teamwork", "travail en équipe", "équipe", "collaboration"],
    "leadership": ["leadership", "meneur", "leader", "management"],
    "autonomie": ["autonomie", "autonome", "autonomous", "indépendant"],
    "creativite": ["creativite", "créativité", "créatif", "creative", "creativity"],
    "rigueur": ["rigueur", "rigoureux", "rigorous", "rigueur professionnelle"],
    "adaptabilite": ["adaptabilite", "adaptabilité", "adaptable", "flexible", "flexibilité"],

    # ----- Niveaux d'expérience -----
    "junior": ["junior", "débutant", "debutant", "entry level", "stagiaire"],
    "senior": ["senior", "confirmé", "confirme", "expérimenté", "experimente", "expert"],
    "stage": ["stage", "stagiaire", "internship", "intern", "pfe"],

    # ----- Tests / Qualité logicielle -----
    "test": ["test", "testing", "qa", "quality assurance", "tests unitaires",
             "tests automatisés", "selenium", "junit", "cypress", "recette"],
    "qa": ["qa", "quality assurance", "testeur", "tests", "assurance qualité"],

    # ----- Gestion de projet / Méthodes Agiles -----
    "agile": ["agile", "scrum", "kanban", "sprint", "méthode agile"],
    "scrum": ["scrum", "scrum master", "agile", "sprint", "product owner"],
    "gestionprojet": ["gestion de projet", "project management", "chef de projet",
                      "project manager", "pmo", "pilotage"],
    "product": ["product owner", "po", "product manager", "chef de produit"],

    # ----- Réseaux / Systèmes / Administration -----
    "reseau": ["reseau", "réseau", "network", "réseaux", "tcp/ip", "routage", "cisco"],
    "network": ["network", "réseau", "réseaux", "networking"],
    "systeme": ["systeme", "système", "system", "sysadmin", "administration système",
                "linux", "windows server", "unix"],
    "linux": ["linux", "unix", "ubuntu", "debian", "bash", "shell"],
    "virtualisation": ["virtualisation", "virtualization", "vmware", "hyperv", "proxmox"],

    # ----- ERP / Gestion d'entreprise -----
    "erp": ["erp", "sap", "odoo", "sage", "progiciel", "pgi"],
    "crm": ["crm", "salesforce", "hubspot", "relation client", "gestion client"],

    # ----- Data Engineering / Big Data -----
    "etl": ["etl", "elt", "talend", "ssis", "pipeline de données", "data engineering"],
    "bigdata": ["big data", "hadoop", "spark", "kafka", "data lake"],
    "analyse": ["analyse", "analytics", "analyste", "analyst", "analytique"],

    # ----- IoT / Embarqué / Robotique -----
    "iot": ["iot", "internet des objets", "objets connectés", "embarqué", "embedded"],
    "robotique": ["robotique", "robotics", "arduino", "raspberry", "automatisme"],
    "embarque": ["embarque", "embarqué", "embedded", "microcontrôleur", "firmware"],

    # ----- Jeux vidéo / 3D -----
    "jeuxvideo": ["jeux vidéo", "jeu vidéo", "game", "gaming", "unity", "unreal", "game dev"],
    "3d": ["3d", "modélisation 3d", "blender", "3ds max", "maya"],

    # ----- Design / UX -----
    "design": ["design", "ux", "ui", "ux/ui", "figma", "adobe xd", "maquette", "graphisme"],
    "graphisme": ["graphisme", "graphiste", "photoshop", "illustrator", "design graphique"],

    # ----- Versioning / Outils -----
    "git": ["git", "github", "gitlab", "bitbucket", "versioning", "contrôle de version"],
    "jira": ["jira", "trello", "ticketing", "suivi de tâches"],

    # ----- Bureautique / Office -----
    "excel": ["excel", "tableur", "spreadsheet", "vba", "google sheets"],
    "office": ["office", "bureautique", "word", "powerpoint", "microsoft office"],

    # ----- E-learning (cœur de métier DecliTech) -----
    "elearning": ["elearning", "e-learning", "formation en ligne", "lms", "moodle",
                  "enseignement à distance", "edtech"],
    "pedagogie": ["pedagogie", "pédagogie", "pedagogy", "enseignement", "didactique",
                  "tutorat", "animation", "accompagnement"],
    "scratch": ["scratch", "blockly", "programmation enfants", "kids coding", "code.org"],

    # ----- Langues parlées (complément) -----
    "portugais": ["portugais", "portuguese", "português"],
    "chinois": ["chinois", "chinese", "mandarin"],
    "russe": ["russe", "russian"],
    "turc": ["turc", "turkish"],
    "neerlandais": ["neerlandais", "néerlandais", "dutch"],
    "langues": ["langues", "languages", "multilingue", "polyglotte", "linguistique"],

    # ----- Langages de programmation (complément) -----
    "c": ["c", "langage c", "ansi c"],
    "cpp": ["cpp", "c++", "c plus plus"],
    "kotlin": ["kotlin", "android kotlin"],
    "swift": ["swift", "ios swift", "swiftui"],
    "go": ["go", "golang"],
    "rust": ["rust", "rust lang"],
    "ruby": ["ruby", "rails", "ruby on rails"],
    "scala": ["scala", "spark scala"],
    "r": ["r", "rstudio", "langage r"],
    "matlab": ["matlab", "simulink", "octave"],
    "perl": ["perl"],
    "dart": ["dart", "flutter dart"],
    "sql": ["sql", "requêtes sql", "pl/sql", "t-sql", "mysql", "postgresql"],
    "html": ["html", "html5", "css", "css3", "sass", "scss", "bootstrap", "tailwind"],

    # ----- Frameworks / bibliothèques (complément) -----
    "vue": ["vue", "vuejs", "vue.js", "nuxt"],
    "spring": ["spring", "spring boot", "springboot", "spring mvc", "hibernate", "jpa"],
    "dotnet": ["dotnet", ".net", "asp.net", "c#", "blazor", "entity framework"],
    "tensorflow": ["tensorflow", "keras", "pytorch", "deep learning"],
    "pandas": ["pandas", "numpy", "scipy", "matplotlib", "data analysis python"],
    "spark": ["spark", "pyspark", "apache spark", "big data"],

    # ----- Bases de données (complément) -----
    "mysql": ["mysql", "mariadb", "sql"],
    "postgresql": ["postgresql", "postgres", "sql"],
    "mongodb": ["mongodb", "mongo", "nosql", "document database"],
    "oracle": ["oracle", "oracle db", "pl/sql"],
    "redis": ["redis", "cache", "key-value"],
    "elasticsearch": ["elasticsearch", "elastic", "kibana", "elk"],
    "nosql": ["nosql", "mongodb", "cassandra", "dynamodb"],

    # ----- Cloud / DevOps (complément) -----
    "aws": ["aws", "amazon web services", "ec2", "s3", "lambda"],
    "azure": ["azure", "microsoft azure", "azure devops"],
    "gcp": ["gcp", "google cloud", "google cloud platform"],
    "docker": ["docker", "conteneur", "container", "containerisation"],
    "kubernetes": ["kubernetes", "k8s", "orchestration", "helm"],
    "terraform": ["terraform", "infrastructure as code", "iac", "ansible"],
    "jenkins": ["jenkins", "ci/cd", "gitlab ci", "github actions", "intégration continue"],

    # ----- Cybersécurité (complément) -----
    "pentest": ["pentest", "penetration testing", "test d'intrusion", "ethical hacking"],
    "soc": ["soc", "security operations", "siem", "surveillance sécurité"],
    "cryptographie": ["cryptographie", "cryptography", "chiffrement", "encryption", "ssl", "tls"],

    # ----- Data / BI (complément) -----
    "powerbi": ["powerbi", "power bi", "dax", "tableau de bord", "dashboard"],
    "tableau": ["tableau", "tableau software", "dataviz", "visualisation"],
    "dataviz": ["dataviz", "data visualization", "visualisation de données", "reporting"],
    "statistiques": ["statistiques", "statistics", "stats", "probabilités", "analyse statistique"],
    "excel_avance": ["excel avancé", "tcd", "tableau croisé dynamique", "macro", "vba"],

    # ----- Mobile (complément) -----
    "android": ["android", "kotlin", "java android", "android studio"],
    "ios": ["ios", "swift", "objective-c", "xcode"],
    "flutter": ["flutter", "dart", "cross-platform", "application mobile"],
    "reactnative": ["react native", "reactnative", "mobile js"],

    # ----- Méthodes / outils projet (complément) -----
    "kanban": ["kanban", "trello", "tableau kanban", "workflow"],
    "uml": ["uml", "modélisation", "merise", "diagramme", "conception"],
    "ci": ["ci", "ci/cd", "intégration continue", "déploiement continu"],

    # ----- Métiers IT (complément) -----
    "architecte": ["architecte", "architect", "architecture logicielle", "solution architect"],
    "consultant": ["consultant", "consulting", "conseil"],
    "analyste": ["analyste", "analyst", "business analyst", "analyste fonctionnel"],
    "administrateur": ["administrateur", "admin", "sysadmin", "dba", "administrateur système"],
    "support": ["support", "helpdesk", "support technique", "hotline", "assistance"],
    "scrummaster": ["scrum master", "scrummaster", "facilitateur agile"],
    "datascientist": ["data scientist", "datascientist", "scientifique des données"],
    "dataengineer": ["data engineer", "dataengineer", "ingénieur données", "etl developer"],

    # ----- Soft skills (complément) -----
    "organisation": ["organisation", "organisé", "organized", "gestion du temps", "planification"],
    "resolution": ["resolution", "résolution de problèmes", "problem solving", "esprit d'analyse"],
    "polyvalence": ["polyvalence", "polyvalent", "versatile", "multitâche"],
    "proactivite": ["proactivite", "proactivité", "proactif", "proactive", "initiative"],
    "esprit_critique": ["esprit critique", "critical thinking", "analyse critique"],
    "negociation": ["negociation", "négociation", "negotiation", "persuasion"],
    "empathie": ["empathie", "empathy", "écoute", "sens du relationnel"],
    "curiosite": ["curiosite", "curiosité", "curious", "apprentissage continu"],
    "stress": ["gestion du stress", "stress management", "résistance au stress", "sang-froid"],

    # ----- Marketing / Digital (familles support DecliTech) -----
    "marketing": ["marketing", "marketing digital", "digital marketing", "growth"],
    "seo": ["seo", "référencement", "sea", "google ads", "référencement naturel"],
    "communitymanager": ["community manager", "community management", "réseaux sociaux", "social media"],
    "contenu": ["contenu", "content", "rédaction", "copywriting", "création de contenu"],

    # ----- Finance / Gestion (familles support) -----
    "comptabilite": ["comptabilite", "comptabilité", "accounting", "comptable", "finance"],
    "finance": ["finance", "financier", "gestion financière", "analyse financière"],
    "audit": ["audit", "auditeur", "contrôle de gestion", "compliance"],

    # ----- RH / Recrutement (familles support) -----
    "rh": ["rh", "ressources humaines", "human resources", "hr"],
    "recrutement": ["recrutement", "recruitment", "sourcing", "talent acquisition", "recruteur"],
    "formation_rh": ["formation", "training", "développement des compétences", "onboarding"],

    # ----- Certifications fréquentes -----
    "certification": ["certification", "certifié", "certified", "diplômé", "habilitation"],
    "toeic": ["toeic", "toefl", "ielts", "certification anglais"],
    "pmp": ["pmp", "prince2", "certification gestion de projet"],
}


# ----------------------------------------------------------------------------
# INDEX INVERSÉ : chaque VARIANTE (pas seulement les clés) connaît TOUT son
# groupe de synonymes. Ainsi "résolution de problèmes" (une variante) retrouve
# "problem solving", et "c++" retrouve "cpp" — même si ce ne sont pas des clés.
# Construit une seule fois au chargement du module.
# ----------------------------------------------------------------------------
_VARIANT_INDEX: dict[str, set[str]] = {}
for _key, _variants in SYNONYMS.items():
    _group = set(v.lower() for v in _variants) | {_key.lower()}
    for _v in _group:
        _VARIANT_INDEX.setdefault(_v, set()).update(_group)


def term_in_text(term: str, text: str) -> bool:
    """Vrai si `term` apparaît comme MOT ENTIER dans `text` (évite les
    sous-chaînes : "ia" ne matche pas dans "stagiaire")."""
    return re.search(r"(?<![\wÀ-ÿ])" + re.escape(term) + r"(?![\wÀ-ÿ])", text) is not None


# ============================================================================
#  TOLÉRANCE AUX FAUTES DE FRAPPE (fuzzy) — robustesse de la détection.
# ----------------------------------------------------------------------------
#  On utilise la distance de Damerau-Levenshtein (gère substitutions, omissions,
#  ajouts ET inversions de lettres). Garde-fous stricts pour éviter les faux
#  positifs : longueur minimale, écart de longueur limité, nb d'éditions borné.
# ============================================================================
def _norm(s: str) -> str:
    """Minuscule + suppression des accents (séniore -> seniore)."""
    s = (s or "").lower().strip()
    return unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode("ascii")


def fuzzy_equal(a: str, b: str, min_len: int = 5) -> bool:
    """Deux MOTS sont-ils quasi identiques (faute de frappe tolérée) ?
    - mots courts (< 5 car.) : correspondance EXACTE seulement (protège C, Go, SQL…)
    - sinon : distance d'édition <= 1 (mots <=6 car.) ou <= 2 (mots plus longs)."""
    a, b = _norm(a), _norm(b)
    if not a or not b:
        return False
    if len(a) < min_len or len(b) < min_len:
        return a == b
    if abs(len(a) - len(b)) > 2:          # longueurs trop différentes -> non
        return False
    dist = DamerauLevenshtein.distance(a, b)
    max_edits = 1 if max(len(a), len(b)) <= 6 else 2
    return dist <= max_edits


def text_contains_term(text: str, term: str) -> bool:
    """Vrai si `term` est présent dans `text` en MOT ENTIER, OU via une faute
    de frappe (fuzzy) pour les termes d'un seul mot d'au moins 5 caractères.
    Sert à la détection tolérante (niveaux d'expérience, mots-clés…)."""
    text = text or ""
    if term_in_text(term.lower(), text.lower()):
        return True
    # Fuzzy : uniquement les termes d'UN seul mot, suffisamment longs.
    if " " in term or len(_norm(term)) < 5:
        return False
    for word in re.findall(r"[A-Za-zÀ-ÿ]{4,}", text):
        if fuzzy_equal(word, term):
            return True
    return False


def expand_term(term: str) -> list[str]:
    """Retourne toutes les variantes équivalentes d'un terme (lui-même inclus).
    Cherche d'abord dans l'index inversé (variantes ET clés), sinon renvoie
    le terme seul."""
    t = (term or "").lower().strip()
    if t in _VARIANT_INDEX:
        return list(_VARIANT_INDEX[t])
    return SYNONYMS.get(t, [t])


def terms_equivalent(a: str, b: str) -> bool:
    """
    Cœur du matching SÉMANTIQUE par dictionnaire : `a` (ex : compétence exigée)
    et `b` (ex : compétence du CV) sont-ils équivalents ?
    Vrai si : identiques, OU l'un est une variante/synonyme de l'autre,
    OU l'un apparaît comme mot entier dans la liste de variantes de l'autre.
    """
    a_l = (a or "").lower().strip()
    b_l = (b or "").lower().strip()
    if not a_l or not b_l:
        return False
    if a_l == b_l:
        return True

    a_vars = set(expand_term(a_l))
    b_vars = set(expand_term(b_l))
    # variantes communes (ex : "francais" et "french" partagent "french")
    if a_vars & b_vars:
        return True
    # une variante de a est présente (mot entier) dans b, ou inversement
    if any(term_in_text(v, b_l) for v in a_vars):
        return True
    if any(term_in_text(v, a_l) for v in b_vars):
        return True
    # Dernier recours : tolérance aux fautes de frappe sur termes d'un seul mot
    # (ex : "jinior" ≈ "junior", "pyhton" ≈ "python"). Garde-fous dans fuzzy_equal.
    if " " not in a_l and " " not in b_l and fuzzy_equal(a_l, b_l):
        return True
    return False
