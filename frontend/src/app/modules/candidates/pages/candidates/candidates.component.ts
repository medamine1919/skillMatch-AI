import { Component, OnInit, inject } from '@angular/core';
import { Router } from '@angular/router';
import { CVAnalysisService, CVAnalysisResponse } from '../../../../services/cv-analysis.service';

@Component({
  selector: 'app-candidates',
  templateUrl: './candidates.component.html',
  styleUrls: ['./candidates.component.css']
})
/**
 * ============================================================================
 *  CandidatesComponent — page "Candidats" (la plus riche de l'app).
 * ----------------------------------------------------------------------------
 *  Trois modes coexistent, pilotés par des booléens :
 *   - mode NORMAL    : liste des candidats + recherche texte + filtre par décision ;
 *   - mode TALENT (RAG) : résultats classés par pertinence sémantique (talentMode) ;
 *   - mode CORBEILLE : candidats supprimés, restaurables (trashMode).
 *  On garde 2 listes : `candidates` (toutes) et `filteredCandidates` (affichée),
 *  pour filtrer sans perdre les données d'origine.
 * ============================================================================
 */
export class CandidatesComponent implements OnInit {

  candidates: CVAnalysisResponse[] = [];          // liste complète chargée du serveur
  filteredCandidates: CVAnalysisResponse[] = [];  // liste réellement affichée (après filtres)
  loading = true;
  error = '';
  searchQuery = '';
  filterDecision: 'all' | 'excellent' | 'strong' | 'moderate' | 'weak' = 'all';

  // ===== Talent Search (RAG) =====
  talentQuery = '';
  talentMode = false;          // true => on affiche les résultats classés par pertinence
  talentLoading = false;
  talentError = '';
  talentResults: CVAnalysisResponse[] = [];
  readonly talentExamples = [
    'coach robotique qui maîtrise Arduino et bon avec les enfants',
    'développeur full stack Angular et Spring Boot',
    'profil data / IA avec Python et machine learning',
    'animateur pédagogue patient pour ateliers Scratch',
  ];

  // ===== Corbeille =====
  trashMode = false;
  trashItems: any[] = [];
  trashLoading = false;
  toast: { message: string; type: 'success' | 'error' } | null = null;

  private router = inject(Router);
  private cvService = inject(CVAnalysisService);

  ngOnInit(): void {
    this.loadCandidates();
  }

  // ============ CORBEILLE ============
  showToast(message: string, type: 'success' | 'error'): void {
    this.toast = { message, type };
    setTimeout(() => this.toast = null, 3500);
  }

  deleteCandidate(c: CVAnalysisResponse, event: Event): void {
    event.stopPropagation();  // ne pas naviguer vers le détail
    if (!c.id) return;
    if (!confirm(`Mettre "${c.candidateName}" à la corbeille ? (suppression définitive après 30 jours)`)) return;
    this.cvService.moveToTrash(c.id).subscribe({
      next: () => {
        this.candidates = this.candidates.filter(x => x.id !== c.id);
        this.applyFilters();
        this.showToast(`"${c.candidateName}" déplacé vers la corbeille.`, 'success');
      },
      error: (e) => this.showToast(e?.error?.error || 'Erreur lors de la suppression.', 'error')
    });
  }

  openTrash(): void {
    this.trashMode = true;
    this.trashLoading = true;
    this.cvService.getTrash().subscribe({
      next: (items) => { this.trashItems = items || []; this.trashLoading = false; },
      error: () => { this.trashLoading = false; this.showToast('Erreur chargement corbeille.', 'error'); }
    });
  }

  closeTrash(): void { this.trashMode = false; }

  restoreCandidate(item: any): void {
    this.cvService.restoreFromTrash(String(item.id)).subscribe({
      next: () => {
        this.trashItems = this.trashItems.filter(x => x.id !== item.id);
        this.showToast(`"${item.candidateName}" restauré.`, 'success');
        this.loadCandidates(); // recharger la liste active
      },
      error: (e) => this.showToast(e?.error?.error || 'Erreur restauration.', 'error')
    });
  }

  purgeCandidate(item: any): void {
    if (!confirm(`Supprimer DÉFINITIVEMENT "${item.candidateName}" ? Cette action est irréversible.`)) return;
    this.cvService.deletePermanently(String(item.id)).subscribe({
      next: () => {
        this.trashItems = this.trashItems.filter(x => x.id !== item.id);
        this.showToast(`"${item.candidateName}" supprimé définitivement.`, 'success');
      },
      error: (e) => this.showToast(e?.error?.error || 'Erreur suppression.', 'error')
    });
  }

