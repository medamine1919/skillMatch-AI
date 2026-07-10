import { Injectable, inject } from '@angular/core';
import { CanActivate, Router, ActivatedRouteSnapshot, RouterStateSnapshot } from '@angular/router';
import { AuthService } from '../services/auth.service';

/**
 * ============================================================================
 *  AuthGuard — "gardien" de routes Angular (équivalent du SecurityConfig côté
 *  serveur, mais pour la NAVIGATION).
 * ----------------------------------------------------------------------------
 *  canActivate() est appelé AVANT d'afficher une page protégée :
 *   - non connecté        -> redirection vers /auth/login (en mémorisant l'URL
 *                            voulue pour y revenir après connexion) ;
 *   - connecté sans le bon rôle -> redirection vers /unauthorized ;
 *   - connecté avec le bon rôle -> accès autorisé.
 *  NB : c'est un confort UX. La VRAIE sécurité reste côté backend (le serveur
 *  refusera de toute façon une requête non autorisée).
 * ============================================================================
 */
@Injectable({
  providedIn: 'root'
})
export class AuthGuard implements CanActivate {
  private authService = inject(AuthService);
  private router = inject(Router);

  canActivate(route: ActivatedRouteSnapshot, state: RouterStateSnapshot): boolean {
    if (this.authService.isAuthenticated()) {
      // La route peut exiger des rôles précis (déclarés dans le routing via data.roles).
      const requiredRoles = route.data['roles'] as Array<string>;
      const user = this.authService.getCurrentUser();

      if (requiredRoles && requiredRoles.length > 0) {
        if (requiredRoles.includes(user?.role)) {
          return true;
        } else {
          this.router.navigate(['/unauthorized']);
          return false;
        }
      }

      return true;
    }

    // Rediriger vers le login et mémoriser l'URL demandée
    this.router.navigate(['/auth/login'], { queryParams: { returnUrl: state.url } });
    return false;
  }
}
