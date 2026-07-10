package com.cvanalysis.service;

import com.cvanalysis.dto.CVAnalysisResponse;
import com.cvanalysis.entity.CVAnalysisResult;
import com.cvanalysis.entity.User;
import com.cvanalysis.exception.InvalidCvDocumentException;
import com.cvanalysis.repository.CVAnalysisResultRepository;
import com.cvanalysis.repository.UserRepository;
import com.fasterxml.jackson.core.JsonProcessingException;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.JsonNode;
import com.lowagie.text.Document;
import com.lowagie.text.DocumentException;
import com.lowagie.text.Element;
import com.lowagie.text.Font;
import com.lowagie.text.PageSize;
import com.lowagie.text.Paragraph;
import com.lowagie.text.Phrase;
import com.lowagie.text.pdf.BaseFont;
import com.lowagie.text.pdf.PdfContentByte;
import com.lowagie.text.pdf.PdfPageEventHelper;
import com.lowagie.text.pdf.PdfPCell;
import com.lowagie.text.pdf.PdfPTable;
import com.lowagie.text.pdf.PdfWriter;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.core.io.ByteArrayResource;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.stereotype.Service;
import org.springframework.util.LinkedMultiValueMap;
import org.springframework.util.MultiValueMap;
import org.springframework.web.client.HttpClientErrorException;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.multipart.MultipartFile;

import java.awt.Color;
import java.io.*;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.time.format.DateTimeFormatter;
import java.util.*;

/**
 * ============================================================================
 *  CVAnalysisService — service CENTRAL côté Java (orchestrateur).
 * ----------------------------------------------------------------------------
 *  C'est le "chef d'orchestre" qui relie tout :
 *    - reçoit le CV uploadé, appelle le microservice IA (FastAPI) pour l'analyse,
 *      puis PERSISTE le résultat en base (cv_analysis_results) ;
 *    - lecture des résultats, statistiques, analytics par recruteur ;
 *    - corbeille (soft-delete) avec purge automatique ;
 *    - Talent Search (RAG) en relayant la requête vers FastAPI ;
 *    - export CSV et génération de rapport PDF.
 *
 *  Communication inter-services : RestTemplate (HTTP) vers FastAPI.
 *  (Re)sérialisation JSON : Jackson ObjectMapper.
 * ============================================================================
 */
@Service
public class CVAnalysisService {

    @Autowired
    private CVAnalysisResultRepository analysisResultRepository;

    @Autowired
    private UserRepository userRepository;

    @Autowired
    private RestTemplate restTemplate;

    /** Service du test technique (pour l'envoi AUTOMATIQUE si bon score). */
    @Autowired
    private TechnicalTestService technicalTestService;

    /** Seuil de score à partir duquel un test est envoyé automatiquement. */
    private static final double AUTO_TEST_THRESHOLD = 75.0;

    /** Interrupteur : envoi AUTOMATIQUE du test désactivé pour le moment.
     *  (Le recruteur peut toujours envoyer un test MANUELLEMENT via le bouton.)
     *  Repasser à true pour réactiver l'envoi auto au-dessus du seuil. */
    private static final boolean AUTO_TEST_ENABLED = false;

    private final ObjectMapper objectMapper = new ObjectMapper();
    private static final String UPLOADS_DIR = "uploads/";
    private static final DateTimeFormatter DATE_FMT = DateTimeFormatter.ofPattern("dd/MM/yyyy HH:mm");

    @Value("${fastapi.url:http://localhost:8000}")
    private String fastApiUrl;

