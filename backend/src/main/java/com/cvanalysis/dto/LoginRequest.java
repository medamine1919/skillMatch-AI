package com.cvanalysis.dto;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * DTO d'entrée pour /auth/login : le corps JSON envoyé par le frontend
 * (e-mail + mot de passe) est automatiquement converti en cet objet.
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class LoginRequest {
    private String email;
    private String password;
}
