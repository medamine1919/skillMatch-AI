package com.cvanalysis.service;

import com.cvanalysis.entity.CVAnalysisResult;
import com.cvanalysis.entity.TechnicalTest;
import com.cvanalysis.entity.User;
import com.cvanalysis.repository.CVAnalysisResultRepository;
import com.cvanalysis.repository.TechnicalTestRepository;
import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.*;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.*;

/**
 * ============================================================================
 *  TechnicalTestService — orchestre le test technique (QCM IA).
 * ----------------------------------------------------------------------------
 *   - generateAndSend : génère le QCM (via FastAPI/Groq) à partir du profil du
 *     candidat, crée le test (jeton + expiration) et envoie l'e-mail d'invitation.
 *   - getPublicTest   : renvoie les questions SANS les bonnes réponses (passage).
 *   - submitTest      : corrige automatiquement et enregistre le score.
 *   - listTests       : pour le tableau de bord recruteur.
 * ============================================================================
 */
@Service
public class TechnicalTestService {

    private static final int PASS_THRESHOLD = 60;      // réussite si score >= 60%
    private static final int EXPIRY_HOURS = 48;        // validité du lien : 48h puis expiration automatique
    private static final DateTimeFormatter FMT = DateTimeFormatter.ofPattern("dd/MM/yyyy HH:mm");

    @Autowired private TechnicalTestRepository testRepository;
    @Autowired private CVAnalysisResultRepository analysisResultRepository;
    @Autowired private RestTemplate restTemplate;
    @Autowired private EmailService emailService;

    private final ObjectMapper objectMapper = new ObjectMapper();

    @Value("${fastapi.url:http://localhost:8000}")
    private String fastApiUrl;

    // =========================================================================
    // 1) GÉNÉRATION + ENVOI
    // =========================================================================
    public TechnicalTest generateAndSend(Long analysisResultId, User recruiter) {
        CVAnalysisResult r = analysisResultRepository.findById(analysisResultId)
                .orElseThrow(() -> new RuntimeException("Candidat introuvable"));
        if (r.getEmail() == null || r.getEmail().isBlank()) {
            throw new RuntimeException("Ce candidat n'a pas d'e-mail : impossible d'envoyer le test.");
        }

        // --- Extraire compétences / spécialité / profil depuis l'analyse stockée ---
        List<String> skills = new ArrayList<>();
        String speciality = "";
        String jobTitle = "Test technique";
        try {
            JsonNode a = objectMapper.readTree(r.getAnalysisData() != null ? r.getAnalysisData() : "{}");
            if (a.path("skills").isArray()) a.path("skills").forEach(s -> skills.add(s.asText()));
            speciality = a.path("specialityRequirement").asText(a.path("specialityCv").asText(""));
            jobTitle = a.path("detectedJobProfile").asText(speciality.isBlank() ? "Test technique" : speciality);
        } catch (Exception ignored) {}

        // --- Demander le QCM au microservice IA (FastAPI / Groq) ---
        String questionsJson = requestQuestionsFromAI(skills, speciality, jobTitle);

        // --- Créer et stocker le test ---
        TechnicalTest test = new TechnicalTest();
        test.setAnalysisResultId(analysisResultId);
        test.setCandidateName(r.getCandidateName());
        test.setCandidateEmail(r.getEmail());
        test.setRecruiter(recruiter);
        test.setToken(UUID.randomUUID().toString());
        test.setStatus("PENDING");
        test.setJobTitle(jobTitle);
        test.setQuestionsJson(questionsJson);
        test.setCreatedAt(LocalDateTime.now());
        test.setExpiresAt(LocalDateTime.now().plusHours(EXPIRY_HOURS));
        try {
            test.setTotalQuestions(objectMapper.readTree(questionsJson).size());
        } catch (Exception e) { test.setTotalQuestions(0); }
        testRepository.save(test);

        // --- Envoyer l'e-mail d'invitation ---
        emailService.sendTestInvitation(r.getCandidateName(), r.getEmail(), test.getToken(), jobTitle);
        return test;
    }

    /** Appelle FastAPI /generate-test ; renvoie le JSON des questions (avec réponses). */
    private String requestQuestionsFromAI(List<String> skills, String speciality, String jobTitle) {
        try {
            Map<String, Object> body = new HashMap<>();
            body.put("skills", skills);
            body.put("speciality", speciality);
            body.put("job_title", jobTitle);
            body.put("num_questions", 10);

            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            String url = fastApiUrl.endsWith("/") ? fastApiUrl + "generate-test" : fastApiUrl + "/generate-test";

            @SuppressWarnings("unchecked")
            Map<String, Object> resp = restTemplate.postForObject(url, new HttpEntity<>(body, headers), Map.class);
            if (resp != null && resp.get("questions") != null) {
                return objectMapper.writeValueAsString(resp.get("questions"));
            }
            throw new RuntimeException("Réponse IA vide");
        } catch (Exception e) {
            throw new RuntimeException("Génération du test impossible (service IA): " + e.getMessage(), e);
        }
    }

