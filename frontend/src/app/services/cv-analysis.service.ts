import { Injectable, inject } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';
import { map } from 'rxjs/operators';
import { environment } from '../../environments/environment';

export interface CVAnalysisRequest {
  fileId: string;
  requirementText?: string;
}

export interface CVAnalysisResponse {
  id: string;
  candidateName: string;
  email: string;
  phone: string;
  scores: {
    educationScore: number;
    experienceScore: number;
    skillsScore: number;
    softSkillsScore: number;
    overallScore: number;
  };
  matchPercentage: number;
  relevanceScore?: number;
  semanticScore?: number;
  recommendations: string[];
  analysis: {
    skills: string[];
    experience: Array<{
      title: string;
      company: string;
      duration: string;
      description: string;
    }>;
    education: Array<{
      degree: string;
      field: string;
      institution: string;
      year: string;
    }>;
    softSkills: string[];
    languages?: string[];
    certifications?: string[];
    projects?: string[];
    summary?: string;
    location?: string;
    specialityCv?: string;
    specialityRequirement?: string;
    decisionLabel?: string;
    recommendationLabel?: string;
    semanticSimilarityRatio?: number;
    weightedScores?: Record<string, number>;
    appliedWeights?: Record<string, number>;
    activeCriteria?: Record<string, boolean>;
    outOfScope?: boolean;
    cvExternalDomain?: string;
    requirementExternalDomain?: string;
    detectedJobProfile?: string;
    criteriaExplanations?: Record<string, { status: string; text: string }>;
    extractedTextPreview?: string;
  };
  timestamp: string;
}

export interface CandidateDetail {
  id: string;
  name: string;
  email: string;
  phone: string;
  cvPath: string;
  analysisHistory: CVAnalysisResponse[];
  lastAnalysis: CVAnalysisResponse;
}

interface RawAnalysisResult {
  id: number | string;
  candidateName?: string;
  email?: string;
  phone?: string;
  cvPath?: string;
  scores?: {
    educationScore?: number;
    experienceScore?: number;
    skillsScore?: number;
    softSkillsScore?: number;
    overallScore?: number;
  };
  analysis?: CVAnalysisResponse['analysis'] | Record<string, unknown> | null;
  analysisData?: string | Record<string, unknown> | null;
  overallScore?: number;
  educationScore?: number;
  experienceScore?: number;
  skillsScore?: number;
  softSkillsScore?: number;
  matchPercentage?: number;
  relevanceScore?: number;
  semanticScore?: number;
  recommendations?: string | string[] | Record<string, unknown> | null;
  createdAt?: string;
  updatedAt?: string;
}

/**
 * ============================================================================
 *  CVAnalysisService — point d'accès unique à l'API d'analyse de CV.
 * ----------------------------------------------------------------------------
 *  Regroupe TOUS les appels HTTP liés aux CV : upload/analyse, liste, détail,
 *  Top 10, statistiques, Talent Search, export PDF/CSV, corbeille.
 *
 *  Concept clé : la NORMALISATION. Les données peuvent arriver sous deux formes
 *  selon l'endpoint (réponse fraîche de FastAPI vs ligne stockée en base où le
 *  détail est un JSON dans "analysisData"). normalizeResponse() les ramène
 *  TOUTES à un format unique (CVAnalysisResponse) -> les composants n'ont alors
 *  qu'un seul format à gérer. RxJS map() applique cette transformation au flux.
 * ============================================================================
 */
@Injectable({
  providedIn: 'root'
})
export class CVAnalysisService {
  private apiUrl = `${environment.apiUrl}/api/cv-analysis`;
  private fastApiUrl = environment.fastApiUrl;
  private http = inject(HttpClient);

