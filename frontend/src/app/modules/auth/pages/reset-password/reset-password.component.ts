import { Component, OnInit, inject } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { ActivatedRoute, Router } from '@angular/router';
import { AuthService } from '../../../../services/auth.service';

/**
 * ResetPasswordComponent — étape 2 du "mot de passe oublié".
 * Lit le jeton depuis l'URL (?token=...), demande le nouveau mot de passe
 * (avec contrôle de robustesse identique à l'inscription : 8+ caractères,
 * lettres ET chiffres) puis appelle l'API. Redirige vers le login en cas de succès.
 */
@Component({
  selector: 'app-reset-password',
  templateUrl: './reset-password.component.html',
  styleUrls: ['../register/register.component.css']
})
export class ResetPasswordComponent implements OnInit {
  form: FormGroup;
  loading = false;
  submitted = false;
  message: string | null = null;
  error: string | null = null;
  private token = '';

  private fb = inject(FormBuilder);
  private auth = inject(AuthService);
  private route = inject(ActivatedRoute);
  private router = inject(Router);

  constructor() {
    this.form = this.fb.group({
      password: ['', [
        Validators.required,
        Validators.minLength(8),
        Validators.pattern(/^(?=.*[A-Za-z])(?=.*\d).{8,}$/)
      ]],
      confirmPassword: ['', Validators.required]
    }, { validators: (g: any) =>
      g.get('password')?.value === g.get('confirmPassword')?.value ? null : { mismatch: true }
    });
  }

  ngOnInit(): void {
    // Récupère le jeton transmis dans le lien e-mail.
    this.token = this.route.snapshot.queryParamMap.get('token') || '';
    if (!this.token) {
      this.error = "Lien invalide ou expiré. Veuillez refaire une demande.";
    }
  }

  get f() { return this.form.controls; }
  get mismatch(): boolean { return !!this.form.errors?.['mismatch']; }

  onSubmit(): void {
    this.submitted = true;
    this.error = null;
    this.message = null;
    if (this.form.invalid || !this.token) return;

    this.loading = true;
    this.auth.resetPassword(this.token, this.form.value.password).subscribe({
      next: (res) => {
        this.loading = false;
        this.message = res?.message || "Mot de passe réinitialisé. Redirection...";
        setTimeout(() => this.router.navigate(['/auth/login']), 2000);
      },
      error: (e) => {
        this.loading = false;
        this.error = e?.error?.message || "Une erreur est survenue. Le lien a peut-être expiré.";
      }
    });
  }
}
