import { Component, OnInit, AfterViewInit, OnDestroy, ViewChild, ElementRef, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Router } from '@angular/router';
import { Chart, registerables } from 'chart.js';
import { TestService } from '../../../../services/test.service';
import { IconComponent } from '../../../../shared/icon/icon.component';

Chart.register(...registerables);

/** Une ligne de test telle que renvoyée par GET /api/tests (listTests). */
interface TestRow {
  id: number;
  analysisResultId: number | null;   // ID du candidat (pour ouvrir sa fiche)
  candidateName: string;
  candidateEmail: string;
  jobTitle: string;
  status: string;                 // PENDING | COMPLETED | EXPIRED
  scorePercent: number | null;
  correctCount: number | null;
  totalQuestions: number | null;
  passed: boolean | null;
  recruiterName: string;
  sentAt: string;
  completedAt: string;
}

/** Recommandation de décision déduite du score du test. */
type RankReco = 'convoquer' | 'revoir' | 'ecarte';

/** Ligne de classement enrichie (recommandation + benchmark par poste). */
interface RankRow extends TestRow {
  reco: RankReco;      // à convoquer / à revoir / écarté
  deltaJob: number;    // écart (points) vs la moyenne du même poste
  topPercent: number;  // positionnement : "Top X%" parmi les candidats testés
}

/**
 * ============================================================================
 *  TestAnalyticsComponent — « Dashboard Test » (recruteur).
 * ----------------------------------------------------------------------------
 *  Tableau de bord BI des TESTS techniques uniquement (n'utilise PAS le score
 *  du modèle d'analyse de CV). Toutes les mesures sont calculées côté client à
 *  partir de la liste renvoyée par /api/tests — aucune modification backend.
 *
 *  Objectif : donner au recruteur assez d'informations pour distinguer les bons
 *  profils (note moyenne, taux de réussite, distribution, classement).
 * ============================================================================
 */
@Component({
  selector: 'app-test-analytics',
  standalone: true,
  imports: [CommonModule, FormsModule, IconComponent],
  templateUrl: './test-analytics.component.html',
  styleUrls: ['./test-analytics.component.css']
})
export class TestAnalyticsComponent implements OnInit, AfterViewInit, OnDestroy {
  private testService = inject(TestService);
  private router = inject(Router);

  all: TestRow[] = [];        // dataset complet
  tests: TestRow[] = [];      // dataset après filtres
  loading = true;
  error: string | null = null;

  // ===== Filtres =====
  filterRecruiter = 'all';
  filterJob = 'all';
  recruiters: string[] = [];
  jobs: string[] = [];

  // ===== KPI =====
  total = 0; completed = 0; pending = 0; expired = 0;
  completionRate = 0; avgScore = 0; passRate = 0; bestScore = 0;

  // ===== Classement des candidats testés (enrichi) =====
  ranking: RankRow[] = [];        // top 10 pour l'affichage
  allRanked: RankRow[] = [];      // tous les candidats testés (pour les segments)

  // ===== Segments de décision =====
  segConvoquer = 0; segRevoir = 0; segEcarte = 0;
  activeSegment: RankReco | null = null;   // segment ouvert dans le modal

  @ViewChild('statusCanvas') statusCanvas?: ElementRef<HTMLCanvasElement>;
  @ViewChild('distCanvas') distCanvas?: ElementRef<HTMLCanvasElement>;
  @ViewChild('jobCanvas') jobCanvas?: ElementRef<HTMLCanvasElement>;
  private statusChart?: Chart;
  private distChart?: Chart;
  private jobChart?: Chart;
  private viewReady = false;

  ngOnInit(): void { this.load(); }
  ngAfterViewInit(): void { this.viewReady = true; this.renderCharts(); }
  ngOnDestroy(): void {
    this.statusChart?.destroy();
    this.distChart?.destroy();
    this.jobChart?.destroy();
  }

  load(): void {
    this.loading = true;
    this.error = null;
    this.testService.listTests().subscribe({
      next: (data) => {
        this.all = (data || []) as TestRow[];
        this.recruiters = Array.from(new Set(this.all.map(t => t.recruiterName).filter(Boolean))).sort();
        this.jobs = Array.from(new Set(this.all.map(t => t.jobTitle).filter(Boolean))).sort();
        this.applyFilters();
        this.loading = false;
      },
      error: () => { this.error = 'Impossible de charger les tests.'; this.loading = false; }
    });
  }

