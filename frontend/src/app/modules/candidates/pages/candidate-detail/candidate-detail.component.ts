import { Component, OnInit, inject } from '@angular/core';
import { CVAnalysisService, CandidateDetail } from '../../../../services/cv-analysis.service';
import { TestService } from '../../../../services/test.service';
import { ActivatedRoute } from '@angular/router';
import { DomSanitizer, SafeHtml } from '@angular/platform-browser';

interface ComparisonMetric {
  key: string;
  label: string;
  maxPoints: number;
  description: string;
}

/**
 * ============================================================================
 *  CandidateDetailComponent — fiche détaillée d'un candidat.
 * ----------------------------------------------------------------------------
 *  Affiche le profil complet + l'analyse du matching CV poste (notes par
 *  critère, points forts/faibles, bandeau "hors domaine" le cas échéant).
 *
 *  Fonctionnalité spéciale : le SURLIGNAGE des critères de Talent Search. Si on
 *  arrive depuis une recherche (paramètre ?q=...), les mots recherchés (et leurs
 *  synonymes) sont mis en évidence dans le CV via highlight(). Le dictionnaire
 *  SYNONYMS est aligné avec celui du moteur RAG côté backend.
 * ============================================================================
 */
@Component({
  selector: 'app-candidate-detail',
  templateUrl: './candidate-detail.component.html',
  styleUrls: ['./candidate-detail.component.css']
})
export class CandidateDetailComponent implements OnInit {
  private readonly comparisonMetrics: ComparisonMetric[] = [
    {
      key: 'speciality_match',
      label: 'Spécialité',
      maxPoints: 25,
      description: 'Adéquation entre la spécialité du CV candidat et celle attendue par le poste.',
    },
    {
      key: 'technical_skills',
      label: 'Compétences techniques',
      maxPoints: 25,
      description: 'Correspondance entre les compétences techniques détectées et les besoins du poste.',
    },
    {
      key: 'relevant_experience',
      label: 'Expérience',
      maxPoints: 15,
      description: 'Pertinence du parcours professionnel par rapport au poste ciblé.',
    },
    {
      key: 'pedagogy_tutoring',
      label: 'Pédagogie / tutorat',
      maxPoints: 15,
      description: 'Capacité à former, accompagner ou encadrer selon les signaux du CV.',
    },
    {
      key: 'soft_skills',
      label: 'Soft skills',
      maxPoints: 10,
      description: 'Qualité des compétences comportementales détectées dans le CV.',
    },
    {
      key: 'semantic_similarity',
      label: 'Similarité sémantique',
      maxPoints: 10,
      description: 'Proximité globale entre le CV candidat et la fiche de poste.',
    },
  ];

  candidate: CandidateDetail | null = null;

  // ===== Envoi du test technique =====
  sendingTest = false;
  testMessage: string | null = null;
  testOk = false;
  loading = true;
  error: string | null = null;

  // ===== Surlignage des critères du Talent Search =====
  searchQueryText = '';
  searchKeywords: string[] = [];
  searchTerms: string[] = [];   // mots-clés + synonymes (pour surligner)
  hasSearch = false;

