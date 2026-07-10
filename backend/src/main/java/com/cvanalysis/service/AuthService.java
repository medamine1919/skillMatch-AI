package com.cvanalysis.service;

import com.cvanalysis.dto.AuthResponse;
import com.cvanalysis.dto.LoginRequest;
import com.cvanalysis.dto.RegisterRequest;
import com.cvanalysis.entity.User;
import com.cvanalysis.repository.UserRepository;
import com.cvanalysis.security.JwtTokenProvider;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.security.authentication.AuthenticationManager;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;

import java.util.UUID;

/**
 * ============================================================================
 *  AuthService — logique d'AUTHENTIFICATION et d'INSCRIPTION.
 * ----------------------------------------------------------------------------
 *  Gère trois opérations :
 *    - login()        : connexion (bloquée si le compte n'est pas APPROVED) ;
 *    - register()     : inscription en attente d'approbation admin (workflow
 *                       de validation par e-mail) ;
 *    - refreshToken() : renouvellement du jeton d'accès via le refresh token.
 * ============================================================================
 */
@Service
public class AuthService {

    @Autowired
    private UserRepository userRepository;

    @Autowired
    private PasswordEncoder passwordEncoder;

    @Autowired
    private AuthenticationManager authenticationManager;

    @Autowired
    private JwtTokenProvider tokenProvider;

    @Autowired
    private EmailService emailService;

    @Value("${brevo.admin-email}")
    private String adminEmail;

    /**
     * Connexion utilisateur — bloquée si compte PENDING ou DECLINED
     */
    public AuthResponse login(LoginRequest loginRequest) {
        // On vérifie le STATUT du compte AVANT de valider le mot de passe :
        // un compte non approuvé ne doit pas pouvoir se connecter, même avec
        // les bons identifiants. Les messages d'erreur (codes) sont interprétés
        // par le frontend pour afficher le bon message à l'utilisateur.
        User user = userRepository.findByEmail(loginRequest.getEmail())
                .orElseThrow(() -> new RuntimeException("Utilisateur non trouvé"));

        if (user.getStatus() == User.Status.PENDING) {
            throw new RuntimeException("ACCOUNT_PENDING");      // en attente d'approbation
        }
        if (user.getStatus() == User.Status.DECLINED) {
            throw new RuntimeException("ACCOUNT_DECLINED");     // compte refusé par l'admin
        }

        // Authentification réelle : Spring vérifie l'e-mail + mot de passe (BCrypt).
        Authentication authentication = authenticationManager.authenticate(
                new UsernamePasswordAuthenticationToken(
                        loginRequest.getEmail(),
                        loginRequest.getPassword()
                )
        );

        // Identifiants valides -> on génère les deux jetons (accès + refresh).
        UserDetails userDetails = (UserDetails) authentication.getPrincipal();
        String token = tokenProvider.generateToken(userDetails);
        String refreshToken = tokenProvider.generateRefreshToken(userDetails);

        return new AuthResponse(
                token,
                refreshToken,
                new AuthResponse.UserDTO(
                        user.getId(),
                        user.getEmail(),
                        user.getName(),
                        user.getRole().name()
                )
        );
    }

