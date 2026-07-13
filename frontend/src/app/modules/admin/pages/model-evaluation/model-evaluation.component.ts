import { Component, OnInit, inject } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { environment } from '../../../../../environments/environment';

/**
 * ============================================================================
 *  ModelEvaluationComponent — « Évaluation du modèle » (réservé à l'admin RH).
 * ----------------------------------------------------------------------------
 *  Affiche les métriques scientifiques du moteur de scoring, calculées par le
 *  microservice IA sur un jeu de test annoté : précision, rappel, F1,
 *  exactitude, matrices de confusion et détail par cas. Données récupérées via
 *  le backend Spring (endpoint protégé hasRole('ADMIN_RH')).
 * ============================================================================
 */
@Component({
  selector: 'app-model-evaluation',
  templateUrl: './model-evaluation.component.html',
  styleUrls: ['./model-evaluation.component.css']
})
export class ModelEvaluationComponent implements OnInit {
  loading = true;
  error: string | null = null;

  rows: any[] = [];
  relevance: any = null;
  domain: any = null;
  stats: any = null;

  private http = inject(HttpClient);
  private apiUrl = `${environment.apiUrl}/api`;

  ngOnInit(): void { this.load(); }

  private authHeaders(): HttpHeaders {
    const token = localStorage.getItem('access_token');
    return new HttpHeaders({ Authorization: `Bearer ${token}` });
  }

  load(): void {
    this.loading = true;
    this.error = null;
    this.http.get<any>(`${this.apiUrl}/admin/model-evaluation`, { headers: this.authHeaders() }).subscribe({
      next: (d) => {
        this.rows = d?.rows || [];
        this.relevance = d?.relevance || null;
        this.domain = d?.domain || null;
        this.stats = d?.stats || null;
        this.loading = false;
      },
      error: () => {
        this.error = "Impossible de charger l'évaluation. Vérifie que le microservice IA (FastAPI) est démarré.";
        this.loading = false;
      }
    });
  }

  /** Formatte un ratio 0..1 en pourcentage. */
  pct(x: number): string { return (100 * (x || 0)).toFixed(1) + '%'; }

  scoreClass(score: number): string { return score >= 55 ? 'sc-ok' : 'sc-ko'; }
}
