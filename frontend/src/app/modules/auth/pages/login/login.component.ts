import { Component, OnInit, inject } from '@angular/core';
import { FormBuilder, FormGroup, Validators } from '@angular/forms';
import { Router, ActivatedRoute } from '@angular/router';
import { AuthService } from '../../../../services/auth.service';

@Component({
  selector: 'app-login',
  templateUrl: './login.component.html',
  styleUrls: ['./login.component.css']
})
/**
 * ============================================================================
 *  LoginComponent — page de connexion.
 * ----------------------------------------------------------------------------
 *  Utilise un "Reactive Form" (FormGroup) avec validations (email valide, mot
 *  de passe min 6 caractères). À la soumission, appelle AuthService.login() et :
 *   - succès -> redirige vers returnUrl (la page demandée avant le login) ;
 *   - échec  -> affiche un message ADAPTÉ selon le code renvoyé par le serveur
 *               (compte en attente, refusé, ou identifiants incorrects).
 * ============================================================================
 */
export class LoginComponent implements OnInit {
  loginForm!: FormGroup;
  loading = false;
  submitted = false;                  // passe à true après une tentative (affiche les erreurs de champ)
  error: string | null = null;
  errorType: 'pending' | 'declined' | 'generic' | null = null;  // pour styliser le message
  returnUrl: string = '';             // page à rejoindre après connexion réussie
  private formBuilder: FormBuilder = inject(FormBuilder);
  private route: ActivatedRoute = inject(ActivatedRoute);
  private router: Router = inject(Router);
  private authService: AuthService = inject(AuthService);

  constructor() { }

  // ngOnInit : exécuté à l'affichage du composant (cycle de vie Angular).
  ngOnInit(): void {
    // Eviter les boucles de refresh avec d'anciens tokens invalides.
    this.authService.logout();
    this.initializeForm();
    // Récupère ?returnUrl=... mis par le guard (sinon /home par défaut).
    this.returnUrl = this.route.snapshot.queryParams['returnUrl'] || '/home';
  }

  /**
   * Initialiser le formulaire de connexion
   */
  private initializeForm(): void {
    this.loginForm = this.formBuilder.group({
      email: ['', [Validators.required, Validators.email]],
      password: ['', [Validators.required, Validators.minLength(6)]],
      rememberMe: [false]
    });
  }

  /**
   * Soumettre le formulaire de connexion
   */
  onSubmit(): void {
    this.submitted = true;
    this.error = null;

    if (this.loginForm.invalid) {
      return;
    }

    this.loading = true;

    this.authService.login({
      email: this.loginForm.value.email,
      password: this.loginForm.value.password
    }).subscribe({
      next: (response) => {
        this.loading = false;
        this.router.navigateByUrl(this.returnUrl);
      },
      error: (error) => {
        this.loading = false;
        const code = error.error?.code;
        if (code === 'ACCOUNT_PENDING') {
          this.errorType = 'pending';
          this.error = 'Votre compte est en attente d\'approbation par l\'administrateur. Vous recevrez un email de confirmation.';
        } else if (code === 'ACCOUNT_DECLINED') {
          this.errorType = 'declined';
          this.error = 'Votre accès a été refusé. Contactez l\'administrateur : fonsibelhajmassoud@gmail.com';
        } else {
          this.errorType = 'generic';
          this.error = error.error?.message || 'Email ou mot de passe incorrect.';
        }
      }
    });
  }

  /**
   * Getters pour accéder aux contrôles du formulaire
   */
  // Raccourci pratique utilisé dans le HTML (ex: f['email'].errors) pour
  // afficher les messages de validation champ par champ.
  get f() {
    return this.loginForm.controls;
  }
}
