import { Component, inject } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { AuthService } from '../../../../services/auth.service';

/**
 * ForgotPasswordComponent — étape 1 du "mot de passe oublié".
 * L'utilisateur saisit son e-mail ; on déclenche l'envoi du lien de
 * réinitialisation. Le message renvoyé est volontairement neutre (on ne
 * révèle pas si l'e-mail existe — bonne pratique de sécurité).
 */
@Component({
  selector: 'app-forgot-password',
  templateUrl: './forgot-password.component.html',
  styleUrls: ['../register/register.component.css']
})
export class ForgotPasswordComponent {
  form: FormGroup;
  loading = false;
  submitted = false;
  message: string | null = null;
  error: string | null = null;

  private fb = inject(FormBuilder);
  private auth = inject(AuthService);

  constructor() {
    this.form = this.fb.group({
      email: ['', [Validators.required, Validators.email]]
    });
  }

  get f() { return this.form.controls; }

  onSubmit(): void {
    this.submitted = true;
    this.error = null;
    this.message = null;
    if (this.form.invalid) return;

    this.loading = true;
    this.auth.forgotPassword(this.form.value.email).subscribe({
      next: (res) => {
        this.loading = false;
        this.message = res?.message ||
          "Si un compte existe pour cet email, un lien de réinitialisation vient d'être envoyé.";
      },
      error: () => {
        this.loading = false;
        this.error = "Une erreur est survenue. Veuillez réessayer.";
      }
    });
  }
}