  applyFilters(): void {
    let res = [...this.all];
    if (this.filterRecruiter !== 'all') res = res.filter(t => t.recruiterName === this.filterRecruiter);
    if (this.filterJob !== 'all') res = res.filter(t => t.jobTitle === this.filterJob);
    this.tests = res;
    this.computeKpis();
    // Laisser Angular créer les <canvas> avant de (re)dessiner.
    setTimeout(() => this.renderCharts(), 0);
  }

  resetFilters(): void {
    this.filterRecruiter = 'all';
    this.filterJob = 'all';
    this.applyFilters();
  }

  /** Tests réellement passés et notés (base des mesures de performance). */
  private completedTests(): TestRow[] {
    return this.tests.filter(t => t.status === 'COMPLETED' && t.scorePercent != null);
  }

  private computeKpis(): void {
    this.total = this.tests.length;
    this.completed = this.tests.filter(t => t.status === 'COMPLETED').length;
    this.pending = this.tests.filter(t => t.status === 'PENDING').length;
    this.expired = this.tests.filter(t => t.status === 'EXPIRED').length;
    this.completionRate = this.total ? Math.round(this.completed / this.total * 100) : 0;

    const done = this.completedTests();
    const scores = done.map(t => t.scorePercent as number);
    this.avgScore = scores.length ? Math.round(scores.reduce((a, b) => a + b, 0) / scores.length) : 0;
    this.passRate = done.length ? Math.round(done.filter(t => t.passed).length / done.length * 100) : 0;
    this.bestScore = scores.length ? Math.max(...scores) : 0;

    // Segments de décision (parmi les candidats ayant réellement passé le test).
    this.segConvoquer = done.filter(t => (t.scorePercent as number) >= 75).length;
    this.segRevoir = done.filter(t => { const s = t.scorePercent as number; return s >= 60 && s < 75; }).length;
    this.segEcarte = done.filter(t => (t.scorePercent as number) < 60).length;

    // Moyenne de score PAR POSTE (référence pour le benchmark de chaque candidat).
    const jobGroups = new Map<string, number[]>();
    done.forEach(t => {
      const k = t.jobTitle || '—';
      if (!jobGroups.has(k)) jobGroups.set(k, []);
      jobGroups.get(k)!.push(t.scorePercent as number);
    });
    const jobAvg = new Map<string, number>();
    jobGroups.forEach((arr, k) => jobAvg.set(k, arr.reduce((a, b) => a + b, 0) / arr.length));

    // Classement enrichi : recommandation + écart au poste + positionnement (Top X%).
    const sorted = [...done].sort((a, b) => (b.scorePercent as number) - (a.scorePercent as number));
    const totalDone = sorted.length;
    this.allRanked = sorted.map((t, i) => {
      const s = t.scorePercent as number;
      const reco: RankReco = s >= 75 ? 'convoquer' : s >= 60 ? 'revoir' : 'ecarte';
      const avg = jobAvg.get(t.jobTitle || '—') ?? s;
      const topPercent = totalDone ? Math.max(1, Math.round((i + 1) / totalDone * 100)) : 0;
      return { ...t, reco, deltaJob: Math.round(s - avg), topPercent };
    });
    this.ranking = this.allRanked.slice(0, 10);
  }

  // ===================== MODAL DÉTAILS D'UN SEGMENT =====================
  /** Candidats du segment actuellement ouvert. */
  get segmentList(): RankRow[] {
    return this.activeSegment ? this.allRanked.filter(r => r.reco === this.activeSegment) : [];
  }
  segmentTitle(): string { return this.activeSegment ? this.recoLabel(this.activeSegment) : ''; }
  openSegment(r: RankReco): void { this.activeSegment = r; }
  closeSegment(): void { this.activeSegment = null; }

  /** Ouvre la fiche complète du candidat (page /candidates/:id). */
  viewFiche(r: RankRow): void {
    if (r.analysisResultId != null) {
      this.router.navigate(['/candidates', r.analysisResultId]);
    }
  }

  // ===================== GRAPHIQUES (Chart.js) =====================
  private renderCharts(): void {
    if (!this.viewReady) return;
    this.renderStatusChart();
    this.renderDistChart();
    this.renderJobChart();
  }

  /** Doughnut : répartition des tests par statut. */
  private renderStatusChart(): void {
    if (!this.statusCanvas) return;
    this.statusChart?.destroy();
    this.statusChart = new Chart(this.statusCanvas.nativeElement, {
      type: 'doughnut',
      data: {
        labels: ['Passés', 'En attente', 'Expirés'],
        datasets: [{
          data: [this.completed, this.pending, this.expired],
          backgroundColor: ['#16a34a', '#d97706', '#dc2626'],
          borderWidth: 0
        }]
      },
      options: {
        responsive: true, maintainAspectRatio: false, cutout: '62%',
        plugins: { legend: { position: 'bottom' } }
      }
    });
  }

