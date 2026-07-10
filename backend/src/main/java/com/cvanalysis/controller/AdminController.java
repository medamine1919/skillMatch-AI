package com.cvanalysis.controller;

import com.cvanalysis.entity.User;
import com.cvanalysis.repository.UserRepository;
import com.cvanalysis.service.CVAnalysisService;
import com.cvanalysis.service.EmailService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.*;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

import java.net.URLEncoder;
import java.nio.charset.StandardCharsets;
import java.util.List;
import java.util.Map;
import java.util.stream.Collectors;

/**
 * ============================================================================
 *  AdminController — espace d'ADMINISTRATION (réservé au rôle ADMIN_RH).
 * ----------------------------------------------------------------------------
 *  Regroupe trois familles d'endpoints :
 *    - ANALYTICS  : vue d'ensemble par recruteur + liste de tous les candidats ;
 *    - UTILISATEURS : lister, approuver, refuser, changer le rôle ;
 *    - APPROBATION PAR E-MAIL : liens cliqués par l'admin depuis sa boîte mail
 *      (ces routes-là sont publiques car ouvertes hors session).
 *
 *  @PreAuthorize("hasRole('ADMIN_RH')") protège chaque opération sensible.
 * ============================================================================
 */
@RestController
@CrossOrigin(origins = {"http://localhost:4200", "http://localhost:3000"})
public class AdminController {

    @Autowired
    private UserRepository userRepository;

    @Autowired
    private EmailService emailService;

    @Autowired
    private CVAnalysisService cvAnalysisService;

    @Value("${app.frontend-url:http://localhost:4200}")
    private String frontendUrl;

    // =========================================================
    // ANALYTICS ADMIN — vue par recruteur + tous les candidats
    // =========================================================
    @GetMapping("/admin/analytics/overview")
    @PreAuthorize("hasRole('ADMIN_RH')")
    public ResponseEntity<?> analyticsOverview() {
        return ResponseEntity.ok(cvAnalysisService.getRecruitersAnalytics());
    }

    @GetMapping("/admin/analytics/candidates")
    @PreAuthorize("hasRole('ADMIN_RH')")
    public ResponseEntity<?> analyticsCandidates() {
        return ResponseEntity.ok(cvAnalysisService.getAllCandidatesWithRecruiter());
    }

    // =========================================================
    // PANEL ADMIN — Liste tous les utilisateurs
    // =========================================================
    @GetMapping("/admin/users")
    @PreAuthorize("hasRole('ADMIN_RH')")
    public ResponseEntity<?> getAllUsers() {
        List<Map<String, Object>> users = userRepository.findAllByOrderByCreatedAtDesc()
            .stream()
            .map(this::toDto)
            .collect(Collectors.toList());
        return ResponseEntity.ok(users);
    }

    // =========================================================
    // PANEL ADMIN — Liste utilisateurs PENDING
    // =========================================================
    @GetMapping("/admin/users/pending")
    @PreAuthorize("hasRole('ADMIN_RH')")
    public ResponseEntity<?> getPendingUsers() {
        List<Map<String, Object>> users = userRepository
            .findByStatusOrderByCreatedAtDesc(User.Status.PENDING)
            .stream()
            .map(this::toDto)
            .collect(Collectors.toList());
        return ResponseEntity.ok(users);
    }

    // =========================================================
    // PANEL ADMIN — Approuver un utilisateur (par ID)
    // =========================================================
    @PostMapping("/admin/users/{id}/approve")
    @PreAuthorize("hasRole('ADMIN_RH')")
    public ResponseEntity<?> approveUser(@PathVariable Long id) {
        return userRepository.findById(id).map(user -> {
            user.setStatus(User.Status.APPROVED);
            user.setRole(User.Role.RECRUITER);
            userRepository.save(user);
            emailService.sendApprovalConfirmation(user.getName(), user.getEmail());
            return ResponseEntity.ok(Map.of("message", "Utilisateur approuvé", "user", toDto(user)));
        }).orElse(ResponseEntity.notFound().build());
    }

