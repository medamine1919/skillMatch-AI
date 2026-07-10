import { Component, inject } from '@angular/core';
import { ActivatedRoute, Router } from '@angular/router';

@Component({
  selector: 'app-invalid-document',
  standalone: true,
  templateUrl: './invalid-document.component.html',
  styleUrls: ['./invalid-document.component.css']
})
/**
 * Page affichée quand le fichier uploadé n'est PAS un CV valide.
 * Le motif précis est passé via le paramètre d'URL ?reason=... (mis par
 * UploadComponent) et affiché à l'utilisateur, avec des boutons de retour.
 */
export class InvalidDocumentComponent {
  private router = inject(Router);
  private route = inject(ActivatedRoute);

  // Lit le motif d'erreur depuis l'URL (valeur par défaut si absent).
  get reason(): string {
    return this.route.snapshot.queryParamMap.get('reason') || 'Le fichier fourni ne ressemble pas à un CV valide.';
  }

  goToUpload(): void {
    this.router.navigate(['/upload']);
  }

  goToDashboard(): void {
    this.router.navigate(['/dashboard']);
  }
}