  // Expansion sémantique (ALIGNÉE avec le dictionnaire RAG côté backend
  // talent_search.py). Sert à surligner aussi les équivalents (FR/EN, synonymes).
  private static readonly SYNONYMS: Record<string, string[]> = {
    // Domaines IA / Data
    ia: ['ia', 'intelligence artificielle', 'artificial intelligence', 'ai', 'machine learning', 'deep learning'],
    ai: ['ai', 'ia', 'intelligence artificielle', 'machine learning', 'deep learning'],
    ml: ['ml', 'machine learning', 'apprentissage automatique', 'scikit-learn'],
    data: ['data', 'données', 'data science', 'data analyst', 'analyse de données', 'big data', 'power bi', 'sql'],
    nlp: ['nlp', 'traitement du langage', 'natural language processing'],
    bi: ['bi', 'business intelligence', 'power bi', 'reporting', 'datawarehouse'],
    // Web / mobile / cloud
    web: ['web', 'frontend', 'backend', 'fullstack', 'full stack'],
    frontend: ['frontend', 'front-end', 'interface', 'ui'],
    backend: ['backend', 'back-end', 'serveur', 'api'],
    mobile: ['mobile', 'android', 'ios', 'flutter', 'react native'],
    api: ['api', 'rest', 'restful', 'microservices'],
    devops: ['devops', 'ci/cd', 'docker', 'kubernetes'],
    cloud: ['cloud', 'aws', 'azure', 'gcp', 'google cloud'],
    bdd: ['bdd', 'base de données', 'database', 'sql', 'mysql', 'postgresql', 'mongodb'],
    securite: ['securite', 'sécurité', 'cybersécurité', 'cybersecurity', 'security'],
    // Langues parlées (FR <-> EN)
    francais: ['francais', 'français', 'french'],
    french: ['french', 'francais', 'français'],
    anglais: ['anglais', 'english'],
    english: ['english', 'anglais'],
    arabe: ['arabe', 'arabic'],
    arabic: ['arabic', 'arabe'],
    espagnol: ['espagnol', 'spanish', 'español'],
    allemand: ['allemand', 'german', 'deutsch'],
    bilingue: ['bilingue', 'bilingual', 'multilingue', 'multilingual'],
    // Programmation + langages
    programmation: ['programmation', 'programming', 'coding', 'développement', 'code'],
    programming: ['programming', 'programmation', 'coding', 'code'],
    coding: ['coding', 'programmation', 'programming', 'code'],
    developpement: ['developpement', 'développement', 'development', 'developer'],
    python: ['python', 'django', 'flask', 'fastapi', 'pandas'],
    java: ['java', 'spring', 'spring boot', 'springboot'],
    javascript: ['javascript', 'js', 'node', 'nodejs', 'typescript', 'ts'],
    angular: ['angular', 'angularjs'],
    react: ['react', 'reactjs'],
    // Métiers
    developpeur: ['developpeur', 'développeur', 'developer', 'dev', 'programmeur'],
    ingenieur: ['ingenieur', 'ingénieur', 'engineer'],
    formateur: ['formateur', 'formatrice', 'trainer', 'enseignant', 'coach'],
    coach: ['coach', 'formateur', 'trainer', 'mentor', 'tuteur'],
    manager: ['manager', 'responsable', 'chef', 'lead', 'encadrant'],
    designer: ['designer', 'ux', 'ui', 'graphiste'],
    // Soft skills
    communication: ['communication', 'communicant', 'relationnel'],
    equipe: ['equipe', 'équipe', 'team', 'teamwork', 'travail en équipe', 'collaboration'],
    leadership: ['leadership', 'leader', 'meneur', 'management'],
    autonomie: ['autonomie', 'autonome', 'indépendant'],
    creativite: ['creativite', 'créativité', 'créatif', 'creative'],
    // Niveaux
    junior: ['junior', 'débutant', 'debutant', 'stagiaire'],
    senior: ['senior', 'confirmé', 'confirme', 'expérimenté', 'expert'],
    stage: ['stage', 'stagiaire', 'internship', 'pfe'],
    // Tests / QA
    test: ['test', 'testing', 'qa', 'tests unitaires', 'selenium', 'junit', 'cypress'],
    qa: ['qa', 'quality assurance', 'testeur', 'tests'],
    // Agile / gestion de projet
    agile: ['agile', 'scrum', 'kanban', 'sprint'],
    scrum: ['scrum', 'scrum master', 'agile', 'product owner'],
    gestionprojet: ['gestion de projet', 'project management', 'chef de projet', 'project manager'],
    // Réseaux / systèmes
    reseau: ['reseau', 'réseau', 'network', 'réseaux', 'tcp/ip', 'cisco'],
    systeme: ['systeme', 'système', 'system', 'sysadmin', 'linux', 'windows server'],
    linux: ['linux', 'unix', 'ubuntu', 'debian', 'bash'],
    // ERP / CRM
    erp: ['erp', 'sap', 'odoo', 'sage', 'pgi'],
    crm: ['crm', 'salesforce', 'hubspot', 'relation client'],
    // Data engineering
    etl: ['etl', 'elt', 'talend', 'pipeline de données', 'data engineering'],
    bigdata: ['big data', 'hadoop', 'spark', 'kafka', 'data lake'],
    // IoT / robotique
    iot: ['iot', 'internet des objets', 'objets connectés', 'embarqué'],
    robotique: ['robotique', 'robotics', 'arduino', 'raspberry'],
    // Jeux / 3D
    jeuxvideo: ['jeux vidéo', 'game', 'gaming', 'unity', 'unreal'],
    // Design / outils
    design: ['design', 'ux', 'ui', 'figma', 'adobe xd', 'maquette'],
    git: ['git', 'github', 'gitlab', 'versioning'],
    excel: ['excel', 'tableur', 'vba', 'google sheets'],
    // E-learning (cœur DecliTech)
    elearning: ['elearning', 'e-learning', 'formation en ligne', 'lms', 'moodle'],
    pedagogie: ['pedagogie', 'pédagogie', 'enseignement', 'tutorat', 'animation'],
    scratch: ['scratch', 'blockly', 'programmation enfants', 'code.org'],
  };