    // =========================================================================
    // 2) PASSAGE (candidat, public) — questions SANS les bonnes réponses
    // =========================================================================
    public Map<String, Object> getPublicTest(String token) {
        TechnicalTest test = testRepository.findByToken(token)
                .orElseThrow(() -> new RuntimeException("Lien de test invalide."));

        // Expiration : bloque l'accès si le délai (48h) est dépassé.
        expireIfNeeded(test);
        Map<String, Object> out = new LinkedHashMap<>();
        out.put("candidateName", test.getCandidateName());
        out.put("jobTitle", test.getJobTitle());
        out.put("status", test.getStatus());
        out.put("totalQuestions", test.getTotalQuestions());

        if (!"PENDING".equals(test.getStatus())) {
            // Déjà passé ou expiré : on ne renvoie pas les questions.
            out.put("scorePercent", test.getScorePercent());
            out.put("passed", test.getPassed());
            return out;
        }
        // Questions SANS le champ "correct" (anti-triche).
        try {
            JsonNode qs = objectMapper.readTree(test.getQuestionsJson());
            List<Map<String, Object>> publicQs = new ArrayList<>();
            for (JsonNode q : qs) {
                Map<String, Object> m = new LinkedHashMap<>();
                m.put("question", q.path("question").asText());
                List<String> opts = new ArrayList<>();
                q.path("options").forEach(o -> opts.add(o.asText()));
                m.put("options", opts);
                publicQs.add(m);
            }
            out.put("questions", publicQs);
        } catch (Exception e) {
            out.put("questions", List.of());
        }
        return out;
    }

    // =========================================================================
    // 3) SOUMISSION + CORRECTION AUTOMATIQUE
    // =========================================================================
    public Map<String, Object> submitTest(String token, List<Integer> answers) {
        TechnicalTest test = testRepository.findByToken(token)
                .orElseThrow(() -> new RuntimeException("Lien de test invalide."));
        expireIfNeeded(test);   // si le délai (48h) est dépassé, le test passe en EXPIRED avant toute soumission
        if (!"PENDING".equals(test.getStatus())) {
            throw new RuntimeException("Ce test a déjà été passé ou a expiré.");
        }

        int correct = 0, total = 0;
        try {
            JsonNode qs = objectMapper.readTree(test.getQuestionsJson());
            total = qs.size();
            for (int i = 0; i < total; i++) {
                int good = qs.get(i).path("correct").asInt(-1);
                Integer given = (answers != null && i < answers.size()) ? answers.get(i) : null;
                if (given != null && given == good) correct++;
            }
            test.setAnswersJson(objectMapper.writeValueAsString(answers));
        } catch (Exception ignored) {}

        double pct = total > 0 ? Math.round((correct * 100.0 / total) * 10.0) / 10.0 : 0.0;
        test.setCorrectCount(correct);
        test.setTotalQuestions(total);
        test.setScorePercent(pct);
        test.setPassed(pct >= PASS_THRESHOLD);
        test.setStatus("COMPLETED");
        test.setCompletedAt(LocalDateTime.now());
        testRepository.save(test);

        Map<String, Object> out = new LinkedHashMap<>();
        out.put("scorePercent", pct);
        out.put("correctCount", correct);
        out.put("totalQuestions", total);
        out.put("passed", test.getPassed());
        return out;
    }

    // =========================================================================
    // 4) DASHBOARD RECRUTEUR
    // =========================================================================
    public List<Map<String, Object>> listTests() {
        List<Map<String, Object>> out = new ArrayList<>();
        for (TechnicalTest t : testRepository.findAllByOrderByCreatedAtDesc()) {
            expireIfNeeded(t);   // reflète l'expiration (48h) même si le candidat n'a jamais ouvert le lien
            Map<String, Object> m = new LinkedHashMap<>();
            m.put("id", t.getId());
            m.put("analysisResultId", t.getAnalysisResultId());   // pour ouvrir la fiche candidat
            m.put("candidateName", t.getCandidateName());
            m.put("candidateEmail", t.getCandidateEmail());
            m.put("jobTitle", t.getJobTitle());
            m.put("status", t.getStatus());
            m.put("scorePercent", t.getScorePercent());
            m.put("correctCount", t.getCorrectCount());
            m.put("totalQuestions", t.getTotalQuestions());
            m.put("passed", t.getPassed());
            m.put("recruiterName", t.getRecruiter() != null ? t.getRecruiter().getName() : "—");
            m.put("sentAt", t.getCreatedAt() != null ? t.getCreatedAt().format(FMT) : "");
            m.put("completedAt", t.getCompletedAt() != null ? t.getCompletedAt().format(FMT) : "");
            out.add(m);
        }
        return out;
    }

    /**
     * Marque un test comme EXPIRED s'il est encore PENDING mais que le délai de
     * validité (48h) est dépassé. Appelé à chaque lecture (dashboard, passage,
     * soumission) pour que l'expiration soit effective même si le candidat
     * n'ouvre jamais le lien d'invitation.
     *
     * @return true si le test vient d'être expiré.
     */
    private boolean expireIfNeeded(TechnicalTest test) {
        if ("PENDING".equals(test.getStatus())
                && test.getExpiresAt() != null
                && test.getExpiresAt().isBefore(LocalDateTime.now())) {
            test.setStatus("EXPIRED");
            testRepository.save(test);
            return true;
        }
        return false;
    }
}
