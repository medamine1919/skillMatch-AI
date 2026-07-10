package com.cvanalysis.config;

import com.cvanalysis.security.JwtAuthenticationFilter;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.config.annotation.authentication.configuration.AuthenticationConfiguration;
import org.springframework.security.config.annotation.method.configuration.EnableMethodSecurity;
import org.springframework.security.config.annotation.web.builders.HttpSecurity;
import org.springframework.security.config.annotation.web.configuration.EnableWebSecurity;
import org.springframework.security.config.http.SessionCreationPolicy;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.security.web.SecurityFilterChain;
import org.springframework.security.web.authentication.UsernamePasswordAuthenticationFilter;
import org.springframework.web.cors.CorsConfiguration;
import org.springframework.web.cors.CorsConfigurationSource;
import org.springframework.web.cors.UrlBasedCorsConfigurationSource;

import java.util.Arrays;

/**
 * ============================================================================
 *  SecurityConfig — configuration centrale de la sécurité (Spring Security).
 * ----------------------------------------------------------------------------
 *  Définit QUI peut accéder à QUOI, et comment les requêtes sont authentifiées.
 *  Points clés :
 *    - API STATELESS : aucune session serveur, tout repose sur le JWT.
 *    - Mots de passe hachés en BCrypt (jamais stockés en clair).
 *    - Filtre JWT inséré AVANT le filtre de login standard.
 *    - @EnableMethodSecurity active les @PreAuthorize sur les méthodes.
 * ============================================================================
 */
@Configuration
@EnableWebSecurity
@EnableMethodSecurity
public class SecurityConfig {

    /** Encodeur de mots de passe : BCrypt (algorithme de hachage salé, robuste). */
    @Bean
    public PasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }

    /** Gestionnaire d'authentification utilisé lors du login (vérifie identifiants). */
    @Bean
    public AuthenticationManager authenticationManager(AuthenticationConfiguration authConfig) throws Exception {
        return authConfig.getAuthenticationManager();
    }

    /** Notre filtre JWT (le "portier" exécuté à chaque requête). */
    @Bean
    public JwtAuthenticationFilter jwtAuthenticationFilter() {
        return new JwtAuthenticationFilter();
    }

    /**
     * Chaîne de filtres de sécurité : définit les règles d'accès aux routes.
     */
    @Bean
    public SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        http
                .cors()                                  // autorise le frontend Angular (voir CORS plus bas)
                .and()
                .csrf().disable()                        // pas de CSRF : API stateless protégée par JWT
                .sessionManagement().sessionCreationPolicy(SessionCreationPolicy.STATELESS)  // aucune session
                .and()
                // ----- Règles d'autorisation par route (du plus ouvert au plus fermé) -----
                .authorizeHttpRequests(authz -> authz
                        // Routes PUBLIQUES (login, inscription, refresh) : accessibles à tous.
                        .requestMatchers("/auth/login", "/auth/register", "/auth/refresh").permitAll()
                        .requestMatchers("/auth/forgot-password", "/auth/reset-password").permitAll()
                        // Passage du test technique par le candidat (sans login, via jeton)
                        .requestMatchers("/public/**").permitAll()
                        // Liens d'approbation/refus envoyés par e-mail : publics (cliqués hors session).
                        .requestMatchers("/auth/approve/**", "/auth/decline/**").permitAll()
                        // Administration : réservée au rôle ADMIN_RH.
                        .requestMatchers("/admin/**").hasRole("ADMIN_RH")
                        // Analyse de CV : tout utilisateur authentifié.
                        .requestMatchers("/cv-analysis/**").authenticated()
                        // Tableau de bord des tests techniques : tout utilisateur authentifié.
                        .requestMatchers("/tests", "/tests/**").authenticated()
                        // Tout le reste est REFUSÉ par défaut (principe de moindre privilège).
                        .anyRequest().denyAll()
                )
                // On insère notre filtre JWT AVANT le filtre de login par formulaire.
                .addFilterBefore(jwtAuthenticationFilter(), UsernamePasswordAuthenticationFilter.class);

        return http.build();
    }

    /**
     * Configuration CORS : autorise le frontend Angular (localhost:4200) à
     * appeler l'API (sinon le navigateur bloquerait les requêtes cross-origin).
     */
    @Bean
    public CorsConfigurationSource corsConfigurationSource() {
        CorsConfiguration configuration = new CorsConfiguration();
        configuration.setAllowedOrigins(Arrays.asList("http://localhost:4200", "http://localhost:3000"));
        configuration.setAllowedMethods(Arrays.asList("GET", "POST", "PUT", "DELETE", "OPTIONS"));
        configuration.setAllowedHeaders(Arrays.asList("*"));
        configuration.setAllowCredentials(true);

        UrlBasedCorsConfigurationSource source = new UrlBasedCorsConfigurationSource();
        source.registerCorsConfiguration("/**", configuration);
        return source;
    }
}
