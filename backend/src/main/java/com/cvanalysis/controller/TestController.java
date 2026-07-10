package com.cvanalysis.controller;

import com.cvanalysis.entity.TechnicalTest;
import com.cvanalysis.entity.User;
import com.cvanalysis.repository.UserRepository;
import com.cvanalysis.service.TechnicalTestService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

/**
 * ============================================================================
 *  TestController — endpoints du test technique.
 * ----------------------------------------------------------------------------
 *  Deux familles :
 *   - SÉCURISÉES (recruteur connecté) : envoyer un test, lister les tests.
 *   - PUBLIQUES (/public/test/**) : passage du test par le candidat SANS login
 *     (authentifié par le JETON du lien). Ces routes sont permitAll côté config.
 * ============================================================================
 */
@RestController
@CrossOrigin(origins = {"http://localhost:4200", "http://localhost:3000"})
public class TestController {

    @Autowired private TechnicalTestService testService;
    @Autowired private UserRepository userRepository;

    /** Récupère le recruteur actuellement connecté (depuis le contexte JWT). */
    private User currentUser() {
        String email = SecurityContextHolder.getContext().getAuthentication().getName();
        return userRepository.findByEmail(email)
                .orElseThrow(() -> new RuntimeException("Utilisateur non trouvé"));
    }

    // ===== RECRUTEUR : envoyer un test à un candidat =====
    @PostMapping("/cv-analysis/results/{id}/send-test")
    @PreAuthorize("hasAnyRole('ADMIN_RH','RECRUITER','USER')")
    public ResponseEntity<?> sendTest(@PathVariable Long id) {
        try {
            TechnicalTest t = testService.generateAndSend(id, currentUser());
            return ResponseEntity.ok(Map.of(
                "message", "Test envoyé à " + t.getCandidateEmail(),
                "token", t.getToken()));
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(Map.of("error", e.getMessage()));
        }
    }

    // ===== RECRUTEUR : tableau de bord des tests =====
    @GetMapping("/tests")
    @PreAuthorize("hasAnyRole('ADMIN_RH','RECRUITER','USER')")
    public ResponseEntity<?> listTests() {
        try {
            return ResponseEntity.ok(testService.listTests());
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(Map.of("error", e.getMessage()));
        }
    }

    // ===== PUBLIC : le candidat ouvre son test via le jeton =====
    @GetMapping("/public/test/{token}")
    public ResponseEntity<?> getPublicTest(@PathVariable String token) {
        try {
            return ResponseEntity.ok(testService.getPublicTest(token));
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.NOT_FOUND).body(Map.of("error", e.getMessage()));
        }
    }

    // ===== PUBLIC : le candidat soumet ses réponses =====
    @PostMapping("/public/test/{token}/submit")
    public ResponseEntity<?> submitTest(@PathVariable String token, @RequestBody Map<String, Object> body) {
        try {
            @SuppressWarnings("unchecked")
            List<Integer> answers = (List<Integer>) body.get("answers");
            return ResponseEntity.ok(testService.submitTest(token, answers));
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(Map.of("error", e.getMessage()));
        }
    }
}
