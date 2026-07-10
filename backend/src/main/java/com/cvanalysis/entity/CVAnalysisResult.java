package com.cvanalysis.entity;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

/**
 * ============================================================================
 *  CVAnalysisResult — ENTITÉ JPA = une ligne de la table cv_analysis_results.
 * ----------------------------------------------------------------------------
 *  @Entity / @Table : mappe cette classe à une table de la base.
 *  @Data (Lombok)   : génère getters/setters/toString automatiquement.
 *  @Id + @GeneratedValue(IDENTITY) : clé primaire auto-incrémentée par la base.
 *  @ManyToOne       : plusieurs analyses appartiennent à UN recruteur (user).
 *  Les gros contenus (détail JSON, texte du CV) sont en colonnes TEXT.
 * ============================================================================
 */
@Entity
@Table(name = "cv_analysis_results")
@Data
@NoArgsConstructor
@AllArgsConstructor
public class CVAnalysisResult {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    // Lien vers le recruteur propriétaire (clé étrangère user_id).
    @ManyToOne
    @JoinColumn(name = "user_id", nullable = false)
    private User user;

    @Column(nullable = false)
    private String candidateName;

    @Column(nullable = false)
    private String email;

    private String phone;

    private String cvPath;

    @Column(columnDefinition = "TEXT")
    private String analysisData; // JSON data

    @com.fasterxml.jackson.annotation.JsonIgnore
    @Column(columnDefinition = "TEXT")
    private String cvFullText; // Texte complet du CV (pour Talent Search RAG)

    private Double overallScore;
    private Double educationScore;
    private Double experienceScore;
    private Double skillsScore;
    private Double softSkillsScore;
    private Double matchPercentage;

    @Column(columnDefinition = "TEXT")
    private String recommendations; // JSON array

    @Column(nullable = false)
    private LocalDateTime createdAt;

    @Column(nullable = false)
    private LocalDateTime updatedAt;

    /** Date de mise en corbeille (null = candidat actif). Purge auto après 30 jours. */
    @Column
    private LocalDateTime deletedAt;

    // ===== Talent Search (RAG) — non persistés, calculés à la volée =====
    @Transient
    private Double relevanceScore;

    @Transient
    private Double semanticScore;

    @PrePersist
    protected void onCreate() {
        createdAt = LocalDateTime.now();
        updatedAt = LocalDateTime.now();
    }

    @PreUpdate
    protected void onUpdate() {
        updatedAt = LocalDateTime.now();
    }
}