  // ===== Talent Search (RAG) =====
  runTalentSearch(): void {
    const q = this.talentQuery.trim();
    if (!q) return;
    this.talentLoading = true;
    this.talentError = '';
    this.talentMode = true;
    this.cvService.talentSearch(q, 50).subscribe({
      next: (results) => {
        this.talentResults = results;
        this.talentLoading = false;
      },
      error: (err) => {
        this.talentError = err?.error?.error || 'Erreur lors de la recherche sémantique.';
        this.talentLoading = false;
        console.error(err);
      }
    });
  }

  useExample(example: string): void {
    this.talentQuery = example;
    this.runTalentSearch();
  }

  clearTalentSearch(): void {
    this.talentQuery = '';
    this.talentMode = false;
    this.talentResults = [];
    this.talentError = '';
  }

  getRelevanceClass(score: number): string {
    if (score >= 70) return 'relevance-high';
    if (score >= 45) return 'relevance-mid';
    return 'relevance-low';
  }

  loadCandidates(): void {
    this.loading = true;
    this.cvService.getAnalysisResults().subscribe({
      next: (data) => {
        this.candidates = (data || []).sort((a, b) =>
          (b.scores?.overallScore || 0) - (a.scores?.overallScore || 0)
        );
        this.applyFilters();
        this.loading = false;
      },
      error: (err) => {
        this.error = 'Erreur lors du chargement des candidats';
        this.loading = false;
        console.error(err);
      }
    });
  }

  /** Recalcule la liste affichée à partir de la recherche texte + du filtre
   *  de décision. Appelée à chaque frappe / changement de filtre. */
  applyFilters(): void {
    let result = [...this.candidates];

    // Filtre recherche
    if (this.searchQuery.trim()) {
      const q = this.searchQuery.toLowerCase().trim();
      result = result.filter(c =>
        (c.candidateName || '').toLowerCase().includes(q) ||
        (c.email || '').toLowerCase().includes(q)
      );
    }

    // Filtre décision
    if (this.filterDecision !== 'all') {
      result = result.filter(c => {
        const s = c.scores?.overallScore || 0;
        switch (this.filterDecision) {
          case 'excellent': return s >= 85;
          case 'strong':    return s >= 70 && s < 85;
          case 'moderate':  return s >= 55 && s < 70;
          case 'weak':      return s < 55;
          default: return true;
        }
      });
    }

    this.filteredCandidates = result;
  }

  onSearch(): void { this.applyFilters(); }
  setFilter(f: 'all' | 'excellent' | 'strong' | 'moderate' | 'weak'): void {
    this.filterDecision = f;
    this.applyFilters();
  }
  clearSearch(): void { this.searchQuery = ''; this.applyFilters(); }

  navigateToDetail(candidateId: string | undefined): void {
    if (candidateId === undefined) return;
    // Si on vient du Talent Search, transmettre la requête pour surligner les critères
    if (this.talentMode && this.talentQuery.trim()) {
      this.router.navigate(['/candidates', candidateId], { queryParams: { q: this.talentQuery.trim() } });
    } else {
      this.router.navigate(['/candidates', candidateId]);
    }
  }

  getScoreClass(score: number): string {
    if (score >= 85) return 'score-excellent';
    if (score >= 70) return 'score-strong';
    if (score >= 55) return 'score-moderate';
    return 'score-weak';
  }

  getDecisionLabel(score: number): string {
    if (score >= 85) return 'Excellent';
    if (score >= 70) return 'Fort';
    if (score >= 55) return 'Modéré';
    return 'Faible';
  }

  // Compteurs pour les filtres
  getCountByDecision(d: 'all' | 'excellent' | 'strong' | 'moderate' | 'weak'): number {
    if (d === 'all') return this.candidates.length;
    return this.candidates.filter(c => {
      const s = c.scores?.overallScore || 0;
      switch (d) {
        case 'excellent': return s >= 85;
        case 'strong':    return s >= 70 && s < 85;
        case 'moderate':  return s >= 55 && s < 70;
        case 'weak':      return s < 55;
        default: return false;
      }
    }).length;
  }
}
