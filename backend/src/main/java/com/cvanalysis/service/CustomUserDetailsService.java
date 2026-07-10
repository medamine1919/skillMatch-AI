package com.cvanalysis.service;

import com.cvanalysis.entity.User;
import com.cvanalysis.repository.UserRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.security.core.userdetails.UserDetailsService;
import org.springframework.security.core.userdetails.UsernameNotFoundException;
import org.springframework.stereotype.Service;

/**
 * Pont entre NOTRE table "users" et Spring Security.
 * Spring appelle loadUserByUsername() pour récupérer l'utilisateur (et son
 * mot de passe haché + ses rôles) lors du login et de la validation du JWT.
 * Comme notre entité User implémente UserDetails, on peut la renvoyer telle quelle.
 */
@Service
public class CustomUserDetailsService implements UserDetailsService {

    @Autowired
    private UserRepository userRepository;

    @Override
    public UserDetails loadUserByUsername(String email) throws UsernameNotFoundException {
        // Ici "username" = l'e-mail (notre identifiant de connexion).
        User user = userRepository.findByEmail(email)
                .orElseThrow(() -> new UsernameNotFoundException("Utilisateur non trouvé: " + email));
        return user;
    }
}
