package com.cvanalysis.repository;

import com.cvanalysis.entity.CVAnalysisResult;
import com.cvanalysis.entity.User;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.time.LocalDateTime;
import java.util.List;

/**
 * ============================================================================
 *  CVAnalysisResultRepository — accès aux données des analyses (couche DAO).
 * ----------------------------------------------------------------------------
 *  En héritant de JpaRepository, on obtient GRATUITEMENT save(), findById(),
 *  delete(), findAll()... sans écrire de SQL.
 *
 *  DEUX façons de définir des requêtes ici :
 *   1) "Derived queries" : Spring DÉDUIT la requête du NOM de la méthode.
 *      Ex : findByUserAndDeletedAtIsNullOrderByCreatedAtDesc
 *           = WHERE user = ? AND deletedAt IS NULL ORDER BY createdAt DESC.
 *   2) @Query (JPQL) : on écrit la requête nous-mêmes pour les cas complexes
 *      (recherche, agrégats, statistiques).
 *
 *  NB : presque toutes les requêtes filtrent "deletedAt IS NULL" pour IGNORER
 *  les candidats en corbeille (soft-delete).
 * ============================================================================
 */
@Repository
public interface CVAnalysisResultRepository extends JpaRepository<CVAnalysisResult, Long> {

    // Toutes les analyses d'un recruteur, plus récentes d'abord.
    List<CVAnalysisResult> findByUserOrderByCreatedAtDesc(User user);

    List<CVAnalysisResult> findAllByOrderByCreatedAtDesc();

    // Les 10 meilleurs scores (Top10 = LIMIT 10 déduit du nom de la méthode).
    List<CVAnalysisResult> findTop10ByOrderByOverallScoreDesc();

    // ===== Soft-delete / Corbeille =====
    // Candidats actifs (non supprimés) d'un recruteur
    List<CVAnalysisResult> findByUserAndDeletedAtIsNullOrderByCreatedAtDesc(User user);
    // Corbeille d'un recruteur (candidats supprimés)
    List<CVAnalysisResult> findByUserAndDeletedAtIsNotNullOrderByDeletedAtDesc(User user);
    // Tous les candidats actifs (pour vivier commun : talent search, analytics)
    List<CVAnalysisResult> findByDeletedAtIsNullOrderByCreatedAtDesc();
    // À purger : en corbeille depuis plus de N jours
    List<CVAnalysisResult> findByDeletedAtIsNotNullAndDeletedAtBefore(LocalDateTime threshold);
    // Top 10 actifs
    List<CVAnalysisResult> findTop10ByDeletedAtIsNullOrderByOverallScoreDesc();

    // Pagination + recherche globale (nom ou email) — exclut la corbeille
    @Query("SELECT r FROM CVAnalysisResult r WHERE r.deletedAt IS NULL AND " +
           "(:search IS NULL OR LOWER(r.candidateName) LIKE LOWER(CONCAT('%', :search, '%')) " +
           "OR LOWER(r.email) LIKE LOWER(CONCAT('%', :search, '%')))" +
           " ORDER BY r.createdAt DESC")
    Page<CVAnalysisResult> findAllWithSearch(@Param("search") String search, Pageable pageable);

    // Filtrer par seuil de score minimum
    @Query("SELECT r FROM CVAnalysisResult r WHERE r.deletedAt IS NULL AND r.overallScore >= :minScore ORDER BY r.overallScore DESC")
    List<CVAnalysisResult> findByMinScore(@Param("minScore") Double minScore);

    // Statistiques agrégées (candidats actifs uniquement)
    @Query("SELECT COUNT(r), AVG(r.overallScore), MAX(r.overallScore), MIN(r.overallScore), AVG(r.matchPercentage) FROM CVAnalysisResult r WHERE r.deletedAt IS NULL")
    Object[] getGlobalStats();

    @Query("SELECT COUNT(r) FROM CVAnalysisResult r WHERE r.deletedAt IS NULL AND r.overallScore >= 85")
    Long countExcellent();

    @Query("SELECT COUNT(r) FROM CVAnalysisResult r WHERE r.deletedAt IS NULL AND r.overallScore >= 70 AND r.overallScore < 85")
    Long countStrong();

    @Query("SELECT COUNT(r) FROM CVAnalysisResult r WHERE r.deletedAt IS NULL AND r.overallScore >= 55 AND r.overallScore < 70")
    Long countModerate();

    @Query("SELECT COUNT(r) FROM CVAnalysisResult r WHERE r.deletedAt IS NULL AND r.overallScore < 55")
    Long countWeak();
}
