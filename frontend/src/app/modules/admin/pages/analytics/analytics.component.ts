import { Component, OnInit, AfterViewInit, OnDestroy, ViewChild, ElementRef, inject } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Router } from '@angular/router';
import { environment } from '../../../../../environments/environment';
import { Chart, registerables } from 'chart.js';

Chart.register(...registerables);

interface RecruiterStat {
  recruiterId: number;
  recruiterName: string;
  recruiterEmail: string;
  role: string;
  totalAnalyses: number;
  avgScore: number;
  countExcellent: number;
  countStrong: number;
  countModerate: number;
  countWeak: number;
  lastActivity: string;
}

interface CandidateRow {
  id: number;
  candidateName: string;
  email: string;
  overallScore: number;
  matchPercentage: number;
  decision: string;
  recruiterId: number;
  recruiterName: string;
  recruiterEmail: string;
  createdAt: string;
  createdAtIso: string;
}

/**
 * ============================================================================
 *  AnalyticsComponent — tableau de bord ANALYTICS (réservé à l'admin RH).
 * ----------------------------------------------------------------------------
 *  Affiche l'activité de recrutement : KPI globaux, performance par recruteur,
 *  graphiques Chart.js (barres = candidats/recruteur, courbe = analyses dans le
 *  temps avec granularité jour/semaine/mois), et un tableau filtrable.
 *
 *  Cycle de vie Angular utilisé :
 *   - ngOnInit        : charge les données depuis l'API ;
 *   - ngAfterViewInit : le <canvas> existe enfin -> on peut dessiner les charts ;
 *   - ngOnDestroy     : on détruit les charts pour éviter les fuites mémoire.
 * ============================================================================
 */
@Component({
  selector: 'app-analytics',
  templateUrl: './analytics.component.html',
  styleUrls: ['./analytics.component.css']
})
export class AnalyticsComponent implements OnInit, AfterViewInit, OnDestroy {
  loading = true;
  error: string | null = null;

  @ViewChild('barCanvas') barCanvas?: ElementRef<HTMLCanvasElement>;
  @ViewChild('lineCanvas') lineCanvas?: ElementRef<HTMLCanvasElement>;
  private barChart?: Chart;
  private lineChart?: Chart;
  private viewReady = false;

  // Granularité de la courbe temporelle
  timeGranularity: 'day' | 'week' | 'month' = 'day';

  totalRecruiters = 0;
  totalAnalyses = 0;
  averageScore = 0;
  recruiters: RecruiterStat[] = [];

  candidates: CandidateRow[] = [];
  filtered: CandidateRow[] = [];

  // Filtres
  search = '';
  filterRecruiter: number | 'all' = 'all';
  filterDecision: 'all' | 'Excellent' | 'Fort' | 'Modéré' | 'Faible' = 'all';

  // Pagination
  currentPage = 0;
  pageSize = 10;

  private http = inject(HttpClient);
  private router = inject(Router);
  private apiUrl = `${environment.apiUrl}/api`;

  ngOnInit(): void { this.loadAll(); }

  ngAfterViewInit(): void { this.viewReady = true; this.renderCharts(); }

  ngOnDestroy(): void {
    this.barChart?.destroy();
    this.lineChart?.destroy();
  }

  private authHeaders(): HttpHeaders {
    const token = localStorage.getItem('access_token');
    return new HttpHeaders({ Authorization: `Bearer ${token}` });
  }

  loadAll(): void {
    this.loading = true;
    this.error = null;
    const headers = this.authHeaders();

    this.http.get<any>(`${this.apiUrl}/admin/analytics/overview`, { headers }).subscribe({
      next: (data) => {
        this.totalRecruiters = data.totalRecruiters || 0;
        this.totalAnalyses = data.totalAnalyses || 0;
        this.averageScore = data.averageScore || 0;
        this.recruiters = data.recruiters || [];
        this.loadCandidates();
      },
      error: () => { this.error = 'Impossible de charger les statistiques.'; this.loading = false; }
    });
  }

  loadCandidates(): void {
    this.http.get<CandidateRow[]>(`${this.apiUrl}/admin/analytics/candidates`, { headers: this.authHeaders() }).subscribe({
      next: (data) => {
        this.candidates = data || [];
        this.applyFilters();
        this.loading = false;
        // Rendre les graphiques après que le DOM (canvas) soit prêt
        setTimeout(() => this.renderCharts(), 0);
      },
      error: () => { this.error = 'Impossible de charger les candidats.'; this.loading = false; }
    });
  }

  // ===================== GRAPHIQUES =====================
  private renderCharts(): void {
    if (!this.viewReady) return;
    this.renderBarChart();
    this.renderLineChart();
  }