  private cvAnalysisService: CVAnalysisService = inject(CVAnalysisService);
  private testService: TestService = inject(TestService);
  private route: ActivatedRoute = inject(ActivatedRoute);
  private sanitizer: DomSanitizer = inject(DomSanitizer);

  private static readonly STOPWORDS = new Set([
    'un','une','des','de','du','le','la','les','qui','que','et','ou','avec','pour','dans',
    'en','est','bon','bonne','trouve','moi','cherche','je','veux','ayant','sur','au','aux',
    'connait','connaît','maitrise','maîtrise','experience','expérience','profil','candidat',
    'candidats','the','and','with','who','good','niveau'
  ]);

  constructor() { }

  get analysis() {
    return this.candidate?.lastAnalysis.analysis;
  }

  get analysisLanguages(): string[] {
    return this.analysis?.languages ?? [];
  }

  get hasAnalysisLanguages(): boolean {
    return this.analysisLanguages.length > 0;
  }

  get analysisCertifications(): string[] {
    return this.analysis?.certifications ?? [];
  }

  get hasAnalysisCertifications(): boolean {
    return this.analysisCertifications.length > 0;
  }

  get analysisProjects(): string[] {
    return this.analysis?.projects ?? [];
  }

  get hasAnalysisProjects(): boolean {
    return this.analysisProjects.length > 0;
  }

  get analysisEducation(): Array<{ degree: string; field: string; institution: string; year: string }> {
    return this.candidate?.lastAnalysis.analysis?.education ?? [];
  }

  get hasAnalysisEducation(): boolean {
    return this.analysisEducation.length > 0;
  }

  get analysisWeightedScores(): Record<string, number> {
    return this.analysis?.weightedScores ?? {};
  }

  /** Poids RÉELLEMENT appliqués par le moteur (adaptatifs selon le poste). */
  get analysisAppliedWeights(): Record<string, number> {
    return (this.analysis as any)?.appliedWeights ?? {};
  }

  /** Vrai si le candidat est hors du périmètre du poste (domaines différents). */
  get isOutOfScope(): boolean {
    return Boolean((this.analysis as any)?.outOfScope);
  }

  get outOfScopeDomain(): string {
    const a: any = this.analysis;
    return a?.requirementExternalDomain || a?.cvExternalDomain || '';
  }

  get criteriaExplanations(): Record<string, { status: string; text: string }> {
    return this.analysis?.criteriaExplanations ?? {};
  }

  /** Critères réellement évalués (selon ce que l'exigence demande). */
  get activeCriteria(): Record<string, boolean> {
    return (this.analysis as any)?.activeCriteria ?? {};
  }

  getComparisonMetrics(): Array<ComparisonMetric & { points: number; percentage: number; level: 'high' | 'medium' | 'low'; explanation: string; inactive: boolean }> {
    const weightedScores = this.analysisWeightedScores;
    const applied = this.analysisAppliedWeights;
    const active = this.activeCriteria;

    return this.comparisonMetrics.map((metric) => {
      // Un critère est "non demandé" si activeCriteria le marque explicitement false.
      const inactive = active[metric.key] === false;
      const points = Number(weightedScores[metric.key] ?? 0);
      // Dénominateur = poids RÉELLEMENT appliqué (adaptatif) si disponible.
      const maxPoints = Number(applied[metric.key] ?? metric.maxPoints) || metric.maxPoints;
      const rawPct = maxPoints > 0 ? (points / maxPoints) * 100 : 0;
      const percentage = Math.max(0, Math.min(100, rawPct)); // borné [0,100]

      let level: 'high' | 'medium' | 'low' = 'low';
      if (percentage >= 75) {
        level = 'high';
      } else if (percentage >= 50) {
        level = 'medium';
      }

      const explanation = inactive
        ? "Critère non demandé dans l'exigence du poste — non pris en compte dans la note."
        : this.buildExplanation(metric.key, points, maxPoints, percentage);
      return { ...metric, maxPoints, points, percentage, level, explanation, inactive };
    });
  }

