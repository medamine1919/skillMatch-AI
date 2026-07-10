import {
  Injectable,
  inject
} from '@angular/core';
import {
  HttpRequest,
  HttpHandler,
  HttpEvent,
  HttpInterceptor,
  HttpErrorResponse
} from '@angular/common/http';
import { Observable, throwError } from 'rxjs';
import { catchError, switchMap } from 'rxjs/operators';
import { AuthService } from '../services/auth.service';
import { Router } from '@angular/router';

/**
 * ============================================================================
 *  JwtInterceptor — intercepte TOUTES les requêtes HTTP sortantes.
 * ----------------------------------------------------------------------------
 *  Deux missions automatiques (le composant n'a rien à gérer) :
 *   1) AJOUTER l'en-tête "Authorization: Bearer <token>" sur les requêtes
 *      protégées (sauf login/register/refresh).
 *   2) RATTRAPER une erreur 401 (jeton expiré) : tenter un refresh puis
 *      REJOUER automatiquement la requête. Si le refresh échoue -> déconnexion.
 *  C'est le pendant client du JwtAuthenticationFilter côté serveur.
 * ============================================================================
 */
@Injectable()
export class JwtInterceptor implements HttpInterceptor {
  private authService = inject(AuthService);
  private router = inject(Router);

  intercept(request: HttpRequest<unknown>, next: HttpHandler): Observable<HttpEvent<unknown>> {
    // On repère les requêtes d'auth pour NE PAS y mettre de jeton ni boucler.
    const isAuthRequest = request.url.includes('/auth/login') || request.url.includes('/auth/register');
    const isRefreshRequest = request.url.includes('/auth/refresh');
    const token = this.authService.getAccessToken();

    // Ajouter le token JWT sur les requêtes protégées uniquement.
    if (token && !isAuthRequest && !isRefreshRequest) {
      request = request.clone({
        setHeaders: {
          Authorization: `Bearer ${token}`
        }
      });
    }

    return next.handle(request).pipe(
      catchError((error: HttpErrorResponse) => {
        // Ne jamais tenter de refresh depuis login/register/refresh pour eviter une boucle infinie.
        if (error.status === 401 && !isAuthRequest && !isRefreshRequest) {
          const savedRefreshToken = localStorage.getItem('refresh_token');
          if (!savedRefreshToken) {
            this.authService.logout();
            this.router.navigate(['/auth/login']);
            return throwError(() => error);
          }

          return this.authService.refreshToken().pipe(
            switchMap((response) => {
              // Relancer la requete originale avec le nouveau token.
              const newToken = response.token;
              return next.handle(request.clone({
                setHeaders: {
                  Authorization: `Bearer ${newToken}`
                }
              }));
            }),
            catchError((refreshError) => {
              // Si le refresh echoue, nettoyer la session et rediriger vers login.
              this.authService.logout();
              this.router.navigate(['/auth/login']);
              return throwError(() => refreshError);
            })
          );
        }

        // Gérer les erreurs 403 (Forbidden)
        if (error.status === 403) {
          this.router.navigate(['/unauthorized']);
        }

        return throwError(() => error);
      })
    );
  }
}
