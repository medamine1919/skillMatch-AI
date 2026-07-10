package com.cvanalysis.entity;

import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

import java.time.LocalDateTime;

/**
 * ============================================================================
 *  TechnicalTest — un test technique (QCM) envoyé à un candidat.
 * ----------------------------------------------------------------------------
 *  Cycle de vie : PENDING (envoyé, en attente) -> COMPLETED (passé) ou EXPIRED.
 *  Les questions (avec les bonnes réponses) sont stockées en JSON côté serveur
 *  pour permettre la CORRECTION AUTOMATIQUE ; le candidat ne reçoit jamais les
 *  bonnes réponses. Le passage se fait via un JETON unique (sans login).
 * ============================================================================
 */
@Entity
@Table(name = "technical_tests")
@Data
@NoArgsConstructor
@AllArgsConstructor
public class TechnicalTest {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    /** Lien vers l'analyse de CV concernée (pour retrouver le candidat). */
    private Long analysisResultId;

    private String candidateName;
    private String candidateEmail;

    /** Recruteur qui a envoyé le test. */
    @ManyToOne
    @JoinColumn(name = "recruiter_id")
    private User recruiter;

    /** Jeton unique du lien d'invitation (sert d'auth légère, sans login). */
    @Column(unique = true, nullable = false)
    private String token;

    /** PENDING = envoyé / COMPLETED = passé / EXPIRED = délai dépassé */
    @Column(nullable = false)
    private String status = "PENDING";

    /** Intitulé du poste visé par le test (pour l'affichage). */
    private String jobTitle;

    /** Questions + bonnes réponses (JSON) — NE JAMAIS exposer tel quel au candidat. */
    @Column(columnDefinition = "TEXT")
    private String questionsJson;

    /** Réponses choisies par le candidat (JSON : index par question). */
    @Column(columnDefinition = "TEXT")
    private String answersJson;

    private Integer totalQuestions;
    private Integer correctCount;     // nb de bonnes réponses
    private Double scorePercent;      // score du test sur 100
    private Boolean passed;           // réussite (>= seuil)

    @Column(nullable = false)
    private LocalDateTime createdAt = LocalDateTime.now();

    /** Date limite pour passer le test (ex: +72h). */
    private LocalDateTime expiresAt;

    private LocalDateTime completedAt;
}
