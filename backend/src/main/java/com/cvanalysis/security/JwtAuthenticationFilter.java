package com.cvanalysis.security;

import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.security.web.authentication.WebAuthenticationDetailsSource;
import org.springframework.util.StringUtils;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;

/**
 * ============================================================================
 *  JwtAuthenticationFilter — le "portier" exécuté à CHAQUE requête HTTP.
 * ----------------------------------------------------------------------------
 *  OncePerRequestFilter garantit qu'il tourne UNE fois par requête. Son rôle :
 *    1. lire le jeton JWT dans l'en-tête "Authorization: Bearer <token>" ;
 *    2. le valider (signature + non expiré) ;
 *    3. si valide, charger l'utilisateur et le déclarer "authentifié" dans le
 *       SecurityContext -> Spring autorise alors l'accès selon son rôle.
 *  Si pas de jeton (ou invalide), la requête continue mais non authentifiée
 *  (elle sera refusée par la config de sécurité si la route est protégée).
 * ============================================================================
 */
public class JwtAuthenticationFilter extends OncePerRequestFilter {

    @Autowired
    private JwtTokenProvider tokenProvider;

    @Autowired
    private UserDetailsService userDetailsService;

    @Override
    protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response, FilterChain filterChain)
            throws ServletException, IOException {
        try {
            // 1) Récupère le jeton depuis l'en-tête Authorization.
            String jwt = getJwtFromRequest(request);

            // 2) Si présent ET valide, on identifie l'utilisateur.
            if (StringUtils.hasText(jwt) && tokenProvider.validateToken(jwt)) {
                String userEmail = tokenProvider.getEmailFromToken(jwt);
                UserDetails userDetails = userDetailsService.loadUserByUsername(userEmail);

                // 3) On crée l'objet d'authentification (avec les rôles/autorités).
                UsernamePasswordAuthenticationToken authentication =
                        new UsernamePasswordAuthenticationToken(
                                userDetails,
                                null,
                                userDetails.getAuthorities());

                authentication.setDetails(new WebAuthenticationDetailsSource().buildDetails(request));
                // 4) On enregistre l'utilisateur comme "connecté" pour cette requête.
                SecurityContextHolder.getContext().setAuthentication(authentication);
            }
        } catch (Exception ex) {
            logger.error("Could not set user authentication in security context", ex);
        }

        // On passe la main au filtre/contrôleur suivant dans la chaîne.
        filterChain.doFilter(request, response);
    }

    /**
     * Extraire le JWT du header Authorization
     */
    private String getJwtFromRequest(HttpServletRequest request) {
        String bearerToken = request.getHeader("Authorization");
        if (StringUtils.hasText(bearerToken) && bearerToken.startsWith("Bearer ")) {
            return bearerToken.substring(7);
        }
        return null;
    }
}
