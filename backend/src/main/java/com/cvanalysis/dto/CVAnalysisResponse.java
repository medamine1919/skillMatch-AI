package com.cvanalysis.dto;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.annotation.JsonIgnoreProperties;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.util.List;
import java.util.Map;

/**
 * ============================================================================
 *  CVAnalysisResponse — DTO de la réponse d'analyse renvoyée par FastAPI.
 * ----------------------------------------------------------------------------
 *  Jackson convertit automatiquement le JSON du microservice Python vers cet
 *  objet Java (et inversement). @JsonProperty mappe les noms de champs ;
 *  @JsonIgnoreProperties(ignoreUnknown=true) sur les sous-classes évite les
 *  erreurs si FastAPI ajoute des champs non déclarés ici.
 *  Les sous-classes (ScoresDTO, AnalysisDTO...) reflètent la structure imbriquée.
 * ============================================================================
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class CVAnalysisResponse {
    private String id;
    private String candidateName;
    private String email;
    private String phone;

    @JsonProperty("scores")
    private ScoresDTO scores;

    @JsonProperty("matchPercentage")
    private Double matchPercentage;

    @JsonProperty("recommendations")
    private List<String> recommendations;

    @JsonProperty("analysis")
    private AnalysisDTO analysis;

    @JsonProperty("fullText")
    private String fullText;

    private String timestamp;

    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    public static class ScoresDTO {
        private Double educationScore;
        private Double experienceScore;
        private Double skillsScore;
        private Double softSkillsScore;
        private Double overallScore;
    }

    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    @JsonIgnoreProperties(ignoreUnknown = true)
    public static class AnalysisDTO {
        private List<String> skills;
        private List<ExperienceDTO> experience;
        private List<EducationDTO> education;
        private List<String> softSkills;
        private List<String> languages;
        private List<String> certifications;
        private List<String> projects;
        private String summary;
        private String location;
        private String specialityCv;
        private String specialityRequirement;
        private String decisionLabel;
        private String recommendationLabel;
        private Double semanticSimilarityRatio;
        private Map<String, Double> weightedScores;
        private Map<String, Double> appliedWeights;
        private Map<String, Boolean> activeCriteria;
        private String detectedJobProfile;
        private Double detectedJobProfileConfidence;
        private Boolean outOfScope;
        private String cvExternalDomain;
        private String requirementExternalDomain;
        private String educationLevel;
        private String educationExplanation;
        private Double educationScore;
        private String extractedTextPreview;
    }

    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    public static class ExperienceDTO {
        private String title;
        private String company;
        private String duration;
        private String description;
    }

    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    public static class EducationDTO {
        private String degree;
        private String field;
        private String institution;
        private String year;
    }
}
