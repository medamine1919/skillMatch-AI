package com.cvanalysis.controller;

import com.cvanalysis.dto.AuthResponse;
import com.cvanalysis.dto.LoginRequest;
import com.cvanalysis.dto.RegisterRequest;
import com.cvanalysis.service.AuthService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.Map;

/**
 * ============================================================================
 *  AuthController — routes PUBLIQUES d'authentification (préfixe /auth).
 * ----------------------------------------------------------------------------
 *  Expose : /login, /register, /refresh. Ces routes sont accessibles sans
 *  jeton (voir SecurityConfig). Le contrôleur traduit les exceptions métier
 *  d'AuthService en codes HTTP + messages clairs interprétés par le frontend.
 * ============================================================================
 */
@RestController
@RequestMapping("/auth")
@CrossOrigin(origins = {"http://localhost:4200", "http://localhost:3000"})
public class AuthController {

    @Autowired
    private AuthService authService;

    /**
     * Connexion. Renvoie les jetons si OK ; sinon un code spécifique :
     *  - 403 ACCOUNT_PENDING / ACCOUNT_DECLINED selon le statut du compte ;
     *  - 401 si e-mail/mot de passe incorrect.
     */
    @PostMapping("/login")
    public ResponseEntity<?> login(@RequestBody LoginRequest loginRequest) {
        try {
            AuthResponse response = authService.login(loginRequest);
            return ResponseEntity.ok(response);
        } catch (RuntimeException e) {
            if ("ACCOUNT_PENDING".equals(e.getMessage())) {
                return ResponseEntity.status(HttpStatus.FORBIDDEN)
                    .body(Map.of("code", "ACCOUNT_PENDING",
                        "message", "Votre compte est en attente d'approbation par l'administrateur."));
            }
            if ("ACCOUNT_DECLINED".equals(e.getMessage())) {
                return ResponseEntity.status(HttpStatus.FORBIDDEN)
                    .body(Map.of("code", "ACCOUNT_DECLINED",
                        "message", "Votre accès a été refusé. Contactez l'administrateur."));
            }
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED)
                .body(Map.of("message", "Email ou mot de passe incorrect."));
        }
    }

    /**
     * Inscription — le compte est créé en statut PENDING (sauf admin).
     * Retourne un message indiquant si approbation requise.
     */
    @PostMapping("/register")
    public ResponseEntity<?> register(@RequestBody RegisterRequest registerRequest) {
        try {
            String result = authService.register(registerRequest);
            if ("PENDING".equals(result)) {
                return ResponseEntity.status(HttpStatus.CREATED)
                    .body(Map.of(
                        "status", "PENDING",
                        "message", "Votre compte a été créé. Vous recevrez un email dès que l'administrateur aura approuvé votre accès."
                    ));
            }
            // Admin : connexion directe
            return ResponseEntity.status(HttpStatus.CREATED)
                .body(authService.login(new com.cvanalysis.dto.LoginRequest(
                    registerRequest.getEmail(), registerRequest.getPassword())));
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.BAD_REQUEST)
                .body(Map.of("message", e.getMessage()));
        }
    }

    /**
     * Renouveler le token
     */
    /**
     * Mot de passe oublié — étape 1 : l'utilisateur saisit son e-mail.
     * On renvoie TOUJOURS un succès (ne pas révéler si l'e-mail existe).
     */
    @PostMapping("/forgot-password")
    public ResponseEntity<?> forgotPassword(@RequestBody Map<String, String> payload) {
        String email = payload.get("email");
        if (email == null || email.isBlank()) {
            return ResponseEntity.badRequest().body(Map.of("message", "Email requis."));
        }
        authService.requestPasswordReset(email);
        return ResponseEntity.ok(Map.of(
            "message", "Si un compte existe pour cet email, un lien de réinitialisation vient d'être envoyé."));
    }

    /**
     * Mot de passe oublié — étape 2 : l'utilisateur fournit le jeton (reçu par
     * e-mail) et son nouveau mot de passe.
     */
    @PostMapping("/reset-password")
    public ResponseEntity<?> resetPassword(@RequestBody Map<String, String> payload) {
        try {
            authService.resetPassword(payload.get("token"), payload.get("newPassword"));
            return ResponseEntity.ok(Map.of("message", "Votre mot de passe a été réinitialisé. Vous pouvez vous connecter."));
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(Map.of("message", e.getMessage()));
        }
    }

    /**
     * Renouvelle l'access token à partir d'un refresh token valide
     * (évite de redemander le mot de passe quand le jeton court expire).
     */
    @PostMapping("/refresh")
    public ResponseEntity<?> refreshToken(@RequestBody Map<String, String> payload) {
        try {
            String refreshToken = payload.get("refreshToken");
            if (refreshToken == null || refreshToken.isBlank()) {
                return ResponseEntity.status(HttpStatus.BAD_REQUEST).body("refreshToken manquant");
            }
            AuthResponse response = authService.refreshToken(refreshToken);
            return ResponseEntity.ok(response);
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED).body(e.getMessage());
        }
    }
}
