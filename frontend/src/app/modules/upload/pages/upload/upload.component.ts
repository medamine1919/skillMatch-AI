import { Component, ElementRef, ViewChild, inject } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { CVAnalysisService } from '../../../../services/cv-analysis.service';
import { Router } from '@angular/router';

@Component({
  selector: 'app-upload',
  templateUrl: './upload.component.html',
  styleUrls: ['./upload.component.css']
})
/**
 * ============================================================================
 *  UploadComponent — page d'upload + lancement de l'analyse d'un CV.
 * ----------------------------------------------------------------------------
 *  Gère : sélection du fichier (clic OU glisser-déposer), validation du format
 *  (PDF/DOC/DOCX), envoi au backend, puis redirection vers la fiche du candidat.
 *  Si le fichier n'est pas un CV, on redirige vers une page d'erreur dédiée.
 *  Les variables loading/error/success pilotent l'affichage (spinner, messages).
 * ============================================================================
 */
export class UploadComponent {
  uploadForm!: FormGroup;
  loading = false;                    // true pendant l'analyse (affiche le spinner)
  error: string | null = null;        // message d'erreur éventuel
  success: string | null = null;
  selectedFile: File | null = null;   // fichier choisi par l'utilisateur
  isDragging = false;                 // état visuel du glisser-déposer

  @ViewChild('fileInput') fileInput!: ElementRef<HTMLInputElement>;
  private fb     = inject(FormBuilder);
  private cvSvc  = inject(CVAnalysisService);
  private router = inject(Router);

  constructor() {
    // L'exigence du poste est désormais OBLIGATOIRE : sans elle, le CV ne peut
    // pas être noté par rapport à un besoin précis. On exige au moins 10 caractères.
    this.uploadForm = this.fb.group({
      requirements: ['', [Validators.required, Validators.minLength(10)]]
    });
  }

  onFileSelected(event: any): void {
    this.setFile(event.target.files?.[0]);
  }

  onDragOver(e: DragEvent): void { e.preventDefault(); e.stopPropagation(); this.isDragging = true; }
  onDragLeave(e: DragEvent): void { e.preventDefault(); e.stopPropagation(); this.isDragging = false; }

  onDrop(e: DragEvent): void {
    e.preventDefault(); e.stopPropagation();
    this.isDragging = false;
    this.setFile(e.dataTransfer?.files?.[0] ?? null);
    if (this.fileInput?.nativeElement) this.fileInput.nativeElement.value = '';
  }

  openFilePicker(): void { this.fileInput?.nativeElement.click(); }

  removeFile(e: Event): void {
    e.stopPropagation();
    this.selectedFile = null;
    this.error = null;
    if (this.fileInput?.nativeElement) this.fileInput.nativeElement.value = '';
  }

  private setFile(file: File | null | undefined): void {
    if (file && this.isValid(file)) {
      this.selectedFile = file;
      this.error = null;
    } else if (file) {
      this.error = 'Format invalide. Acceptés : PDF, DOC, DOCX';
      this.selectedFile = null;
    }
  }

  private isNonCvError(message: string): boolean {
    const normalized = message.toLowerCase();
    return normalized.includes('pas un cv')
      || normalized.includes('ne ressemble pas à un cv')
      || normalized.includes('ne ressemble pas a un cv')
      || normalized.includes('données extraites non conformes à un cv')
      || normalized.includes('donnees extraites non conformes a un cv')
      || normalized.includes('invalid cv document');
  }

  private formatUploadError(err: any): string {
    const backend = err?.error;
    const backendMessage = typeof backend === 'string'
      ? backend
      : backend?.message || err?.message || '';

    if (backend?.errors?.length) {
      const msgs = backend.errors.map((e: any) =>
        `${Array.isArray(e.loc) ? e.loc.join('.') : e.loc}: ${e.msg}`);
      const prefix = backend.message || 'Le fichier fourni n\'est pas un CV.';
      return `${prefix} Merci de sélectionner un autre fichier. (${msgs.join(' ; ')})`;
    }

    if (backendMessage && this.isNonCvError(backendMessage)) {
      return `${backendMessage} Merci de sélectionner un autre fichier.`;
    }

    if (backendMessage) {
      return backendMessage;
    }

    return "Erreur lors de l'analyse. Merci de réessayer avec un autre fichier.";
  }

  private redirectToNonCvPage(message: string): void {
    this.router.navigate(['/invalid-document'], {
      queryParams: { reason: message }
    });
  }

  private isValid(file: File): boolean {
    const validMimes = [
      'application/pdf',
      'application/msword',
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    ];
    const ext = file.name.slice(file.name.lastIndexOf('.')).toLowerCase();
    return validMimes.includes(file.type) || ['.pdf', '.doc', '.docx'].includes(ext);
  }

  // Renvoie le NOM d'icône SVG correspondant au type de fichier (affiché via <app-icon>).
  getFileIcon(): string {
    return 'document';
  }

  getFileSize(): string {
    if (!this.selectedFile) return '';
    const kb = this.selectedFile.size / 1024;
    if (kb < 1024) return `${kb.toFixed(1)} KB`;
    return `${(kb / 1024).toFixed(1)} MB`;
  }

  /** Soumission : envoie le fichier + l'exigence du poste au backend, puis
   *  redirige vers la fiche détaillée du candidat analysé. */
  onSubmit(): void {
    if (!this.selectedFile) { this.error = 'Veuillez sélectionner un fichier.'; return; }
    // Exigence du poste obligatoire : on bloque tant qu'elle n'est pas remplie.
    if (this.uploadForm.invalid) {
      this.uploadForm.markAllAsTouched();
      this.error = 'Veuillez décrire les exigences du poste (au moins 10 caractères) pour analyser le CV par rapport au besoin.';
      return;
    }
    this.loading = true;
    this.error = null;
    this.success = null;

    // Appel asynchrone : subscribe() reçoit soit le succès (next), soit l'erreur.
    this.cvSvc.uploadAndAnalyzeCV(this.selectedFile, this.uploadForm.value.requirements || '').subscribe({
      next: (res) => {
        this.loading = false;
        this.router.navigate(['/candidates', res.id]);   // -> fiche du candidat
      },
      error: (err) => {
        this.loading = false;
        const formatted = this.formatUploadError(err);
        if (this.isNonCvError(formatted)) {
          this.redirectToNonCvPage(formatted);
          return;
        }
        this.error = formatted;
      }
    });
  }
}