  /** Histogramme : distribution des notes par tranche de 20 points. */
  private renderDistChart(): void {
    if (!this.distCanvas) return;
    const buckets = [0, 0, 0, 0, 0]; // 0-20, 20-40, 40-60, 60-80, 80-100
    this.completedTests().forEach(t => {
      const s = t.scorePercent as number;
      buckets[Math.min(4, Math.floor(s / 20))]++;
    });
    this.distChart?.destroy();
    this.distChart = new Chart(this.distCanvas.nativeElement, {
      type: 'bar',
      data: {
        labels: ['0-20', '20-40', '40-60', '60-80', '80-100'],
        datasets: [{
          label: 'Candidats',
          data: buckets,
          backgroundColor: '#2563eb',
          borderRadius: 6, maxBarThickness: 48
        }]
      },
      options: {
        responsive: true, maintainAspectRatio: false,
        plugins: { legend: { display: false }, tooltip: { enabled: true } },
        scales: { y: { beginAtZero: true, ticks: { precision: 0 } } }
      }
    });
  }

  /** Barres horizontales : note moyenne par poste (distinguer les profils). */
  private renderJobChart(): void {
    if (!this.jobCanvas) return;
    const map = new Map<string, number[]>();
    this.completedTests().forEach(t => {
      const key = t.jobTitle || '—';
      if (!map.has(key)) map.set(key, []);
      map.get(key)!.push(t.scorePercent as number);
    });
    const labels = Array.from(map.keys());
    const data = labels.map(k => {
      const arr = map.get(k)!;
      return Math.round(arr.reduce((a, b) => a + b, 0) / arr.length);
    });
    this.jobChart?.destroy();
    this.jobChart = new Chart(this.jobCanvas.nativeElement, {
      type: 'bar',
      data: {
        labels,
        datasets: [{ label: 'Note moyenne (%)', data, backgroundColor: '#2563eb', borderRadius: 6, maxBarThickness: 48 }]
      },
      options: {
        indexAxis: 'y', responsive: true, maintainAspectRatio: false,
        plugins: { legend: { display: false } },
        scales: { x: { beginAtZero: true, max: 100 } }
      }
    });
  }

  scoreClass(score: number | null): string {
    if (score == null) return '';
    return score >= 60 ? 'sc-ok' : 'sc-ko';
  }
  initial(name: string): string { return (name?.charAt(0) || '?').toUpperCase(); }

  recoLabel(r: RankReco): string {
    return r === 'convoquer' ? 'À convoquer' : r === 'revoir' ? 'À revoir' : 'Écarté';
  }
  recoClass(r: RankReco): string {
    return r === 'convoquer' ? 'b-conv' : r === 'revoir' ? 'b-rev' : 'b-eca';
  }
  deltaClass(d: number): string { return d >= 0 ? 'd-pos' : 'd-neg'; }
  deltaLabel(d: number): string { return (d > 0 ? '+' : '') + d; }

  private statusFr(s: string): string {
    return s === 'PENDING' ? 'En attente' : s === 'COMPLETED' ? 'Passé' : s === 'EXPIRED' ? 'Expiré' : s;
  }

  /** Export CSV du tableau des tests filtrés (séparateur ';' + BOM pour Excel FR). */
  exportCsv(): void {
    const sep = ';';
    const esc = (v: any): string => {
      const s = (v ?? '').toString().replace(/"/g, '""');
      return /[";\n]/.test(s) ? `"${s}"` : s;
    };
    const headers = ['Candidat', 'Email', 'Poste', 'Statut', 'Score (%)', 'Bonnes réponses', 'Résultat', 'Recruteur', 'Envoyé le', 'Passé le'];
    const rows = this.tests.map(t => [
      t.candidateName,
      t.candidateEmail,
      t.jobTitle,
      this.statusFr(t.status),
      t.scorePercent != null ? t.scorePercent : '',
      (t.correctCount != null && t.totalQuestions != null) ? `${t.correctCount}/${t.totalQuestions}` : '',
      t.status === 'COMPLETED' ? (t.passed ? 'Réussi' : 'Échoué') : '',
      t.recruiterName,
      t.sentAt,
      t.completedAt
    ].map(esc).join(sep));

    const bom = String.fromCharCode(0xFEFF);
    const csv = bom + [headers.join(sep), ...rows].join('\r\n');
    const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `dashboard-tests-${new Date().toISOString().slice(0, 10)}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  }

  /** Export PDF via l'impression du navigateur (capture aussi les graphiques). */
  exportPdf(): void {
    window.print();
  }
}
