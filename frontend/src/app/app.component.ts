import { Component } from '@angular/core';
import { Router } from '@angular/router';
import { AuthService } from './services/auth.service';

@Component({
  selector: 'app-root',
  standalone: false,
  templateUrl: './app.component.html',
  styleUrls: ['./app.component.css']
})
/**
 * AppComponent — composant RACINE de l'application (la "coquille").
 * Affiche la barre latérale + le <router-outlet> qui charge la page courante.
 * currentUser$ est observé par le template pour montrer/masquer la sidebar et
 * adapter le menu selon que l'utilisateur est connecté (et selon son rôle).
 */
export class AppComponent {
  title = 'CV Analysis Platform';
  // Flux réactif de l'utilisateur connecté (| async dans le HTML).
  currentUser$ = this.authService.currentUser$;

  constructor(private authService: AuthService, private router: Router) { }

  /** Déconnexion immédiate : vide la session puis redirige vers le login. */
  logout(): void {
    this.authService.logout();                       // efface jetons + utilisateur
    this.router.navigate(['/auth/login']);           // redirection directe
  }

  /** Traduit le code de rôle technique en libellé lisible affiché dans la sidebar. */
  roleLabel(role: string): string {
    switch (role) {
      case 'ADMIN_RH':  return 'Administrateur RH';
      case 'RECRUITER': return 'Recruteur';
      case 'USER':      return 'Utilisateur';
      default:          return role || '';
    }
  }
}