  /** Convertit une donnée brute (de l'API ou de la base) vers le format unique
   *  attendu par l'app, en gérant les deux structures possibles + valeurs par défaut. */
  private normalizeResponse(raw: RawAnalysisResult): CVAnalysisResponse {
    const isStructured = Boolean((raw as any)?.scores);
    const structuredScores = (raw as any)?.scores ?? {};
    const analysisData = this.parseAnalysisData({
      ...(typeof raw.analysisData === 'object' && raw.analysisData ? raw.analysisData : {}),
      ...((raw as any)?.analysis && typeof (raw as any).analysis === 'object' ? (raw as any).analysis : {}),
      analysisData: raw.analysisData,
    });
    const recommendations = this.parseRecommendations(raw.recommendations);
    const scoresSource = isStructured ? structuredScores : raw;

    return {
      id: String(raw.id),
      candidateName: raw.candidateName ?? 'Candidat',
      email: raw.email ?? '',
      phone: raw.phone ?? '',
      scores: {
        educationScore: scoresSource.educationScore ?? 0,
        experienceScore: scoresSource.experienceScore ?? 0,
        skillsScore: scoresSource.skillsScore ?? 0,
        softSkillsScore: scoresSource.softSkillsScore ?? 0,
        overallScore: scoresSource.overallScore ?? 0,
      },
      matchPercentage: raw.matchPercentage ?? scoresSource.overallScore ?? 0,
      relevanceScore: raw.relevanceScore,
      semanticScore: raw.semanticScore,
      recommendations,
      analysis: analysisData,
      timestamp: raw.updatedAt ?? raw.createdAt ?? '',
    };
  }

  /** Transforme le détail d'analyse (objet OU chaîne JSON) en structure typée.
   *  Gère les différents noms de champs possibles (ex: skills vs skills_technical)
   *  pour rester robuste quelle que soit la source. */
  private parseAnalysisData(value: RawAnalysisResult['analysisData'] | RawAnalysisResult['analysis']): CVAnalysisResponse['analysis'] {
    const analysis = this.normalizeAnalysisPayload(value);

    const experience = Array.isArray(analysis['experience'])
      ? analysis['experience'].map((exp: Record<string, unknown>) => ({
          title: String(exp['title'] ?? exp['job_title'] ?? ''),
          company: String(exp['company'] ?? ''),
          duration: String(exp['duration'] ?? `${exp['start_date'] ?? ''}${exp['end_date'] ? ' - ' + exp['end_date'] : ''}`),
          description: String(exp['description'] ?? ''),
        }))
      : [];

    const education = Array.isArray(analysis['education'])
      ? analysis['education'].map((edu: Record<string, unknown>) => ({
          degree: String(edu['degree'] ?? ''),
          field: String(edu['field'] ?? ''),
          institution: String(edu['institution'] ?? ''),
          year: String(edu['year'] ?? edu['end_date'] ?? edu['start_date'] ?? ''),
        }))
      : [];

    return {
      skills: this.asStringArray(this.readAnalysisField(analysis, ['skills', 'skills_technical', 'technicalSkills'], [])),
      experience,
      education,
      softSkills: this.asStringArray(this.readAnalysisField(analysis, ['softSkills', 'skills_soft', 'soft_skills'], [])),
      languages: this.asStringArray(this.readAnalysisField(analysis, ['languages'], [])),
      certifications: this.asStringArray(this.readAnalysisField(analysis, ['certifications'], [])),
      projects: this.asStringArray(this.readAnalysisField(analysis, ['projects'], [])),
      summary: String(this.readAnalysisField(analysis, ['summary'], '')),
      location: String(this.readAnalysisField(analysis, ['location'], '')),
      specialityCv: String(this.readAnalysisField(analysis, ['specialityCv', 'speciality_cv'], '')),
      specialityRequirement: String(this.readAnalysisField(analysis, ['specialityRequirement', 'speciality_requirement'], '')),
      decisionLabel: String(this.readAnalysisField(analysis, ['decisionLabel', 'decision_label'], '')),
      recommendationLabel: String(this.readAnalysisField(analysis, ['recommendationLabel', 'recommendation_label'], '')),
      semanticSimilarityRatio: Number(this.readAnalysisField(analysis, ['semanticSimilarityRatio', 'semantic_similarity_ratio'], 0)),
      weightedScores: this.readAnalysisObject(analysis, ['weightedScores', 'weighted_scores']),
      // Champs du scoring dynamique (poids réels, critères actifs, hors-domaine)
      appliedWeights: this.readAnalysisObject(analysis, ['appliedWeights', 'applied_weights']),
      activeCriteria: this.readAnalysisBooleanObject(analysis, ['activeCriteria', 'active_criteria']),
      outOfScope: Boolean(this.readAnalysisField(analysis, ['outOfScope', 'out_of_scope'], false)),
      cvExternalDomain: String(this.readAnalysisField(analysis, ['cvExternalDomain', 'cv_external_domain'], '')),
      requirementExternalDomain: String(this.readAnalysisField(analysis, ['requirementExternalDomain', 'requirement_external_domain'], '')),
      detectedJobProfile: String(this.readAnalysisField(analysis, ['detectedJobProfile', 'detected_job_profile'], '')),
      criteriaExplanations: this.readAnalysisObject(analysis, ['criteriaExplanations', 'criteria_explanations']) as unknown as Record<string, { status: string; text: string }>,
      extractedTextPreview: String(this.readAnalysisField(analysis, ['extractedTextPreview', 'extracted_text_preview'], '')),
    };
  }