    // =========================================================================
    // UPLOAD & ANALYSE
    // =========================================================================
    public CVAnalysisResponse uploadAndAnalyzeCV(MultipartFile file, String requirements) throws IOException {
        // 1) Identifier le recruteur connecté (depuis le contexte de sécurité JWT).
        String userEmail = SecurityContextHolder.getContext().getAuthentication().getName();
        User user = userRepository.findByEmail(userEmail)
                .orElseThrow(() -> new RuntimeException("Utilisateur non trouvé"));

        // 2) Sauvegarder le fichier sur disque avec un nom unique (UUID) pour
        //    éviter les collisions entre deux CV du même nom.
        String fileName = UUID.randomUUID() + "_" + file.getOriginalFilename();
        Path uploadPath = Paths.get(UPLOADS_DIR);
        Files.createDirectories(uploadPath);
        Path filePath = uploadPath.resolve(fileName);
        Files.write(filePath, file.getBytes());

        // 3) Déléguer l'ANALYSE IA au microservice Python (FastAPI).
        CVAnalysisResponse analysisResponse = callFastAPIForAnalysis(file, requirements);

        // 4) Mapper la réponse vers l'entité persistée en base.
        CVAnalysisResult result = new CVAnalysisResult();
        result.setUser(user);
        result.setCandidateName(analysisResponse.getCandidateName());
        result.setEmail(analysisResponse.getEmail());
        result.setPhone(analysisResponse.getPhone());
        result.setCvPath(filePath.toString());
        result.setOverallScore(analysisResponse.getScores().getOverallScore());
        result.setEducationScore(analysisResponse.getScores().getEducationScore());
        result.setExperienceScore(analysisResponse.getScores().getExperienceScore());
        result.setSkillsScore(analysisResponse.getScores().getSkillsScore());
        result.setSoftSkillsScore(analysisResponse.getScores().getSoftSkillsScore());
        result.setMatchPercentage(analysisResponse.getMatchPercentage());
        result.setCvFullText(analysisResponse.getFullText());

        // Les structures complexes (détail d'analyse, recommandations) sont
        // stockées en JSON (colonnes TEXT) -> sérialisation par Jackson.
        try {
            result.setAnalysisData(objectMapper.writeValueAsString(analysisResponse.getAnalysis()));
            result.setRecommendations(objectMapper.writeValueAsString(analysisResponse.getRecommendations()));
        } catch (JsonProcessingException e) {
            throw new RuntimeException("Erreur sérialisation données", e);
        }

        // 5) Persister en base, puis renvoyer la réponse enrichie de l'id/date.
        analysisResultRepository.save(result);
        analysisResponse.setId(result.getId().toString());
        analysisResponse.setTimestamp(result.getCreatedAt().toString());

        // 6) Envoi AUTOMATIQUE d'un test technique si le score est élevé (>= 75).
        //    En try/catch : un échec d'envoi ne doit jamais casser l'analyse.
        try {
            double score = result.getOverallScore() != null ? result.getOverallScore() : 0.0;
            if (AUTO_TEST_ENABLED && score >= AUTO_TEST_THRESHOLD
                    && result.getEmail() != null && !result.getEmail().isBlank()) {
                technicalTestService.generateAndSend(result.getId(), user);
            }
        } catch (Exception e) {
            System.err.println("[AutoTest] Envoi automatique impossible : " + e.getMessage());
        }
        return analysisResponse;
    }

