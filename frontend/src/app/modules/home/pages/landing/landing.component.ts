import { Component, OnInit } from '@angular/core';
import { Router } from '@angular/router';
import { AuthService } from '../../../../services/auth.service';
import { CVAnalysisService } from '../../../../services/cv-analysis.service';

@Component({
  selector: 'app-landing',
  templateUrl: './landing.component.html',
  styleUrls: ['./landing.component.css']
})
/**
 * ============================================================================
 *  LandingComponent — page d'ACCUEIL après connexion.
 * ----------------------------------------------------------------------------
 *  Affiche un message de bienvenue personnalisé (selon l'heure), des raccourcis
 *  vers les fonctionnalités, quelques KPI rapides et les derniers candidats.
 *  Les tableaux `features` et `steps` alimentent l'affichage (boucle *ngFor).
 * ============================================================================
 */
export class LandingComponent implements OnInit {

  userName: string = 'Utilisateur';
  greeting: string = '';        // "Bonjour/Bon après-midi/Bonsoir" selon l'heure

  stats = {
    totalCandidates: 0,
    averageScore: 0,
    countExcellent: 0
  };

  recentCandidates: any[] = [];
  loading = true;

  features = [
    {
      icon: 'rocket',
      title: 'Analyser un CV',
      description: 'Téléversez un CV (PDF/DOCX) et obtenez une analyse IA détaillée en quelques secondes.',
      action: () => this.goToUpload(),
      color: 'gradient-purple',
      buttonText: 'Démarrer '
    },
    {
      icon: 'dashboard',
      title: 'Tableau de bord',
      description: 'Visualisez les KPIs, distributions et statistiques de tous vos candidats analysés.',
      action: () => this.goToDashboard(),
      color: 'gradient-blue',
      buttonText: 'Voir le dashboard '
    },
    {
      icon: 'users',
      title: 'Candidats analysés',
      description: 'Consultez l\'historique complet et les détails de chaque candidat avec leurs scores.',
      action: () => this.goToHistory(),
      color: 'gradient-green',
      buttonText: 'Voir l\'historique '
    }
  ];

  steps = [
    { num: 1, icon: 'document', title: 'Téléverser', desc: 'Importez le CV au format PDF ou DOCX' },
    { num: 2, icon: 'cpu', title: 'Analyse IA', desc: 'Notre IA extrait et analyse les compétences' },
    { num: 3, icon: 'trending-up', title: 'Scoring', desc: 'Calcul multi-critères sur 100 points' },
    { num: 4, icon: 'check-circle', title: 'Décision', desc: 'Recevez la recommandation finale' }
  ];

  constructor(
    private router: Router,
    private authService: AuthService,
    private cvService: CVAnalysisService
  ) {}

  ngOnInit(): void {
    this.loadUserInfo();
    this.computeGreeting();
    this.loadQuickStats();
  }

  private loadUserInfo(): void {
    const user = this.authService.getCurrentUser();
    if (user?.email) {
      this.userName = user.email.split('@')[0];
    }
  }

  private computeGreeting(): void {
    const hour = new Date().getHours();
    if (hour < 12) this.greeting = 'Bonjour';
    else if (hour < 18) this.greeting = 'Bon après-midi';
    else this.greeting = 'Bonsoir';
  }

  private loadQuickStats(): void {
    this.cvService.getStatistics().subscribe({
      next: (data) => {
        this.stats = {
          totalCandidates: data.totalCandidates || 0,
          averageScore: Math.round(data.averageScore || 0),
          countExcellent: data.countExcellent || 0
        };
      },
      error: () => { /* silencieux — page d'accueil */ }
    });

    this.cvService.getAnalysisResults().subscribe({
      next: (data) => {
        this.recentCandidates = (data || [])
          .sort((a: any, b: any) =>
            new Date(b.createdAt || 0).getTime() - new Date(a.createdAt || 0).getTime())
          .slice(0, 5);
        this.loading = false;
      },
      error: () => { this.loading = false; }
    });
  }

  goToDashboard(): void { this.router.navigate(['/dashboard']); }
  goToHistory(): void { this.router.navigate(['/candidates']); }
  goToUpload(): void { this.router.navigate(['/upload']); }
  goToCandidate(id: number): void { this.router.navigate(['/candidates', id]); }

  getScoreClass(score: number): string {
    if (score >= 85) return 'score-excellent';
    if (score >= 70) return 'score-strong';
    if (score >= 55) return 'score-moderate';
    return 'score-weak';
  }
}