  private normalizeAnalysisPayload(value: RawAnalysisResult['analysisData'] | RawAnalysisResult['analysis']): Record<string, any> {
    const fromObject = this.toAnalysisRecord(value);
    const fromAnalysisData = this.toAnalysisRecord((value as Record<string, unknown> | null | undefined)?.['analysisData']);

    return { ...fromAnalysisData, ...fromObject };
  }

  private toAnalysisRecord(value: unknown): Record<string, any> {
    const parsed = typeof value === 'string' ? this.safeJsonParse(value) : value ?? {};
    return parsed && typeof parsed === 'object' ? parsed as Record<string, any> : {};
  }

  private readAnalysisField<T>(analysis: Record<string, any>, keys: string[], fallback: T): T {
    for (const key of keys) {
      const value = analysis[key];
      if (value !== undefined && value !== null) {
        return value as T;
      }
    }
    return fallback;
  }

  private readAnalysisObject(analysis: Record<string, any>, keys: string[]): Record<string, number> {
    const value = this.readAnalysisField<Record<string, unknown>>(analysis, keys, {});
    return value && typeof value === 'object' ? value as Record<string, number> : {};
  }

  private readAnalysisBooleanObject(analysis: Record<string, any>, keys: string[]): Record<string, boolean> {
    const value = this.readAnalysisField<Record<string, unknown>>(analysis, keys, {});
    if (!value || typeof value !== 'object') {
      return {};
    }

    return Object.entries(value).reduce<Record<string, boolean>>((acc, [key, entry]) => {
      acc[key] = Boolean(entry);
      return acc;
    }, {});
  }

  private parseRecommendations(value: RawAnalysisResult['recommendations']): string[] {
    const parsed = typeof value === 'string' ? this.safeJsonParse(value) : value;

    if (Array.isArray(parsed)) {
      return parsed.map((item) => String(item));
    }

    if (parsed && typeof parsed === 'object') {
      return Object.values(parsed).flatMap((entry) =>
        Array.isArray(entry) ? entry.map((item) => String(item)) : [String(entry)]
      );
    }

    return [];
  }

  private asStringArray(value: unknown): string[] {
    if (!Array.isArray(value)) {
      return [];
    }

    return value.map((item) => String(item));
  }

  /** Parse du JSON sans planter : renvoie null si la chaîne est invalide. */
  private safeJsonParse(value: string): unknown {
    try {
      return JSON.parse(value);
    } catch {
      return null;
    }
  }