    /**
     * Appelle le microservice FastAPI (/score) en multipart (fichier + exigence)
     * et désérialise sa réponse JSON en CVAnalysisResponse. Gère proprement le
     * cas "ce n'est pas un CV" (400) en levant une exception métier dédiée.
     */
    private CVAnalysisResponse callFastAPIForAnalysis(MultipartFile file, String requirements) {
        try {
            // On enveloppe les octets du fichier pour les envoyer en multipart.
            ByteArrayResource fileAsResource = new ByteArrayResource(file.getBytes()) {
                @Override
                public String getFilename() { return file.getOriginalFilename(); }
            };

            MultiValueMap<String, Object> body = new LinkedMultiValueMap<>();
            body.add("file", fileAsResource);
            if (requirements != null) body.add("requirements", requirements);

            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.MULTIPART_FORM_DATA);

            String url = fastApiUrl.endsWith("/") ? fastApiUrl + "score" : fastApiUrl + "/score";
            CVAnalysisResponse response = restTemplate.postForObject(
                    url, new HttpEntity<>(body, headers), CVAnalysisResponse.class);

            if (response != null) return response;
            throw new InvalidCvDocumentException("Le fichier fourni n'est pas un CV valide.");
        } catch (HttpClientErrorException.BadRequest e) {
            String message = extractFastApiErrorMessage(e.getResponseBodyAsString());
            throw new InvalidCvDocumentException(message);
        } catch (Exception e) {
            throw new RuntimeException("Erreur appel FastAPI: " + e.getMessage(), e);
        }
    }

    /** Extrait un message d'erreur lisible depuis le corps JSON renvoyé par FastAPI
     *  (FastAPI met souvent l'info utile dans "detail" ou "detail.message"). */
    private String extractFastApiErrorMessage(String body) {
        if (body == null || body.isBlank()) {
            return "Le fichier fourni n'est pas un CV valide.";
        }

        try {
            JsonNode root = objectMapper.readTree(body);
            JsonNode detail = root.path("detail");
            if (detail.isTextual()) {
                return detail.asText();
            }
            if (detail.isObject()) {
                JsonNode message = detail.path("message");
                if (message.isTextual()) {
                    return message.asText();
                }
            }
            JsonNode message = root.path("message");
            if (message.isTextual()) {
                return message.asText();
            }
        } catch (Exception ignored) {
        }

        return body;
    }

    // =========================================================================
    // LECTURE
    // =========================================================================
    /** Liste les candidats ACTIFS (hors corbeille) du recruteur connecté. */
    public List<CVAnalysisResult> getAnalysisResults() {
        String userEmail = SecurityContextHolder.getContext().getAuthentication().getName();
        User user = userRepository.findByEmail(userEmail)
                .orElseThrow(() -> new RuntimeException("Utilisateur non trouvé"));
        return analysisResultRepository.findByUserAndDeletedAtIsNullOrderByCreatedAtDesc(user);
    }

    // =========================================================================
    // CORBEILLE (soft-delete) — rétention 30 jours puis purge auto
    // =========================================================================
    private static final int TRASH_RETENTION_DAYS = 30;

    private User currentUser() {
        String email = SecurityContextHolder.getContext().getAuthentication().getName();
        return userRepository.findByEmail(email)
                .orElseThrow(() -> new RuntimeException("Utilisateur non trouvé"));
    }

    /** Mettre un candidat à la corbeille (réservé au propriétaire). */
    public void moveToTrash(Long id) {
        User user = currentUser();
        CVAnalysisResult r = analysisResultRepository.findById(id)
                .orElseThrow(() -> new RuntimeException("Candidat introuvable"));
        if (r.getUser() == null || !r.getUser().getId().equals(user.getId())) {
            throw new RuntimeException("Action non autorisée sur ce candidat.");
        }
        r.setDeletedAt(java.time.LocalDateTime.now());
        analysisResultRepository.save(r);
    }

    /** Liste de la corbeille du recruteur courant + jours restants avant purge. */
    public List<Map<String, Object>> getTrash() {
        User user = currentUser();
        List<CVAnalysisResult> deleted = analysisResultRepository
                .findByUserAndDeletedAtIsNotNullOrderByDeletedAtDesc(user);
        List<Map<String, Object>> out = new ArrayList<>();
        for (CVAnalysisResult r : deleted) {
            long daysInTrash = java.time.Duration.between(r.getDeletedAt(), java.time.LocalDateTime.now()).toDays();
            long daysLeft = Math.max(0, TRASH_RETENTION_DAYS - daysInTrash);
            Map<String, Object> m = new LinkedHashMap<>();
            m.put("id", r.getId());
            m.put("candidateName", r.getCandidateName());
            m.put("email", r.getEmail());
            m.put("overallScore", orZero(r.getOverallScore()));
            m.put("deletedAt", r.getDeletedAt().format(DATE_FMT));
            m.put("daysLeft", daysLeft);
            out.add(m);
        }
        return out;
    }

    /** Restaurer un candidat depuis la corbeille. */
    public void restoreFromTrash(Long id) {
        User user = currentUser();
        CVAnalysisResult r = analysisResultRepository.findById(id)
                .orElseThrow(() -> new RuntimeException("Candidat introuvable"));
        if (r.getUser() == null || !r.getUser().getId().equals(user.getId())) {
            throw new RuntimeException("Action non autorisée.");
        }
        r.setDeletedAt(null);
        analysisResultRepository.save(r);
    }

    /** Suppression définitive immédiate (depuis la corbeille). */
    public void deletePermanently(Long id) {
        User user = currentUser();
        CVAnalysisResult r = analysisResultRepository.findById(id)
                .orElseThrow(() -> new RuntimeException("Candidat introuvable"));
        if (r.getUser() == null || !r.getUser().getId().equals(user.getId())) {
            throw new RuntimeException("Action non autorisée.");
        }
        analysisResultRepository.delete(r);
    }

    /** Purge automatique quotidienne : supprime définitivement après 30 jours. */
    @org.springframework.scheduling.annotation.Scheduled(cron = "0 0 3 * * *") // tous les jours à 3h
    public void purgeOldTrash() {
        java.time.LocalDateTime threshold = java.time.LocalDateTime.now().minusDays(TRASH_RETENTION_DAYS);
        List<CVAnalysisResult> toPurge = analysisResultRepository
                .findByDeletedAtIsNotNullAndDeletedAtBefore(threshold);
        if (!toPurge.isEmpty()) {
            analysisResultRepository.deleteAll(toPurge);
            System.out.println("[Corbeille] Purge automatique : " + toPurge.size() + " candidat(s) supprimé(s) définitivement.");
        }
    }

    public Page<CVAnalysisResult> getAnalysisResultsPaged(String search, int page, int size) {
        Pageable pageable = PageRequest.of(page, size);
        return analysisResultRepository.findAllWithSearch(
                (search != null && !search.isBlank()) ? search : null, pageable);
    }

    public Optional<CVAnalysisResult> getAnalysisResultById(Long id) {
        return analysisResultRepository.findById(id);
    }

    public List<CVAnalysisResult> getTopCandidates() {
        return analysisResultRepository.findTop10ByDeletedAtIsNullOrderByOverallScoreDesc();
    }

    // =========================================================================
    // TALENT SEARCH (RAG) — recherche sémantique sur le vivier
    // =========================================================================
    /** Seuil minimal de pertinence (%) pour qu'un candidat soit affiché. */
    private static final double RELEVANCE_THRESHOLD = 35.0;

    /**
     * Talent Search : classe le vivier par pertinence vis-à-vis d'une requête.
     * Étapes : dédup par e-mail -> construction des profils texte -> appel
     * FastAPI (/talent-search) -> filtrage au seuil de pertinence -> tri.
     */
    public List<CVAnalysisResult> talentSearch(String query, int topK) {
        List<CVAnalysisResult> all = analysisResultRepository.findByDeletedAtIsNullOrderByCreatedAtDesc();
        if (query == null || query.isBlank() || all.isEmpty()) {
            return List.of();
        }

        // 0) Dédupliquer par email : ne garder que l'analyse la plus récente
        //    (la liste est triée par date décroissante => on garde la 1re vue).
        LinkedHashMap<String, CVAnalysisResult> uniqueByEmail = new LinkedHashMap<>();
        for (CVAnalysisResult r : all) {
            String key = (r.getEmail() != null && !r.getEmail().isBlank())
                    ? r.getEmail().toLowerCase()
                    : "id-" + r.getId();
            uniqueByEmail.putIfAbsent(key, r);
        }
        List<CVAnalysisResult> deduped = new ArrayList<>(uniqueByEmail.values());

        // 1) Construire les profils texte pour chaque candidat
        List<Map<String, String>> candidates = new ArrayList<>();
        for (CVAnalysisResult r : deduped) {
            candidates.add(Map.of(
                    "id", String.valueOf(r.getId()),
                    "text", buildProfileText(r)
            ));
        }

        // 2) Appeler FastAPI /talent-search
        Map<String, Double> scoreById = new HashMap<>();
        Map<String, Double> semanticById = new HashMap<>();
        try {
            Map<String, Object> body = new HashMap<>();
            body.put("query", query);
            body.put("candidates", candidates);
            body.put("top_k", topK);

            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);

            String url = fastApiUrl.endsWith("/") ? fastApiUrl + "talent-search" : fastApiUrl + "/talent-search";
            @SuppressWarnings("unchecked")
            Map<String, Object> resp = restTemplate.postForObject(url, new HttpEntity<>(body, headers), Map.class);

            if (resp != null && resp.get("results") instanceof List<?> results) {
                for (Object item : results) {
                    if (item instanceof Map<?, ?> m) {
                        String id = String.valueOf(m.get("id"));
                        double score = m.get("score") != null ? ((Number) m.get("score")).doubleValue() : 0.0;
                        double sem = m.get("semantic") != null ? ((Number) m.get("semantic")).doubleValue() : 0.0;
                        scoreById.put(id, score);
                        semanticById.put(id, sem);
                    }
                }
            }
        } catch (Exception e) {
            throw new RuntimeException("Erreur Talent Search (FastAPI): " + e.getMessage(), e);
        }

        // 3) Annoter + filtrer (seuil 35%) + trier par pertinence décroissante
        List<CVAnalysisResult> ranked = new ArrayList<>();
        for (CVAnalysisResult r : deduped) {
            String id = String.valueOf(r.getId());
            if (scoreById.containsKey(id)) {
                double pct = Math.round(scoreById.get(id) * 1000.0) / 10.0; // en %
                if (pct >= RELEVANCE_THRESHOLD) {           // ne garder que les pertinents
                    r.setRelevanceScore(pct);
                    r.setSemanticScore(Math.round(semanticById.getOrDefault(id, 0.0) * 1000.0) / 10.0);
                    ranked.add(r);
                }
            }
        }
        ranked.sort((a, b) -> Double.compare(
                b.getRelevanceScore() != null ? b.getRelevanceScore() : 0.0,
                a.getRelevanceScore() != null ? a.getRelevanceScore() : 0.0));
        return ranked;
    }

    /** Construit un texte de profil riche à partir des données d'analyse stockées. */
    private String buildProfileText(CVAnalysisResult r) {
        StringBuilder sb = new StringBuilder();
        if (r.getCandidateName() != null) sb.append(r.getCandidateName()).append(". ");

        try {
            JsonNode a = objectMapper.readTree(
                    r.getAnalysisData() != null ? r.getAnalysisData() : "{}");
            appendText(sb, a.path("summary"));
            appendArray(sb, a.path("skills"));
            appendArray(sb, a.path("softSkills"));
            appendArray(sb, a.path("languages"));
            appendArray(sb, a.path("certifications"));
            appendArray(sb, a.path("projects"));
            appendText(sb, a.path("specialityCv"));
            appendText(sb, a.path("location"));

            JsonNode exp = a.path("experience");
            if (exp.isArray()) {
                for (JsonNode e : exp) {
                    appendText(sb, e.path("title"));
                    appendText(sb, e.path("company"));
                    appendText(sb, e.path("description"));
                }
            }
            JsonNode edu = a.path("education");
            if (edu.isArray()) {
                for (JsonNode e : edu) {
                    appendText(sb, e.path("degree"));
                    appendText(sb, e.path("field"));
                    appendText(sb, e.path("institution"));
                }
            }

            // Texte intégral du CV (capte TOUT : niveaux de langue, certifs, etc.).
            // Repli sur l'aperçu pour les candidats analysés avant cette fonctionnalité.
            if (r.getCvFullText() != null && !r.getCvFullText().isBlank()) {
                sb.append(" ").append(r.getCvFullText());
            } else {
                appendText(sb, a.path("extractedTextPreview"));
            }
        } catch (Exception ignored) {
        }
        return sb.toString().trim();
    }

    private void appendText(StringBuilder sb, JsonNode node) {
        if (node != null && node.isTextual() && !node.asText().isBlank()) {
            sb.append(node.asText()).append(". ");
        }
    }

    private void appendArray(StringBuilder sb, JsonNode node) {
        if (node != null && node.isArray()) {
            for (JsonNode item : node) {
                if (item.isTextual() && !item.asText().isBlank()) {
                    sb.append(item.asText()).append(", ");
                }
            }
        }
    }

    // =========================================================================
    // ANALYTICS ADMIN — vue par recruteur + tous les candidats
    // =========================================================================

    /** Vue d'ensemble : stats globales + agrégats par recruteur. */
    public Map<String, Object> getRecruitersAnalytics() {
        List<CVAnalysisResult> all = analysisResultRepository.findByDeletedAtIsNullOrderByCreatedAtDesc();

        // On parcourt toutes les analyses et on les REGROUPE par recruteur,
        // en cumulant le total, la somme des scores et la répartition par niveau
        // (excellent/fort/modéré/faible) — calcul d'agrégats "à la main".
        // Agrégation par recruteur (clé = id utilisateur)
        Map<Long, Map<String, Object>> byRecruiter = new LinkedHashMap<>();
        for (CVAnalysisResult r : all) {
            User u = r.getUser();
            if (u == null) continue;
            Long uid = u.getId();
            Map<String, Object> agg = byRecruiter.computeIfAbsent(uid, k -> {
                Map<String, Object> m = new LinkedHashMap<>();
                m.put("recruiterId", uid);
                m.put("recruiterName", u.getName());
                m.put("recruiterEmail", u.getEmail());
                m.put("role", u.getRole().name());
                m.put("totalAnalyses", 0);
                m.put("sumScore", 0.0);
                m.put("countExcellent", 0);
                m.put("countStrong", 0);
                m.put("countModerate", 0);
                m.put("countWeak", 0);
                m.put("lastActivity", "");
                return m;
            });

            double score = orZero(r.getOverallScore());
            agg.put("totalAnalyses", (int) agg.get("totalAnalyses") + 1);
            agg.put("sumScore", (double) agg.get("sumScore") + score);
            if (score >= 85)      agg.put("countExcellent", (int) agg.get("countExcellent") + 1);
            else if (score >= 70) agg.put("countStrong",    (int) agg.get("countStrong") + 1);
            else if (score >= 55) agg.put("countModerate",  (int) agg.get("countModerate") + 1);
            else                  agg.put("countWeak",      (int) agg.get("countWeak") + 1);

            String created = r.getCreatedAt() != null ? r.getCreatedAt().format(DATE_FMT) : "";
            if (((String) agg.get("lastActivity")).isEmpty()) {
                agg.put("lastActivity", created); // la liste est triée desc => 1re vue = plus récente
            }
        }

        // Finaliser : moyenne par recruteur
        List<Map<String, Object>> recruiters = new ArrayList<>();
        for (Map<String, Object> agg : byRecruiter.values()) {
            int total = (int) agg.get("totalAnalyses");
            double sum = (double) agg.get("sumScore");
            agg.put("avgScore", total > 0 ? Math.round(sum / total * 10.0) / 10.0 : 0.0);
            agg.remove("sumScore");
            recruiters.add(agg);
        }
        // Trier par nombre d'analyses décroissant
        recruiters.sort((a, b) -> Integer.compare((int) b.get("totalAnalyses"), (int) a.get("totalAnalyses")));

        // Stats globales
        double avgGlobal = all.isEmpty() ? 0.0 :
                Math.round(all.stream().mapToDouble(r -> orZero(r.getOverallScore())).average().orElse(0.0) * 10.0) / 10.0;

        Map<String, Object> out = new LinkedHashMap<>();
        out.put("totalRecruiters", recruiters.size());
        out.put("totalAnalyses", all.size());
        out.put("averageScore", avgGlobal);
        out.put("recruiters", recruiters);
        return out;
    }

    /** Tous les candidats avec le recruteur qui les a traités (pour le tableau filtrable). */
    public List<Map<String, Object>> getAllCandidatesWithRecruiter() {
        List<CVAnalysisResult> all = analysisResultRepository.findByDeletedAtIsNullOrderByCreatedAtDesc();
        List<Map<String, Object>> out = new ArrayList<>();
        for (CVAnalysisResult r : all) {
            User u = r.getUser();
            double score = orZero(r.getOverallScore());
            Map<String, Object> m = new LinkedHashMap<>();
            m.put("id", r.getId());
            m.put("candidateName", r.getCandidateName());
            m.put("email", r.getEmail());
            m.put("overallScore", score);
            m.put("matchPercentage", orZero(r.getMatchPercentage()));
            m.put("educationScore", orZero(r.getEducationScore()));
            m.put("experienceScore", orZero(r.getExperienceScore()));
            m.put("skillsScore", orZero(r.getSkillsScore()));
            m.put("softSkillsScore", orZero(r.getSoftSkillsScore()));
            m.put("decision", decisionLabel(score));
            m.put("recruiterId", u != null ? u.getId() : null);
            m.put("recruiterName", u != null ? u.getName() : "—");
            m.put("recruiterEmail", u != null ? u.getEmail() : "—");
            m.put("createdAt", r.getCreatedAt() != null ? r.getCreatedAt().format(DATE_FMT) : "");
            m.put("createdAtIso", r.getCreatedAt() != null ? r.getCreatedAt().toString() : "");
            out.add(m);
        }
        return out;
    }

    private String decisionLabel(double score) {
        if (score >= 85) return "Excellent";
        if (score >= 70) return "Fort";
        if (score >= 55) return "Modéré";
        return "Faible";
    }

    // =========================================================================
    // STATISTIQUES
    // =========================================================================
    /** Statistiques globales du dashboard (total, moyenne, min/max, répartition). */
    public Map<String, Object> getStatistics() {
        Object[] raw = analysisResultRepository.getGlobalStats();
        Object[] row = (Object[]) raw[0];

        long total     = row[0] != null ? ((Number) row[0]).longValue() : 0L;
        double avgScore = row[1] != null ? Math.round(((Number) row[1]).doubleValue() * 10.0) / 10.0 : 0.0;
        double maxScore = row[2] != null ? ((Number) row[2]).doubleValue() : 0.0;
        double minScore = row[3] != null ? ((Number) row[3]).doubleValue() : 0.0;
        double avgMatch = row[4] != null ? Math.round(((Number) row[4]).doubleValue() * 10.0) / 10.0 : 0.0;

        Map<String, Object> stats = new LinkedHashMap<>();
        stats.put("totalCandidates", total);
        stats.put("averageScore", avgScore);
        stats.put("maxScore", maxScore);
        stats.put("minScore", minScore);
        stats.put("averageMatch", avgMatch);
        stats.put("countExcellent", analysisResultRepository.countExcellent());
        stats.put("countStrong",    analysisResultRepository.countStrong());
        stats.put("countModerate",  analysisResultRepository.countModerate());
        stats.put("countWeak",      analysisResultRepository.countWeak());
        return stats;
    }

    // =========================================================================
    // EXPORT CSV
    // =========================================================================
    /** Exporte tous les candidats actifs au format CSV (téléchargeable). */
    public byte[] exportAllToCSV() {
        List<CVAnalysisResult> results = analysisResultRepository.findByDeletedAtIsNullOrderByCreatedAtDesc();
        StringWriter sw = new StringWriter();
        PrintWriter pw = new PrintWriter(sw);

        // En-tête
        pw.println("ID,Nom Candidat,Email,Téléphone,Score Global,% Correspondance," +
                   "Score Éducation,Score Expérience,Score Compétences,Score Soft Skills,Date Analyse");

        DateTimeFormatter fmt = DateTimeFormatter.ofPattern("dd/MM/yyyy HH:mm");
        for (CVAnalysisResult r : results) {
            pw.printf("%d,\"%s\",\"%s\",\"%s\",%.1f,%.1f,%.1f,%.1f,%.1f,%.1f,\"%s\"%n",
                    r.getId(),
                    safe(r.getCandidateName()),
                    safe(r.getEmail()),
                    safe(r.getPhone()),
                    orZero(r.getOverallScore()),
                    orZero(r.getMatchPercentage()),
                    orZero(r.getEducationScore()),
                    orZero(r.getExperienceScore()),
                    orZero(r.getSkillsScore()),
                    orZero(r.getSoftSkillsScore()),
                    r.getCreatedAt() != null ? r.getCreatedAt().format(fmt) : ""
            );
        }
        pw.flush();
        return sw.toString().getBytes(java.nio.charset.StandardCharsets.UTF_8);
    }

    // =========================================================================
    // GÉNÉRATION RAPPORT PDF
    // =========================================================================
    /** Génère un rapport PDF mis en forme (en-tête, infos, scores, décision,
     *  recommandations) pour un candidat donné, via la librairie OpenPDF. */
    public byte[] generatePDFReport(Long id) throws Exception {
        CVAnalysisResult r = analysisResultRepository.findById(id)
                .orElseThrow(() -> new RuntimeException("Résultat non trouvé: " + id));

        ByteArrayOutputStream baos = new ByteArrayOutputStream();
        Document doc = new Document(PageSize.A4, 40, 40, 60, 60);
        PdfWriter writer = PdfWriter.getInstance(doc, baos);

        // En-tête/pied de page
        writer.setPageEvent(new PdfPageEventHelper() {
            @Override
            public void onEndPage(PdfWriter w, Document d) {
                try {
                    PdfContentByte cb = w.getDirectContent();
                    // Bande supérieure
                    cb.setColorFill(new Color(102, 126, 234));
                    cb.rectangle(0, PageSize.A4.getHeight() - 30, PageSize.A4.getWidth(), 30);
                    cb.fill();
                    // Texte entête
                    cb.beginText();
                    cb.setColorFill(Color.WHITE);
                    cb.setFontAndSize(BaseFont.createFont(BaseFont.HELVETICA_BOLD, BaseFont.CP1252, false), 11);
                    cb.showTextAligned(Element.ALIGN_CENTER, "SkillMatch AI — Rapport d'analyse",
                            PageSize.A4.getWidth() / 2, PageSize.A4.getHeight() - 18, 0);
                    cb.endText();
                    // Pied de page
                    cb.setColorFill(new Color(240, 240, 240));
                    cb.rectangle(0, 0, PageSize.A4.getWidth(), 25);
                    cb.fill();
                    cb.beginText();
                    cb.setColorFill(new Color(100, 100, 100));
                    cb.setFontAndSize(BaseFont.createFont(BaseFont.HELVETICA, BaseFont.CP1252, false), 9);
                    cb.showTextAligned(Element.ALIGN_LEFT,
                            "Généré le " + java.time.LocalDate.now().format(DateTimeFormatter.ofPattern("dd/MM/yyyy")),
                            40, 8, 0);
                    cb.showTextAligned(Element.ALIGN_RIGHT,
                            "Page " + w.getPageNumber(),
                            PageSize.A4.getWidth() - 40, 8, 0);
                    cb.endText();
                } catch (Exception ignored) {}
            }
        });

        doc.open();

        // Polices
        BaseFont bfBold   = BaseFont.createFont(BaseFont.HELVETICA_BOLD,   BaseFont.CP1252, false);
        BaseFont bfNormal = BaseFont.createFont(BaseFont.HELVETICA,        BaseFont.CP1252, false);
        Font titleFont    = new Font(bfBold,   22, Font.NORMAL, new Color(50, 50, 120));
        Font subFont      = new Font(bfNormal, 12, Font.NORMAL, new Color(100, 100, 100));
        Font h2Font       = new Font(bfBold,   14, Font.NORMAL, new Color(102, 126, 234));
        Font boldFont     = new Font(bfBold,   11, Font.NORMAL, Color.BLACK);
        Font normalFont   = new Font(bfNormal, 11, Font.NORMAL, Color.BLACK);
        Font smallGray    = new Font(bfNormal,  9, Font.NORMAL, new Color(130, 130, 130));

        // === TITRE PRINCIPAL ===
        doc.add(new Paragraph(" ", new Font(bfNormal, 6)));
        Paragraph title = new Paragraph("Rapport d'Analyse de CV", titleFont);
        title.setAlignment(Element.ALIGN_CENTER);
        doc.add(title);

        Paragraph subtitle = new Paragraph("SkillMatch AI — Déclitech Innovation", subFont);
        subtitle.setAlignment(Element.ALIGN_CENTER);
        doc.add(subtitle);
        doc.add(new Paragraph(" "));

        // Séparateur
        PdfContentByte cb2 = writer.getDirectContent();
        cb2.setColorStroke(new Color(102, 126, 234));
        cb2.setLineWidth(1.5f);
        cb2.moveTo(40, doc.top() - 80);
        cb2.lineTo(PageSize.A4.getWidth() - 40, doc.top() - 80);
        cb2.stroke();
        doc.add(new Paragraph(" "));

        // === INFORMATIONS CANDIDAT ===
        addSectionTitle(doc, "Informations du Candidat", h2Font);
        PdfPTable infoTable = new PdfPTable(2);
        infoTable.setWidthPercentage(100);
        infoTable.setSpacingBefore(8);
        addInfoRow(infoTable, "Nom complet",   safe(r.getCandidateName()), boldFont, normalFont);
        addInfoRow(infoTable, "Email",         safe(r.getEmail()),         boldFont, normalFont);
        addInfoRow(infoTable, "Téléphone",     safe(r.getPhone()),         boldFont, normalFont);
        addInfoRow(infoTable, "Date d'analyse",
                r.getCreatedAt() != null ? r.getCreatedAt().format(DATE_FMT) : "-",
                boldFont, normalFont);
        doc.add(infoTable);
        doc.add(new Paragraph(" "));

        // === SCORES ===
        addSectionTitle(doc, "Scores d'Analyse", h2Font);
        PdfPTable scoresTable = new PdfPTable(3);
        scoresTable.setWidthPercentage(100);
        scoresTable.setSpacingBefore(8);
        scoresTable.setWidths(new float[]{2, 1.5f, 1.5f});

        // En-tête tableau
        String[] headers = {"Critère", "Score obtenu", "Niveau"};
        for (String h : headers) {
            PdfPCell cell = new PdfPCell(new Phrase(h, new Font(bfBold, 10, Font.NORMAL, Color.WHITE)));
            cell.setBackgroundColor(new Color(102, 126, 234));
            cell.setPadding(8);
            cell.setBorderColor(new Color(90, 110, 200));
            scoresTable.addCell(cell);
        }

        addScoreRow(scoresTable, "Score Global",       orZero(r.getOverallScore()),    25.0, bfBold, bfNormal, true);
        addScoreRow(scoresTable, "% Correspondance",   orZero(r.getMatchPercentage()), 25.0, bfBold, bfNormal, false);
        addScoreRow(scoresTable, "Éducation",          orZero(r.getEducationScore()),  15.0, bfBold, bfNormal, false);
        addScoreRow(scoresTable, "Expérience",         orZero(r.getExperienceScore()), 15.0, bfBold, bfNormal, false);
        addScoreRow(scoresTable, "Compétences tech.",  orZero(r.getSkillsScore()),     25.0, bfBold, bfNormal, false);
        addScoreRow(scoresTable, "Soft Skills",        orZero(r.getSoftSkillsScore()), 10.0, bfBold, bfNormal, false);
        doc.add(scoresTable);
        doc.add(new Paragraph(" "));

        // === DÉCISION IA ===
        double overall = orZero(r.getOverallScore());
        String decision, color;
        if (overall >= 85)      { decision = "EXCELLENT — Profil très recommandé";      color = "vert"; }
        else if (overall >= 70) { decision = "BON — Profil recommandé";                 color = "bleu"; }
        else if (overall >= 55) { decision = "MODÉRÉ — À examiner";                     color = "orange"; }
        else                    { decision = "FAIBLE — Profil non recommandé";           color = "rouge"; }

        Color decisionColor = overall >= 85 ? new Color(40, 167, 69) :
                              overall >= 70 ? new Color(0, 123, 255) :
                              overall >= 55 ? new Color(255, 152, 0) :
                                             new Color(220, 53, 69);

        addSectionTitle(doc, "Décision IA", h2Font);
        PdfPTable decisionTable = new PdfPTable(1);
        decisionTable.setWidthPercentage(100);
        PdfPCell decCell = new PdfPCell(new Phrase(decision, new Font(bfBold, 13, Font.NORMAL, Color.WHITE)));
        decCell.setBackgroundColor(decisionColor);
        decCell.setPadding(12);
        decCell.setHorizontalAlignment(Element.ALIGN_CENTER);
        decCell.setBorder(0);
        decisionTable.addCell(decCell);
        doc.add(decisionTable);
        doc.add(new Paragraph(" "));

        // === RECOMMANDATIONS ===
        try {
            List<?> recs = objectMapper.readValue(r.getRecommendations(), List.class);
            if (recs != null && !recs.isEmpty()) {
                addSectionTitle(doc, "Recommandations IA", h2Font);
                for (Object rec : recs) {
                    Paragraph p = new Paragraph("  • " + rec.toString(), normalFont);
                    p.setSpacingBefore(3);
                    doc.add(p);
                }
                doc.add(new Paragraph(" "));
            }
        } catch (Exception ignored) {}

        // === PIED DE RAPPORT ===
        doc.add(new Paragraph(" "));
        Paragraph footer = new Paragraph(
                "Ce rapport a été généré automatiquement par SkillMatch AI — Déclitech Innovation",
                smallGray);
        footer.setAlignment(Element.ALIGN_CENTER);
        doc.add(footer);

        doc.close();
        return baos.toByteArray();
    }

    // =========================================================================
    // HELPERS PDF
    // =========================================================================
    private void addSectionTitle(Document doc, String text, Font font) throws DocumentException {
        Paragraph p = new Paragraph(text, font);
        p.setSpacingBefore(8);
        p.setSpacingAfter(4);
        doc.add(p);
    }

    private void addInfoRow(PdfPTable table, String label, String value, Font bold, Font normal) {
        PdfPCell lCell = new PdfPCell(new Phrase(label, bold));
        lCell.setBackgroundColor(new Color(248, 249, 250));
        lCell.setPadding(7);
        lCell.setBorderColor(new Color(220, 220, 220));

        PdfPCell vCell = new PdfPCell(new Phrase(value, normal));
        vCell.setPadding(7);
        vCell.setBorderColor(new Color(220, 220, 220));

        table.addCell(lCell);
        table.addCell(vCell);
    }

    private void addScoreRow(PdfPTable table, String label, double score, double max,
                              BaseFont bfBold, BaseFont bfNormal, boolean highlight) {
        Color bg = highlight ? new Color(240, 244, 255) : Color.WHITE;
        Color scoreColor = score >= (max * 0.85) ? new Color(40, 167, 69) :
                           score >= (max * 0.6)  ? new Color(255, 152, 0) :
                                                   new Color(220, 53, 69);

        String level = score >= (max * 0.85) ? "Excellent" :
                       score >= (max * 0.6)  ? "Modéré"   : "Faible";

        Font lFont = new Font(highlight ? bfBold : bfNormal, 10, Font.NORMAL, Color.BLACK);
        PdfPCell c1 = new PdfPCell(new Phrase(label, lFont));
        c1.setBackgroundColor(bg); c1.setPadding(7); c1.setBorderColor(new Color(220, 220, 220));

        PdfPCell c2 = new PdfPCell(new Phrase(String.format("%.1f", score),
                new Font(bfBold, 11, Font.NORMAL, scoreColor)));
        c2.setBackgroundColor(bg); c2.setPadding(7);
        c2.setHorizontalAlignment(Element.ALIGN_CENTER);
        c2.setBorderColor(new Color(220, 220, 220));

        PdfPCell c3 = new PdfPCell(new Phrase(level,
                new Font(bfNormal, 10, Font.NORMAL, scoreColor)));
        c3.setBackgroundColor(bg); c3.setPadding(7);
        c3.setHorizontalAlignment(Element.ALIGN_CENTER);
        c3.setBorderColor(new Color(220, 220, 220));

        table.addCell(c1); table.addCell(c2); table.addCell(c3);
    }

    // Petits utilitaires : safe() neutralise les guillemets (CSV/PDF) ;
    // orZero() évite les NullPointerException sur les scores non renseignés.
    private String safe(String s) { return s != null ? s.replace("\"", "'") : ""; }
    private double orZero(Double d) { return d != null ? d : 0.0; }
}