  /**
   * Explication "pourquoi cette note" (XAI).
   * Priorité à l'explication détaillée du backend ; sinon repli intelligent
   * généré côté frontend (fonctionne pour les candidats déjà analysés).
   */
  private buildExplanation(key: string, points: number, maxPoints: number, percentage: number): string {
    const backend = this.criteriaExplanations[key];
    if (backend && backend.text) {
      return backend.text;
    }

    const a = this.analysis;
    const isZero = points <= 0.01;
    const isLow = percentage < 50;

    switch (key) {
      case 'speciality_match':
        if (isZero) return "Le domaine du CV ne correspond pas à celui attendu pour ce poste.";
        if (isLow) return "Le profil n'est que partiellement aligné avec la spécialité du poste.";
        return "Le profil correspond bien à la spécialité attendue par le poste.";

      case 'technical_skills':
        if (isZero) return "Aucune des compétences techniques attendues n'a été retrouvée dans le CV.";
        if (isLow) return `Une partie seulement des compétences correspond` + (a?.skills?.length ? ` (détectées : ${a.skills.slice(0,4).join(', ')}).` : '.');
        return `Les compétences du CV couvrent bien les besoins du poste` + (a?.skills?.length ? ` (ex : ${a.skills.slice(0,4).join(', ')}).` : '.');

      case 'relevant_experience':
        if (isZero) return "Aucune expérience pertinente n'a été détectée par rapport au poste.";
        if (isLow) return "L'expérience détectée est limitée ou peu alignée avec le poste.";
        return "Le parcours professionnel est pertinent pour le poste.";

      case 'pedagogy_tutoring':
        if (isZero) return "Aucun signal pédagogique (enseignement, formation, tutorat, coaching, animation) n'a été détecté dans le CV. C'est pourquoi ce critère est à 0.";
        if (isLow) return "Quelques signaux pédagogiques détectés, mais limités.";
        return "Bonne capacité pédagogique / d'encadrement détectée dans le CV.";

      case 'soft_skills':
        if (isZero) return "Aucune compétence comportementale (communication, travail en équipe, etc.) n'a été détectée.";
        if (isLow) return `Peu de soft skills détectées` + (a?.softSkills?.length ? ` (${a.softSkills.slice(0,4).join(', ')}).` : '.');
        return `Bonnes compétences comportementales` + (a?.softSkills?.length ? ` : ${a.softSkills.slice(0,4).join(', ')}.` : '.');

      case 'semantic_similarity': {
        const sim = Math.round((a?.semanticSimilarityRatio || 0) * 100);
        if (isLow) return `Faible proximité de sens entre le CV et la fiche de poste (${sim}%).`;
        return `Bonne proximité de sens entre le CV et le poste (${sim}%).`;
      }

      default:
        return isZero ? "Ce critère n'a pas été validé pour ce candidat." : "";
    }
  }

  getStrengths(): Array<string> {
    return this.getComparisonMetrics()
      .filter((metric) => metric.level === 'high')
      .map((metric) => `${metric.label} (${metric.points.toFixed(1)}/${metric.maxPoints})`);
  }

  getWeaknesses(): Array<string> {
    return this.getComparisonMetrics()
      .filter((metric) => metric.level === 'low')
      .map((metric) => `${metric.label} (${metric.points.toFixed(1)}/${metric.maxPoints})`);
  }

  hasComparisonDetails(): boolean {
    const weightedScores = this.analysisWeightedScores;
    return Boolean(weightedScores && Object.keys(weightedScores).length);
  }

  formatMetricValue(points: number, maxPoints: number): string {
    return `${points.toFixed(1)}/${maxPoints}`;
  }