  /**
   * Uploader et analyser un CV
   */
  uploadAndAnalyzeCV(file: File, requirementText?: string): Observable<CVAnalysisResponse> {
    const formData = new FormData();
    formData.append('file', file);
    if (requirementText) {
      formData.append('requirements', requirementText);
    }

    return this.http.post<RawAnalysisResult>(`${this.apiUrl}/analyze`, formData)
      .pipe(map((response) => this.normalizeResponse(response)));
  }

  /**
   * Obtenir les résultats d'analyse
   */
  getAnalysisResults(): Observable<CVAnalysisResponse[]> {
    return this.http.get<RawAnalysisResult[]>(`${this.apiUrl}/results`).pipe(
      map((results) => results.map((result) => this.normalizeResponse(result)))
    );
  }

  /**
   * Obtenir les détails d'un candidat
   */
  getCandidateDetail(candidateId: string): Observable<CandidateDetail> {
    return this.http.get<RawAnalysisResult>(`${this.apiUrl}/candidates/${candidateId}`).pipe(
      map((result) => {
        const mapped = this.normalizeResponse(result);
        return {
          id: String(result.id),
          name: mapped.candidateName,
          email: mapped.email,
          phone: mapped.phone,
          cvPath: result.cvPath ?? '',
          analysisHistory: [mapped],
          lastAnalysis: mapped,
        };
      })
    );
  }

  /**
   * Appeler le service FastAPI directement pour le scoring
   */
  scoreWithFastAPI(analysisData: any): Observable<any> {
    return this.http.post<any>(
      `${this.fastApiUrl}/score`,
      analysisData
    );
  }

  /**
   * Obtenir le Top-10 candidats par score global
   */
  getTopCandidates() : Observable<CVAnalysisResponse[]> {
    return this.http.get<RawAnalysisResult[]>(`${this.apiUrl}/top`).pipe(
      map((results) => results.map((result) => this.normalizeResponse(result)))
    );
  }

  /**
   * Télécharger un rapport PDF
   */
  downloadReport(analysisId: string): Observable<Blob> {
    return this.http.get(
      `${this.apiUrl}/results/${analysisId}/report`,
      { responseType: 'blob' }
    );
  }

  /**
   * Exporter les résultats en CSV
   */
  exportToCSV(): Observable<Blob> {
    return this.http.get(
      `${this.apiUrl}/results/export/csv`,
      { responseType: 'blob' }
    );
  }

  /**
   * Statistiques globales KPI
   */
  getStatistics(): Observable<any> {
    return this.http.get<any>(`${this.apiUrl}/statistics`);
  }

  /**
   * Talent Search (RAG) — recherche sémantique en langage naturel sur le vivier
   */
  talentSearch(query: string, topK: number = 50): Observable<CVAnalysisResponse[]> {
    return this.http.post<RawAnalysisResult[]>(`${this.apiUrl}/talent-search`, { query, topK }).pipe(
      map((results) => results.map((result) => this.normalizeResponse(result)))
    );
  }

  // ===== Corbeille (soft-delete) =====
  /** Déplacer un candidat vers la corbeille */
  moveToTrash(id: string): Observable<any> {
    return this.http.delete<any>(`${this.apiUrl}/results/${id}`);
  }

  /** Liste de la corbeille (candidats supprimés + jours restants) */
  getTrash(): Observable<any[]> {
    return this.http.get<any[]>(`${this.apiUrl}/trash`);
  }

  /** Restaurer un candidat depuis la corbeille */
  restoreFromTrash(id: string): Observable<any> {
    return this.http.post<any>(`${this.apiUrl}/trash/${id}/restore`, {});
  }

  /** Supprimer définitivement un candidat */
  deletePermanently(id: string): Observable<any> {
    return this.http.delete<any>(`${this.apiUrl}/trash/${id}`);
  }
}