    /**
     * Inscription — compte créé en statut PENDING, email envoyé à l'admin
     */
    public String register(RegisterRequest registerRequest) {
        // Unicité de l'e-mail : on refuse les doublons.
        if (userRepository.existsByEmail(registerRequest.getEmail())) {
            throw new RuntimeException("Cet email est déjà utilisé");
        }
        // Contrôle de robustesse du mot de passe (même règle que le frontend) :
        // 8 caractères minimum, au moins une lettre ET un chiffre.
        if (!isStrongPassword(registerRequest.getPassword())) {
            throw new RuntimeException("Le mot de passe doit contenir au moins 8 caractères, avec au moins une lettre et un chiffre.");
        }

        // Cas spécial : l'adresse admin (définie en config) est approuvée
        // automatiquement et reçoit le rôle ADMIN_RH.
        boolean isAdmin = adminEmail.equalsIgnoreCase(registerRequest.getEmail());

        User user = new User();
        user.setEmail(registerRequest.getEmail());
        // Le mot de passe est HACHÉ (BCrypt) avant stockage — jamais en clair.
        user.setPassword(passwordEncoder.encode(registerRequest.getPassword()));
        user.setName(registerRequest.getName());
        user.setRole(isAdmin ? User.Role.ADMIN_RH : User.Role.RECRUITER);
        user.setEnabled(true);
        // Admin -> APPROVED direct ; recruteur -> PENDING (attend validation).
        user.setStatus(isAdmin ? User.Status.APPROVED : User.Status.PENDING);
        // Jeton unique inclus dans le lien d'approbation envoyé à l'admin.
        user.setApprovalToken(UUID.randomUUID().toString());

        userRepository.save(user);

        if (!isAdmin) {
            // Recruteur : on prévient l'admin par e-mail (avec liens approuver/refuser).
            emailService.sendApprovalRequestToAdmin(
                user.getName(), user.getEmail(),
                String.valueOf(user.getId()), user.getApprovalToken()
            );
            return "PENDING";
        }

        return "APPROVED";
    }

    /**
     * Renouveler le token
     */
    public AuthResponse refreshToken(String refreshToken) {
        // Le refresh token (longue durée) permet d'obtenir un nouvel access
        // token sans redemander le mot de passe. On le valide d'abord.
        if (!tokenProvider.validateToken(refreshToken)) {
            throw new RuntimeException("Token de rafraîchissement invalide");
        }

        String userEmail = tokenProvider.getEmailFromToken(refreshToken);
        User user = userRepository.findByEmail(userEmail)
                .orElseThrow(() -> new RuntimeException("Utilisateur non trouvé"));

        String newToken = tokenProvider.generateToken(user);
        String newRefreshToken = tokenProvider.generateRefreshToken(user);

        return new AuthResponse(
                newToken,
                newRefreshToken,
                new AuthResponse.UserDTO(
                        user.getId(),
                        user.getEmail(),
                        user.getName(),
                        user.getRole().name()
                )
        );
    }

    // =========================================================================
    // MOT DE PASSE OUBLIÉ
    // =========================================================================

    /** Règle de robustesse : 8+ caractères, au moins une lettre ET un chiffre. */
    private boolean isStrongPassword(String pwd) {
        return pwd != null && pwd.matches("^(?=.*[A-Za-z])(?=.*\\d).{8,}$");
    }

    /**
     * Étape 1 — l'utilisateur demande une réinitialisation via son e-mail.
     * On génère un jeton temporaire (valable 1h) et on envoie un lien par e-mail.
     * Pour des raisons de sécurité, on ne révèle PAS si l'e-mail existe ou non.
     */
    public void requestPasswordReset(String email) {
        userRepository.findByEmail(email).ifPresent(user -> {
            user.setResetToken(UUID.randomUUID().toString());
            user.setResetTokenExpiry(java.time.LocalDateTime.now().plusHours(1));
            userRepository.save(user);
            emailService.sendPasswordResetEmail(user.getName(), user.getEmail(), user.getResetToken());
        });
    }

    /**
     * Étape 2 — l'utilisateur fournit le jeton (reçu par e-mail) + un nouveau
     * mot de passe. On vérifie la validité/expiration du jeton, la robustesse
     * du mot de passe, puis on l'enregistre (haché) et on invalide le jeton.
     */
    public void resetPassword(String token, String newPassword) {
        User user = userRepository.findByResetToken(token)
                .orElseThrow(() -> new RuntimeException("Lien de réinitialisation invalide."));

        if (user.getResetTokenExpiry() == null
                || user.getResetTokenExpiry().isBefore(java.time.LocalDateTime.now())) {
            throw new RuntimeException("Le lien de réinitialisation a expiré. Veuillez refaire une demande.");
        }
        if (!isStrongPassword(newPassword)) {
            throw new RuntimeException("Le mot de passe doit contenir au moins 8 caractères, avec au moins une lettre et un chiffre.");
        }

        user.setPassword(passwordEncoder.encode(newPassword));
        // Jeton à usage unique : on l'efface après utilisation.
        user.setResetToken(null);
        user.setResetTokenExpiry(null);
        userRepository.save(user);
    }
}
