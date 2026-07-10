package com.cvanalysis.dto;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * DTO d'entrée pour /auth/register : données saisies au formulaire d'inscription.
 */
@Data
@NoArgsConstructor
@AllArgsConstructor
public class RegisterRequest {
    private String name;
    private String email;
    private String password;
    private String role; // Admin RH, Recruiter, User, etc.
}