  /** Bar chart : nombre de candidats analysés par recruteur. */
  private renderBarChart(): void {
    if (!this.barCanvas) return;
    const labels = this.recruiters.map(r => r.recruiterName);
    const data = this.recruiters.map(r => r.totalAnalyses);
    this.barChart?.destroy();
    this.barChart = new Chart(this.barCanvas.nativeElement, {
      type: 'bar',
      data: {
        labels,
        datasets: [{
          label: 'Candidats analysés',
          data,
          backgroundColor: '#2563eb',
          borderRadius: 6,
          maxBarThickness: 48,
        }]
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false }, tooltip: { enabled: true } },
        scales: { y: { beginAtZero: true, ticks: { precision: 0 } } }
      }
    });
  }

  /** Line chart : analyses par recruteur dans le temps (jour/semaine/mois). */
  private renderLineChart(): void {
    if (!this.lineCanvas) return;
    const { labels, datasets } = this.buildTimeSeries(this.timeGranularity);
    this.lineChart?.destroy();
    this.lineChart = new Chart(this.lineCanvas.nativeElement, {
      type: 'line',
      data: { labels, datasets },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        interaction: { mode: 'index', intersect: false },
        plugins: { legend: { position: 'bottom' } },
        scales: { y: { beginAtZero: true, ticks: { precision: 0 } } }
      }
    });
  }

  changeGranularity(g: 'day' | 'week' | 'month'): void {
    this.timeGranularity = g;
    this.renderLineChart();
  }

  /** Construit les séries temporelles : 1 ligne par recruteur. */
  private buildTimeSeries(granularity: 'day' | 'week' | 'month') {
    // Clé de période à partir d'une date ISO
    const periodKey = (iso: string): string => {
      const d = new Date(iso);
      if (isNaN(d.getTime())) return '';
      const y = d.getFullYear();
      const m = (d.getMonth() + 1).toString().padStart(2, '0');
      const day = d.getDate().toString().padStart(2, '0');
      if (granularity === 'month') return `${y}-${m}`;
      if (granularity === 'week') {
        const onejan = new Date(y, 0, 1);
        const week = Math.ceil((((d.getTime() - onejan.getTime()) / 86400000) + onejan.getDay() + 1) / 7);
        return `${y}-S${week.toString().padStart(2, '0')}`;
      }
      return `${y}-${m}-${day}`;
    };

    // Toutes les périodes présentes (triées)
    const periodSet = new Set<string>();
    this.candidates.forEach(c => { const k = periodKey(c.createdAtIso); if (k) periodSet.add(k); });
    const labels = Array.from(periodSet).sort();

    const palette = ['#2563eb', '#16a34a', '#d97706', '#dc2626', '#7c3aed', '#0891b2', '#db2777', '#65a30d'];

    const datasets = this.recruiters.map((r, idx) => {
      const counts = labels.map(lbl =>
        this.candidates.filter(c => c.recruiterId === r.recruiterId && periodKey(c.createdAtIso) === lbl).length
      );
      const color = palette[idx % palette.length];
      return {
        label: r.recruiterName,
        data: counts,
        borderColor: color,
        backgroundColor: color + '33',
        tension: 0.3,
        fill: false,
        pointRadius: 3,
      };
    });

    return { labels, datasets };
  }

  applyFilters(): void {
    let res = [...this.candidates];
    if (this.filterRecruiter !== 'all') {
      res = res.filter(c => c.recruiterId === this.filterRecruiter);
    }
    if (this.filterDecision !== 'all') {
      res = res.filter(c => c.decision === this.filterDecision);
    }
    const q = this.search.toLowerCase().trim();
    if (q) {
      res = res.filter(c =>
        (c.candidateName || '').toLowerCase().includes(q) ||
        (c.email || '').toLowerCase().includes(q) ||
        (c.recruiterName || '').toLowerCase().includes(q));
    }
    this.filtered = res;
    this.currentPage = 0;
  }

  resetFilters(): void {
    this.search = '';
    this.filterRecruiter = 'all';
    this.filterDecision = 'all';
    this.applyFilters();
  }

  // Pagination
  get totalPages(): number { return Math.ceil(this.filtered.length / this.pageSize); }
  get paged(): CandidateRow[] {
    const start = this.currentPage * this.pageSize;
    return this.filtered.slice(start, start + this.pageSize);
  }
  pageNumbers(): number[] { return Array.from({ length: this.totalPages }, (_, i) => i); }
  prevPage(): void { if (this.currentPage > 0) this.currentPage--; }
  nextPage(): void { if (this.currentPage < this.totalPages - 1) this.currentPage++; }
  goToPage(p: number): void { this.currentPage = p; }

  filterByRecruiter(id: number): void {
    this.filterRecruiter = id;
    this.applyFilters();
    // scroll vers le tableau
    document.getElementById('candidates-table')?.scrollIntoView({ behavior: 'smooth' });
  }

  viewCandidate(id: number): void { this.router.navigate(['/candidates', id]); }

  getScoreClass(score: number): string {
    if (score >= 85) return 'score-excellent';
    if (score >= 70) return 'score-strong';
    if (score >= 55) return 'score-moderate';
    return 'score-weak';
  }
  getDecisionClass(decision: string): string {
    switch (decision) {
      case 'Excellent': return 'score-excellent';
      case 'Fort': return 'score-strong';
      case 'Modéré': return 'score-moderate';
      default: return 'score-weak';
    }
  }
  initial(name: string): string { return (name?.charAt(0) || '?').toUpperCase(); }
}
