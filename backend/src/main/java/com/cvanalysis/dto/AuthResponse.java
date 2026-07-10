package com.cvanalysis.dto;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * DTO (Data Transfer Object) renvoyé après un login/refresh réussi.
 * Un DTO sert à transporter EXACTEMENT les données utiles au frontend, sans
 * exposer l'entité interne (ici on ne renvoie jamais le mot de passe).
 * Contient les deux jetons + les infos publiques de l'utilisateur.
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class AuthResponse {
    private String token;          // jeton d'accès (courte durée)
    private String refreshToken;   // jeton de renouvellement (longue durée)
    private UserDTO user;          // infos publiques de l'utilisateur connecté

    /** Sous-objet : données utilisateur sûres à exposer au frontend. */

    @Data
    @NoArgsConstructor
    @AllArgsConstructor
    public static class UserDTO {
        private Long id;
        private String email;
        private String name;
        private String role;
    }
}
