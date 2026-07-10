package com.cvanalysis.entity;

import com.fasterxml.jackson.annotation.JsonIgnore;
import jakarta.persistence.*;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import org.springframework.security.core.GrantedAuthority;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.userdetails.UserDetails;

import java.time.LocalDateTime;
import java.util.Collection;
import java.util.List;

/**
 * ============================================================================
 *  User — ENTITÉ JPA (table "users") ET utilisateur Spring Security.
 * ----------------------------------------------------------------------------
 *  Particularité : la classe implémente UserDetails, l'interface attendue par
 *  Spring Security. Ainsi le MÊME objet sert à la fois de ligne en base ET
 *  d'identité de sécurité (avec rôles, état du compte...).
 *  Les méthodes isAccountNonLocked()/getAuthorities() ci-dessous relient notre
 *  modèle (statut, rôle) aux mécanismes de Spring.
 * ============================================================================
 */
@Entity
@Table(name = "users")
@Data
@NoArgsConstructor
@AllArgsConstructor
public class User implements UserDetails {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @Column(unique = true, nullable = false)
    private String email;

    @Column(nullable = false)
    private String password;

    @Column(nullable = false)
    private String name;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    private Role role;

    @Column(nullable = false)
    private Boolean enabled = true;

    /** PENDING → en attente d'approbation admin, APPROVED → actif, DECLINED → refusé */
    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    private Status status = Status.PENDING;

    /** Token unique envoyé dans le mail admin pour approuver/décliner via lien */
    @Column(unique = true)
    private String approvalToken;

    /** Date d'inscription */
    @Column
    private LocalDateTime createdAt = LocalDateTime.now();

    /** Jeton temporaire pour réinitialiser le mot de passe (mot de passe oublié). */
    @Column
    private String resetToken;

    /** Date d'expiration du jeton de réinitialisation (1h après la demande). */
    @Column
    private LocalDateTime resetTokenExpiry;

    @OneToMany(mappedBy = "user", cascade = CascadeType.ALL)
    @JsonIgnore
    private List<CVAnalysisResult> analysisResults;

    @Override
    public Collection<? extends GrantedAuthority> getAuthorities() {
        return List.of(new SimpleGrantedAuthority("ROLE_" + role.name()));
    }

    @Override
    public String getUsername() {
        return email;
    }

    @Override
    public boolean isAccountNonExpired() {
        return true;
    }

    @Override
    public boolean isAccountNonLocked() {
        // Bloque la connexion si le compte n'est pas approuvé
        return status == Status.APPROVED;
    }

    @Override
    public boolean isCredentialsNonExpired() {
        return true;
    }

    @Override
    public boolean isEnabled() {
        return enabled;
    }

    public enum Role {
        ADMIN_RH,
        RECRUITER,
        USER
    }

    public enum Status {
        PENDING,
        APPROVED,
        DECLINED
    }
}
