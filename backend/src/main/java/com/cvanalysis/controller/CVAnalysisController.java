package com.cvanalysis.controller;

import com.cvanalysis.dto.CVAnalysisResponse;
import com.cvanalysis.entity.CVAnalysisResult;
import com.cvanalysis.exception.InvalidCvDocumentException;
import com.cvanalysis.service.CVAnalysisService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.data.domain.Page;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.io.IOException;
import java.util.List;
import java.util.Map;

/**
 * ============================================================================
 *  CVAnalysisController — la "porte d'entrée" HTTP des fonctionnalités CV.
 * ----------------------------------------------------------------------------
 *  @RestController        : chaque méthode renvoie directement du JSON.
 *  @RequestMapping        : toutes les routes commencent par /cv-analysis.
 *  @PreAuthorize          : contrôle d'accès par rôle, méthode par méthode.
 *  @CrossOrigin           : autorise le frontend Angular à appeler ces routes.
 *  ResponseEntity         : permet de maîtriser le code HTTP (200, 400, 500...).
 *
 *  Le contrôleur reste MINCE : il valide/route la requête et délègue toute la
 *  logique métier au CVAnalysisService (bonne séparation des responsabilités).
 *  Chaque méthode est entourée d'un try/catch pour renvoyer une erreur propre.
 * ============================================================================
 */
@RestController
@RequestMapping("/cv-analysis")
@CrossOrigin(origins = {"http://localhost:4200", "http://localhost:3000"})
public class CVAnalysisController {

    @Autowired
    private CVAnalysisService cvAnalysisService;

