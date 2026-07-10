import { Component, OnInit, inject } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { TestService } from '../../../../services/test.service';
import { IconComponent } from '../../../../shared/icon/icon.component';

/**
 * ============================================================================
 *  TestsDashboardComponent — tableau de bord des tests techniques (recruteur).
 * ----------------------------------------------------------------------------
 *  Liste tous les tests envoyés avec leur statut (envoyé / passé / expiré) et
 *  le score obtenu. Permet de filtrer par statut.
 * ============================================================================
 */
@Component({
  selector: 'app-tests-dashboard',
  standalone: true,
  imports: [CommonModule, FormsModule, IconComponent],
  templateUrl: './tests-dashboard.component.html',
  styleUrls: ['./tests-dashboard.component.css']
})
export class TestsDashboardComponent implements OnInit {
  private testService = inject(TestService);

  tests: any[] = [];
  filtered: any[] = [];
  loading = true;
  error: string | null = null;
  filter: 'ALL' | 'PENDING' | 'COMPLETED' | 'EXPIRED' = 'ALL';

  ngOnInit(): void { this.load(); }

  load(): void {
    this.loading = true;
    this.testService.listTests().subscribe({
      next: (data) => { this.tests = data || []; this.applyFilter(); this.loading = false; },
      error: () => { this.error = 'Impossible de charger les tests.'; this.loading = false; }
    });
  }

  applyFilter(): void {
    this.filtered = this.filter === 'ALL'
      ? this.tests
      : this.tests.filter(t => t.status === this.filter);
  }

  setFilter(f: 'ALL' | 'PENDING' | 'COMPLETED' | 'EXPIRED'): void {
    this.filter = f; this.applyFilter();
  }

  countBy(status: string): number {
    return this.tests.filter(t => t.status === status).length;
  }

  statusLabel(s: string): string {
    return s === 'PENDING' ? 'En attente' : s === 'COMPLETED' ? 'Passé' : s === 'EXPIRED' ? 'Expiré' : s;
  }
  statusClass(s: string): string {
    return s === 'COMPLETED' ? 'st-done' : s === 'EXPIRED' ? 'st-expired' : 'st-pending';
  }
  scoreClass(score: number): string {
    if (score >= 60) return 'sc-ok';
    return 'sc-ko';
  }
  initial(name: string): string { return (name?.charAt(0) || '?').toUpperCase(); }
}
