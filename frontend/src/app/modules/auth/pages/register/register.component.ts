import { Component, OnInit, inject } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { Router } from '@angular/router';
import { AuthService } from '../../../../services/auth.service';

@Component({
  selector: 'app-register',
  templateUrl: './register.component.html',
  styleUrls: ['./register.component.css']
})
/**
 * ============================================================================
 *  RegisterComponent — page d'inscription d'un nouveau recruteur.
 * ----------------------------------------------------------------------------
 *  Formulaire réactif avec un validateur PERSONNALISÉ (passwordMatchValidator)
 *  qui vérifie que mot de passe == confirmation. À la soumission :
 *   - statut PENDING -> message "compte en attente d'approbation admin" ;
 *   - sinon (admin)  -> connexion directe + redirection dashboard.
 * ============================================================================
 */
export class RegisterComponent implements OnInit {
  registerForm!: FormGroup;
  loading = false;
  submitted = false;
  error: string | null = null;
  success: string | null = null;
  private formBuilder: FormBuilder = inject(FormBuilder);
  private router: Router = inject(Router);
  private authService: AuthService = inject(AuthService);

  constructor() { }

  get passwordMismatch(): boolean {
    return !!this.registerForm?.errors?.['passwordMismatch'];
  }

  ngOnInit(): void {
    this.initializeForm();
  }

  /**
   * Initialiser le formulaire d'inscription
   */
  private initializeForm(): void {
    this.registerForm = this.formBuilder.group({
      name: ['', [Validators.required, Validators.minLength(3)]],
      email: ['', [Validators.required, Validators.email]],
      // Mot de passe : 8+ caractères ET contenant au moins une lettre et un chiffre.
      // Validators.pattern applique l'expression régulière (?=.*lettre)(?=.*chiffre).{8,}
      password: ['', [
        Validators.required,
        Validators.minLength(8),
        Validators.pattern(/^(?=.*[A-Za-z])(?=.*\d).{8,}$/)
      ]],
      confirmPassword: ['', Validators.required]
    }, {
      validators: this.passwordMatchValidator
    });
  }

  /**
   * Validator personnalisé pour vérifier que les mots de passe correspondent
   */
  // Validateur au niveau du GROUPE (pas d'un seul champ) : compare les deux
  // mots de passe. Retourne une erreur 'passwordMismatch' s'ils diffèrent.
  private passwordMatchValidator(group: FormGroup): { [key: string]: any } | null {
    const password = group.get('password')?.value;
    const confirmPassword = group.get('confirmPassword')?.value;
    return password === confirmPassword ? null : { 'passwordMismatch': true };
  }

  /**
   * Soumettre le formulaire d'inscription
   */
  onSubmit(): void {
    this.submitted = true;
    this.error = null;
    this.success = null;

    if (this.registerForm.invalid) {
      return;
    }

    this.loading = true;

    this.authService.register(
      this.registerForm.value.email,
      this.registerForm.value.password,
      this.registerForm.value.name
    ).subscribe({
      next: (response: any) => {
        this.loading = false;
        if (response?.status === 'PENDING') {
          // Compte créé mais en attente d'approbation
          this.success = 'Votre compte a été créé avec succès ! Un email a été envoyé à l\'administrateur. Vous serez notifié par email dès que votre accès sera approuvé.';
          // Ne pas rediriger — rester sur la page
        } else {
          // Admin connecté directement
          this.success = 'Connexion réussie ! Redirection...';
          setTimeout(() => this.router.navigate(['/dashboard']), 1500);
        }
      },
      error: (error) => {
        this.loading = false;
        this.error =
          (typeof error.error === 'string' && error.error) ||
          error.error?.message ||
          'Erreur d\'inscription. Veuillez réessayer.';
      }
    });
  }

  /**
   * Getters pour accéder aux contrôles du formulaire
   */
  get f() {
    return this.registerForm.controls;
  }
}