    // =========================================================
    // PANEL ADMIN — Décliner un utilisateur (par ID)
    // =========================================================
    @PostMapping("/admin/users/{id}/decline")
    @PreAuthorize("hasRole('ADMIN_RH')")
    public ResponseEntity<?> declineUser(@PathVariable Long id) {
        return userRepository.findById(id).map(user -> {
            user.setStatus(User.Status.DECLINED);
            userRepository.save(user);
            emailService.sendDeclineNotification(user.getName(), user.getEmail());
            return ResponseEntity.ok(Map.of("message", "Utilisateur décliné", "user", toDto(user)));
        }).orElse(ResponseEntity.notFound().build());
    }

    // =========================================================
    // PANEL ADMIN — Changer le rôle d'un utilisateur
    // =========================================================
    @PostMapping("/admin/users/{id}/role")
    @PreAuthorize("hasRole('ADMIN_RH')")
    public ResponseEntity<?> changeRole(@PathVariable Long id, @RequestBody Map<String, String> body) {
        String roleStr = body.get("role");
        if (roleStr == null) {
            return ResponseEntity.badRequest().body(Map.of("message", "Rôle manquant"));
        }
        final User.Role newRole;
        try {
            newRole = User.Role.valueOf(roleStr.toUpperCase());
        } catch (IllegalArgumentException e) {
            return ResponseEntity.badRequest().body(Map.of("message", "Rôle invalide : " + roleStr));
        }
        return userRepository.findById(id).map(user -> {
            user.setRole(newRole);
            // Un compte à qui on attribue un rôle est forcément actif
            if (user.getStatus() != User.Status.APPROVED) {
                user.setStatus(User.Status.APPROVED);
            }
            userRepository.save(user);
            return ResponseEntity.ok(Map.of("message", "Rôle mis à jour", "user", toDto(user)));
        }).orElse(ResponseEntity.notFound().build());
    }

    // =========================================================
    // LIEN EMAIL — Approuver via token (bouton dans le mail)
    // =========================================================
    @GetMapping("/auth/approve/{token}")
    public ResponseEntity<Void> approveViaToken(@PathVariable String token) {
        return userRepository.findByApprovalToken(token).map(user -> {
            user.setStatus(User.Status.APPROVED);
            user.setRole(User.Role.RECRUITER);
            userRepository.save(user);
            emailService.sendApprovalConfirmation(user.getName(), user.getEmail());
            // Rediriger vers le front avec message de succès
            return redirectTo("/admin/users?approved=" + enc(user.getName()));
        }).orElseGet(() -> redirectTo("/admin/users?error=token_invalid"));
    }

    // =========================================================
    // LIEN EMAIL — Décliner via token (bouton dans le mail)
    // =========================================================
    @GetMapping("/auth/decline/{token}")
    public ResponseEntity<Void> declineViaToken(@PathVariable String token) {
        return userRepository.findByApprovalToken(token).map(user -> {
            user.setStatus(User.Status.DECLINED);
            userRepository.save(user);
            emailService.sendDeclineNotification(user.getName(), user.getEmail());
            return redirectTo("/admin/users?declined=" + enc(user.getName()));
        }).orElseGet(() -> redirectTo("/admin/users?error=token_invalid"));
    }

    /** Construit une réponse de redirection 302 vers le frontend */
    private ResponseEntity<Void> redirectTo(String path) {
        HttpHeaders headers = new HttpHeaders();
        headers.setLocation(java.net.URI.create(frontendUrl + path));
        return new ResponseEntity<>(headers, HttpStatus.FOUND);
    }

    /** Encode un paramètre d'URL (gère les espaces, accents, etc.) */
    private String enc(String value) {
        return URLEncoder.encode(value, StandardCharsets.UTF_8);
    }

    // =========================================================
    // DTO utilisateur (sans mot de passe)
    // =========================================================
    private Map<String, Object> toDto(User u) {
        return Map.of(
            "id",        u.getId(),
            "name",      u.getName(),
            "email",     u.getEmail(),
            "role",      u.getRole().name(),
            "status",    u.getStatus().name(),
            "createdAt", u.getCreatedAt() != null ? u.getCreatedAt().toString() : ""
        );
    }
}
