package com.cvanalysis.repository;

import com.cvanalysis.entity.User;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.stereotype.Repository;

import java.util.List;
import java.util.Optional;

/**
 * Repository des utilisateurs. Méthodes "derived" : Spring génère la requête
 * SQL à partir du nom de la méthode (pas de SQL à écrire).
 */
@Repository
public interface UserRepository extends JpaRepository<User, Long> {
    Optional<User> findByEmail(String email);                 // chercher par e-mail (login)
    boolean existsByEmail(String email);                      // vérifier l'unicité à l'inscription
    Optional<User> findByApprovalToken(String approvalToken); // retrouver via le lien d'approbation e-mail
    Optional<User> findByResetToken(String resetToken);       // retrouver via le lien de réinitialisation
    List<User> findByStatusOrderByCreatedAtDesc(User.Status status); // ex : tous les PENDING
    List<User> findAllByOrderByCreatedAtDesc();               // tous, plus récents d'abord
}
