package com.cvanalysis.repository;

import com.cvanalysis.entity.TechnicalTest;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

/**
 * Accès aux tests techniques. Méthodes "derived" (Spring génère le SQL depuis
 * le nom). Le jeton sert à retrouver un test depuis le lien d'invitation.
 */
@Repository
public interface TechnicalTestRepository extends JpaRepository<TechnicalTest, Long> {
    Optional<TechnicalTest> findByToken(String token);                 // passage via lien
    List<TechnicalTest> findAllByOrderByCreatedAtDesc();              // dashboard recruteur
    List<TechnicalTest> findByAnalysisResultIdOrderByCreatedAtDesc(Long analysisResultId);
}
