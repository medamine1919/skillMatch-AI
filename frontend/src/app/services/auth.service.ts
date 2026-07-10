import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { Observable, BehaviorSubject } from 'rxjs';
import { tap } from 'rxjs/operators';
import { environment } from '../../environments/environment';

export interface AuthResponse {
  token: string;
  refreshToken: string;
  user: {
    id: number;
    email: string;
    role: string;
  };
}

export interface LoginRequest {
  email: string;
  password: string;
}

/**
 * ============================================================================
 *  AuthService — gère l'authentification côté frontend.
 * ----------------------------------------------------------------------------
 *  Rôles :
 *   - appeler l'API (login / register / refresh) ;
 *   - STOCKER les jetons + l'utilisateur dans le localStorage (persiste après
 *     rafraîchissement de la page) ;
 *   - diffuser l'utilisateur courant à toute l'app via currentUser$.
 *
 *  BehaviorSubject = "boîte" qui retient la dernière valeur et la pousse à tous
 *  les abonnés. Quand l'utilisateur se connecte/déconnecte, la sidebar, les
 *  menus, etc. se mettent à jour automatiquement (programmation réactive RxJS).
 * ============================================================================
 */
@Injectable({
  providedIn: 'root'   // service unique (singleton) partagé dans toute l'app
})
export class AuthService {
  private apiUrl = `${environment.apiUrl}/api/auth`;
  // Source réactive de l'utilisateur connecté (initialisée depuis le localStorage).
  private currentUserSubject = new BehaviorSubject<any>(this.getStoredUser());
  public currentUser$ = this.currentUserSubject.asObservable();  // version lecture seule
  private http = inject(HttpClient);

  constructor() {
  }

  /**
   * Connexion utilisateur
   */
  login(credentials: LoginRequest): Observable<AuthResponse> {
    // tap() = "effet de bord" : à la réponse OK, on enregistre les jetons
    // sans modifier le flux renvoyé au composant.
    return this.http.post<AuthResponse>(`${this.apiUrl}/login`, credentials)
      .pipe(
        tap(response => this.handleAuthSuccess(response))
      );
  }

  /**
   * Inscription utilisateur
   */
  register(email: string, password: string, name: string): Observable<any> {
    return this.http.post<any>(`${this.apiUrl}/register`, {
      email,
      password,
      name
    })
      .pipe(
        tap(response => {
          // Ne connecter que si un token est renvoyé (cas admin).
          // Pour un compte PENDING, la réponse ne contient pas de token.
          if (response && response.token) {
            this.handleAuthSuccess(response);
          }
        })
      );
  }

  /**
   * Renouveler le token JWT
   */
  refreshToken(): Observable<AuthResponse> {
    const refreshToken = localStorage.getItem('refresh_token');
    return this.http.post<AuthResponse>(`${this.apiUrl}/refresh`, { refreshToken })
      .pipe(
        tap(response => this.handleAuthSuccess(response))
      );
  }

  /**
   * Mot de passe oublié — demande d'un lien de réinitialisation par e-mail.
   */
  forgotPassword(email: string): Observable<any> {
    return this.http.post<any>(`${this.apiUrl}/forgot-password`, { email });
  }

  /**
   * Mot de passe oublié — envoi du nouveau mot de passe avec le jeton reçu.
   */
  resetPassword(token: string, newPassword: string): Observable<any> {
    return this.http.post<any>(`${this.apiUrl}/reset-password`, { token, newPassword });
  }

  /**
   * Déconnexion
   */
  logout(): void {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user');
    this.currentUserSubject.next(null);
  }

  /**
   * Obtenir le token d'accès
   */
  getAccessToken(): string | null {
    return localStorage.getItem('access_token');
  }

  /**
   * Vérifier si l'utilisateur est connecté
   */
  isAuthenticated(): boolean {
    return !!this.getAccessToken();
  }

  /**
   * Obtenir l'utilisateur courant
   */
  getCurrentUser(): any {
    return this.currentUserSubject.value;
  }

  /**
   * Traiter la réussite de l'authentification
   */
  private handleAuthSuccess(response: AuthResponse): void {
    // On garde jetons + utilisateur en localStorage (survit au refresh navigateur)
    localStorage.setItem('access_token', response.token);
    localStorage.setItem('refresh_token', response.refreshToken);
    localStorage.setItem('user', JSON.stringify(response.user));
    // On notifie toute l'app que l'utilisateur a changé.
    this.currentUserSubject.next(response.user);
  }

  /**
   * Charger l'utilisateur courant depuis le localStorage
   */
  private getStoredUser(): any {
    const user = localStorage.getItem('user');
    // Ignorer les valeurs invalides ("undefined"/"null" stockées par erreur)
    if (user && user !== 'undefined' && user !== 'null') {
      try {
        return JSON.parse(user);
      } catch (e) {
        console.error('Erreur lors du chargement de l\'utilisateur', e);
        localStorage.removeItem('user'); // nettoyer la valeur corrompue
      }
    }

    return null;
  }
}