  ngOnInit(): void {
    const candidateId = this.route.snapshot.paramMap.get('id');
    // Récupérer la requête du Talent Search (si on vient de là)
    const q = this.route.snapshot.queryParamMap.get('q');
    if (q && q.trim()) {
      this.searchQueryText = q.trim();
      this.searchKeywords = this.tokenizeQuery(q);
      // Étendre chaque mot-clé avec ses synonymes (IA machine learning, etc.)
      const expanded = new Set<string>();
      for (const kw of this.searchKeywords) {
        (CandidateDetailComponent.SYNONYMS[kw] || [kw]).forEach(t => expanded.add(t));
      }
      this.searchTerms = Array.from(expanded);
      this.hasSearch = this.searchTerms.length > 0;
    }
    if (candidateId) {
      this.loadCandidateDetail(candidateId);
    }
  }

  // ============ SURLIGNAGE DES CRITÈRES RECHERCHÉS ============
  private tokenizeQuery(text: string): string[] {
    const tokens = (text.toLowerCase().match(/[a-zà-ÿ0-9+#.]+/gi) || [])
      .filter(t => t.length >= 2 && !CandidateDetailComponent.STOPWORDS.has(t));
    return Array.from(new Set(tokens));
  }

  private escapeHtml(s: string): string {
    return (s ?? '')
      .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
  }

  private escapeRegex(s: string): string {
    return s.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  }

  /**
   * Renvoie le texte avec les mots-clés (et synonymes) entourés de <mark>.
   * Match par MOTS ENTIERS uniquement (évite "ia" dans "stagiaire").
   */
  highlight(text: string | null | undefined): SafeHtml {
    const safe = this.escapeHtml(String(text ?? ''));
    if (!this.hasSearch || !this.searchTerms.length) {
      return this.sanitizer.bypassSecurityTrustHtml(safe);
    }
    // Trier par longueur décroissante pour matcher les expressions avant les mots
    const pattern = this.searchTerms
      .slice().sort((a, b) => b.length - a.length)
      .map(k => this.escapeRegex(k)).join('|');
    // Frontières de mot compatibles accents (lookbehind/lookahead)
    const re = new RegExp('(?<![\\wÀ-ÿ])(' + pattern + ')(?![\\wÀ-ÿ])', 'gi');
    const html = safe.replace(re, '<mark class="kw-highlight">$1</mark>');
    return this.sanitizer.bypassSecurityTrustHtml(html);
  }

  /** Indique si un texte contient au moins un mot-clé (mot entier) recherché. */
  matchesSearch(text: string | null | undefined): boolean {
    if (!this.hasSearch) return false;
    const low = String(text ?? '').toLowerCase();
    return this.searchTerms.some(k => {
      const re = new RegExp('(?<![\\wÀ-ÿ])' + this.escapeRegex(k) + '(?![\\wÀ-ÿ])', 'i');
      return re.test(low);
    });
  }

  /**
   * Charger les détails du candidat
   */
  private loadCandidateDetail(candidateId: string): void {
    this.cvAnalysisService.getCandidateDetail(candidateId).subscribe({
      next: (candidate) => {
        this.candidate = candidate;
        this.loading = false;
      },
      error: (error) => {
        this.loading = false;
        this.error = 'Erreur lors du chargement des détails du candidat.';
        console.error('Erreur:', error);
      }
    });
  }

  /**
   * Télécharger le rapport
   */
  downloadReport(): void {
    if (this.candidate?.lastAnalysis.id) {
      this.cvAnalysisService.downloadReport(this.candidate.lastAnalysis.id).subscribe({
        next: (blob) => {
          const url = window.URL.createObjectURL(blob);
          const link = document.createElement('a');
          link.href = url;
          link.download = `rapport_${this.candidate?.name}.pdf`;
          link.click();
          window.URL.revokeObjectURL(url);
        },
        error: (error) => {
          console.error('Erreur lors du téléchargement:', error);
        }
      });
    }
  }

  /** Envoie un test technique au candidat (génération IA + e-mail d'invitation). */
  sendTest(): void {
    const id = this.candidate?.lastAnalysis?.id;
    if (!id || this.sendingTest) return;
    this.sendingTest = true;
    this.testMessage = null;
    this.testService.sendTest(id).subscribe({
      next: (res) => {
        this.sendingTest = false;
        this.testOk = true;
        this.testMessage = res?.message || 'Test envoyé au candidat par e-mail.';
        setTimeout(() => this.testMessage = null, 5000);
      },
      error: (e) => {
        this.sendingTest = false;
        this.testOk = false;
        this.testMessage = e?.error?.error || "Échec de l'envoi du test.";
      }
    });
  }
}
