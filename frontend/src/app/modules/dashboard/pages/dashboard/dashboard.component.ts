import { Component, OnInit, inject } from '@angular/core';
import { CVAnalysisService, CVAnalysisResponse } from '../../../../services/cv-analysis.service';

@Component({
  selector: 'app-dashboard',
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.css']
})
/**
 * ============================================================================
 *  DashboardComponent — tableau de bord (vue synthétique du recruteur).
 * ----------------------------------------------------------------------------
 *  Charge en parallèle : la liste des analyses, le Top 10, et les statistiques.
 *  Affiche des KPI (moyenne, répartition par décision), une liste paginée +
 *  recherche, et permet l'export CSV. Si l'API stats échoue, on recalcule les
 *  statistiques localement (computeStatsLocally) -> robustesse.
 * ============================================================================
 */
export class DashboardComponent implements OnInit {

  analysisResults: CVAnalysisResponse[] = [];
  filteredResults: CVAnalysisResponse[] = [];
  topCandidates: CVAnalysisResponse[] = [];
  loading = true;
  error: string | null = null;
  exportError: string | null = null;

  // Recherche
  searchQuery = '';

  // Pagination
  currentPage = 0;
  pageSize = 8;
  get totalPages(): number {
    return Math.ceil(this.filteredResults.length / this.pageSize);
  }

  // Statistiques depuis l'API
  stats: any = {
    totalCandidates: 0, averageScore: 0, maxScore: 0, minScore: 0,
    averageMatch: 0, countExcellent: 0, countStrong: 0, countModerate: 0, countWeak: 0
  };

  private cvAnalysisService = inject(CVAnalysisService);

  ngOnInit(): void {
    this.loadAll();
  }

  private loadAll(): void {
    this.loading = true;

    // Charger résultats
    this.cvAnalysisService.getAnalysisResults().subscribe({
      next: (results) => {
        this.analysisResults = results;
        this.filteredResults = [...results];
        this.computeStatsLocally();
        this.loading = false;
      },
      error: () => {
        this.loading = false;
        this.error = 'Erreur lors du chargement des résultats.';
      }
    });

    // Charger top 10
    this.cvAnalysisService.getTopCandidates().subscribe({
      next: (results) => { this.topCandidates = results; },
      error: (e) => console.error('Top candidats:', e)
    });

    // Charger stats API si disponible
    this.cvAnalysisService.getStatistics().subscribe({
      next: (s) => { this.stats = s; },
      error: () => { /* fallback sur stats locales */ }
    });
  }

  private computeStatsLocally(): void {
    const total = this.analysisResults.length;
    if (total === 0) return;
    const scores = this.analysisResults.map(r => r.scores?.overallScore || 0);
    this.stats = {
      totalCandidates: total,
      averageScore: Math.round(scores.reduce((a, b) => a + b, 0) / total * 10) / 10,
      maxScore:     Math.max(...scores),
      minScore:     Math.min(...scores),
      averageMatch: Math.round(this.analysisResults.reduce((a, r) => a + (r.matchPercentage || 0), 0) / total * 10) / 10,
      countExcellent: scores.filter(s => s >= 85).length,
      countStrong:    scores.filter(s => s >= 70 && s < 85).length,
      countModerate:  scores.filter(s => s >= 55 && s < 70).length,
      countWeak:      scores.filter(s => s < 55).length
    };
  }

  // ===== RECHERCHE =====
  onSearch(): void {
    const q = this.searchQuery.toLowerCase().trim();
    this.filteredResults = q
      ? this.analysisResults.filter(r =>
          (r.candidateName || '').toLowerCase().includes(q) ||
          (r.email || '').toLowerCase().includes(q))
      : [...this.analysisResults];
    this.currentPage = 0;
  }

  clearSearch(): void {
    this.searchQuery = '';
    this.onSearch();
  }

  // ===== PAGINATION =====
  getPaginatedResults(): CVAnalysisResponse[] {
    const start = this.currentPage * this.pageSize;
    return this.filteredResults.slice(start, start + this.pageSize);
  }

  getPageNumbers(): number[] {
    return Array.from({ length: this.totalPages }, (_, i) => i);
  }

  prevPage(): void { if (this.currentPage > 0) this.currentPage--; }
  nextPage(): void { if (this.currentPage < this.totalPages - 1) this.currentPage++; }
  goToPage(p: number): void { this.currentPage = p; }

  // ===== UTILITAIRES VISUELS =====
  getPercent(count: number): number {
    if (!this.stats.totalCandidates) return 0;
    return Math.round((count / this.stats.totalCandidates) * 100);
  }

  getScoreClass(score: number): string {
    if (score >= 85) return 'score-excellent';
    if (score >= 70) return 'score-strong';
    if (score >= 55) return 'score-moderate';
    return 'score-weak';
  }

  getScoreColor(score: number): string {
    if (score >= 85) return 'linear-gradient(90deg,#22c55e,#16a34a)';
    if (score >= 70) return 'linear-gradient(90deg,#3b82f6,#2563eb)';
    if (score >= 55) return 'linear-gradient(90deg,#f59e0b,#d97706)';
    return 'linear-gradient(90deg,#ef4444,#dc2626)';
  }

  getDecisionLabel(score: number): string {
    if (score >= 85) return 'Excellent';
    if (score >= 70) return 'Fort';
    if (score >= 55) return 'Modéré';
    return 'Faible';
  }

  getDecisionBadge(score: number): string {
    if (score >= 85) return 'badge badge-excellent';
    if (score >= 70) return 'badge badge-strong';
    if (score >= 55) return 'badge badge-moderate';
    return 'badge badge-weak';
  }

  // ===== EXPORT CSV =====
  // Le backend renvoie un fichier binaire (Blob). On crée une URL temporaire en
  // mémoire et on simule un clic sur un lien pour déclencher le téléchargement.
  exportToCSV(): void {
    this.exportError = null;
    this.cvAnalysisService.exportToCSV().subscribe({
      next: (blob) => {
        const url = window.URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = 'skillmatch_resultats.csv';
        link.click();
        window.URL.revokeObjectURL(url);   // libère la mémoire
      },
      error: (err) => {
        this.exportError = err?.error?.error || err?.error?.message || 'Impossible d’exporter le CSV.';
        console.error('Erreur export CSV', err);
      }
    });
  }
}
