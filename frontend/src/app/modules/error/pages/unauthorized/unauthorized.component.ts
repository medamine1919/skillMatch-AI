import { Component, inject } from '@angular/core';
import { Router } from '@angular/router';

@Component({
  selector: 'app-unauthorized',
  templateUrl: './unauthorized.component.html',
  styleUrls: ['./unauthorized.component.css']
})
/**
 * Page "Accès refusé" (403) : affichée par le guard quand un utilisateur
 * connecté tente d'accéder à une route interdite à son rôle.
 */
export class UnauthorizedComponent {
  private router = inject(Router);

  constructor() { }

  goHome(): void {
    this.router.navigate(['/dashboard']);
  }
}