    // =========================================================================
    // UPLOAD & ANALYSE
    // =========================================================================
    @PostMapping("/analyze")
    @PreAuthorize("isAuthenticated()")
    public ResponseEntity<?> uploadAndAnalyzeCV(
            @RequestParam("file") MultipartFile file,
            @RequestParam(value = "requirements", required = false) String requirements) {
        try {
            CVAnalysisResponse response = cvAnalysisService.uploadAndAnalyzeCV(file, requirements);
            return ResponseEntity.ok(response);
        } catch (InvalidCvDocumentException e) {
            return ResponseEntity.status(HttpStatus.BAD_REQUEST)
                    .body(Map.of(
                            "message", e.getMessage(),
                            "reason", "invalid_cv_document"
                    ));
        } catch (IOException e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).build();
        } catch (RuntimeException e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body(Map.of("message", e.getMessage()));
        }
    }

    // =========================================================================
    // RÉSULTATS — liste simple (compatibilité)
    // =========================================================================
    @GetMapping("/results")
    @PreAuthorize("hasAnyRole('ADMIN_RH', 'RECRUITER', 'USER')")
    public ResponseEntity<?> getAnalysisResults() {
        try {
            List<CVAnalysisResult> results = cvAnalysisService.getAnalysisResults();
            return ResponseEntity.ok(results);
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body(Map.of("error", e.getMessage()));
        }
    }

    // =========================================================================
    // RÉSULTATS — paginés + recherche
    // =========================================================================
    @GetMapping("/results/page")
    @PreAuthorize("hasAnyRole('ADMIN_RH', 'RECRUITER', 'USER')")
    public ResponseEntity<?> getResultsPaged(
            @RequestParam(defaultValue = "")  String search,
            @RequestParam(defaultValue = "0")  int page,
            @RequestParam(defaultValue = "10") int size) {
        try {
            Page<CVAnalysisResult> paged = cvAnalysisService.getAnalysisResultsPaged(search, page, size);
            return ResponseEntity.ok(paged);
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body(Map.of("error", e.getMessage()));
        }
    }

    // =========================================================================
    // RÉSULTAT PAR ID
    // =========================================================================
    @GetMapping("/results/{id}")
    @PreAuthorize("hasAnyRole('ADMIN_RH', 'RECRUITER', 'USER')")
    public ResponseEntity<?> getAnalysisResult(@PathVariable Long id) {
        try {
            return cvAnalysisService.getAnalysisResultById(id)
                    .map(ResponseEntity::ok)
                    .orElse(ResponseEntity.notFound().build());
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).build();
        }
    }

    // =========================================================================
    // DÉTAIL CANDIDAT (alias)
    // =========================================================================
    @GetMapping("/candidates/{id}")
    @PreAuthorize("hasAnyRole('ADMIN_RH', 'RECRUITER', 'USER')")
    public ResponseEntity<?> getCandidateDetail(@PathVariable Long id) {
        try {
            return cvAnalysisService.getAnalysisResultById(id)
                    .map(ResponseEntity::ok)
                    .orElse(ResponseEntity.notFound().build());
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).build();
        }
    }

    // =========================================================================
    // CORBEILLE (soft-delete)
    // =========================================================================
    @DeleteMapping("/results/{id}")
    @PreAuthorize("hasAnyRole('ADMIN_RH', 'RECRUITER', 'USER')")
    public ResponseEntity<?> moveToTrash(@PathVariable Long id) {
        try {
            cvAnalysisService.moveToTrash(id);
            return ResponseEntity.ok(Map.of("message", "Candidat déplacé vers la corbeille"));
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(Map.of("error", e.getMessage()));
        }
    }

    @GetMapping("/trash")
    @PreAuthorize("hasAnyRole('ADMIN_RH', 'RECRUITER', 'USER')")
    public ResponseEntity<?> getTrash() {
        try {
            return ResponseEntity.ok(cvAnalysisService.getTrash());
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).body(Map.of("error", e.getMessage()));
        }
    }

    @PostMapping("/trash/{id}/restore")
    @PreAuthorize("hasAnyRole('ADMIN_RH', 'RECRUITER', 'USER')")
    public ResponseEntity<?> restoreFromTrash(@PathVariable Long id) {
        try {
            cvAnalysisService.restoreFromTrash(id);
            return ResponseEntity.ok(Map.of("message", "Candidat restauré"));
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(Map.of("error", e.getMessage()));
        }
    }

    @DeleteMapping("/trash/{id}")
    @PreAuthorize("hasAnyRole('ADMIN_RH', 'RECRUITER', 'USER')")
    public ResponseEntity<?> deletePermanently(@PathVariable Long id) {
        try {
            cvAnalysisService.deletePermanently(id);
            return ResponseEntity.ok(Map.of("message", "Candidat supprimé définitivement"));
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.BAD_REQUEST).body(Map.of("error", e.getMessage()));
        }
    }

    // =========================================================================
    // TALENT SEARCH (RAG) — recherche sémantique en langage naturel
    // =========================================================================
    @PostMapping("/talent-search")
    @PreAuthorize("hasAnyRole('ADMIN_RH', 'RECRUITER', 'USER')")
    public ResponseEntity<?> talentSearch(@RequestBody Map<String, Object> body) {
        try {
            String query = body.get("query") != null ? body.get("query").toString() : "";
            int topK = body.get("topK") != null ? ((Number) body.get("topK")).intValue() : 50;
            if (query.isBlank()) {
                return ResponseEntity.badRequest().body(Map.of("error", "Requête vide"));
            }
            List<CVAnalysisResult> results = cvAnalysisService.talentSearch(query, topK);
            return ResponseEntity.ok(results);
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body(Map.of("error", e.getMessage()));
        }
    }

    // =========================================================================
    // TOP 10
    // =========================================================================
    @GetMapping("/top")
    @PreAuthorize("hasAnyRole('ADMIN_RH', 'RECRUITER', 'USER')")
    public ResponseEntity<?> getTopCandidates() {
        try {
            List<CVAnalysisResult> top = cvAnalysisService.getTopCandidates();
            return ResponseEntity.ok(top);
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR).build();
        }
    }

    // =========================================================================
    // STATISTIQUES KPI
    // =========================================================================
    @GetMapping("/statistics")
    @PreAuthorize("hasAnyRole('ADMIN_RH', 'RECRUITER', 'USER')")
    public ResponseEntity<?> getStatistics() {
        try {
            Map<String, Object> stats = cvAnalysisService.getStatistics();
            return ResponseEntity.ok(stats);
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body(Map.of("error", e.getMessage()));
        }
    }

    // =========================================================================
    // TÉLÉCHARGER RAPPORT PDF
    // =========================================================================
    @GetMapping("/results/{id}/report")
    @PreAuthorize("hasAnyRole('ADMIN_RH', 'RECRUITER', 'USER')")
    public ResponseEntity<?> downloadReport(@PathVariable Long id) {
        try {
            byte[] pdfBytes = cvAnalysisService.generatePDFReport(id);
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_PDF);
            headers.setContentDispositionFormData("attachment",
                    "rapport_cv_" + id + ".pdf");
            headers.setContentLength(pdfBytes.length);
            return new ResponseEntity<>(pdfBytes, headers, HttpStatus.OK);
        } catch (RuntimeException e) {
            return ResponseEntity.notFound().build();
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body(Map.of("error", "Erreur génération PDF: " + e.getMessage()));
        }
    }

    // =========================================================================
    // EXPORTER CSV
    // =========================================================================
    @GetMapping("/results/export/csv")
    @PreAuthorize("hasAnyRole('ADMIN_RH', 'RECRUITER', 'USER')")
    public ResponseEntity<?> exportToCSV() {
        try {
            byte[] csvBytes = cvAnalysisService.exportAllToCSV();
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.parseMediaType("text/csv; charset=UTF-8"));
            headers.setContentDispositionFormData("attachment",
                    "skillmatch_resultats.csv");
            headers.setContentLength(csvBytes.length);
            return new ResponseEntity<>(csvBytes, headers, HttpStatus.OK);
        } catch (Exception e) {
            return ResponseEntity.status(HttpStatus.INTERNAL_SERVER_ERROR)
                    .body(Map.of("error", "Erreur export CSV: " + e.getMessage()));
        }
    }
}
