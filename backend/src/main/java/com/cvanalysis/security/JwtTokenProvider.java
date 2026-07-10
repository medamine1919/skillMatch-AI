package com.cvanalysis.security;

import io.jsonwebtoken.Claims;
import io.jsonwebtoken.Jwts;
import io.jsonwebtoken.SignatureAlgorithm;
import io.jsonwebtoken.security.Keys;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.stereotype.Component;

import javax.crypto.SecretKey;
import java.util.Date;
import java.util.HashMap;
import java.util.Map;
import java.util.function.Function;

/**
 * ============================================================================
 *  JwtTokenProvider — fabrique et vérifie les jetons JWT.
 * ----------------------------------------------------------------------------
 *  Un JWT (JSON Web Token) est une "carte d'identité" signée numériquement.
 *  Après login, on en remet un au client ; à chaque requête, le client le
 *  renvoie pour prouver qui il est, SANS que le serveur stocke de session.
 *
 *  Un JWT contient :
 *    - subject  : l'identité (ici l'e-mail de l'utilisateur)
 *    - claims   : infos additionnelles (ici le rôle)
 *    - iat/exp  : dates d'émission et d'expiration
 *    - signature: empreinte HMAC-SHA512 calculée avec une clé SECRÈTE.
 *  Comme la signature dépend du secret serveur, un jeton modifié devient
 *  invalide -> impossible à falsifier sans connaître le secret.
 *
 *  On gère deux jetons : un court (access) et un long (refresh).
 * ============================================================================
 */
@Component
public class JwtTokenProvider {

    // Clé secrète et durées de vie, injectées depuis application.yml.
    @Value("${jwt.secret}")
    private String jwtSecret;

    @Value("${jwt.expiration}")
    private long jwtExpirationMs;

    @Value("${jwt.refresh-expiration}")
    private long refreshTokenExpirationMs;

    /** Transforme le secret texte en clé cryptographique pour signer/vérifier. */
    private SecretKey getSigningKey() {
        return Keys.hmacShaKeyFor(jwtSecret.getBytes());
    }

    /**
     * Générer un JWT token
     */
    public String generateToken(UserDetails userDetails) {
        Map<String, Object> claims = new HashMap<>();
        claims.put("role", userDetails.getAuthorities().stream().findFirst().get());
        return createToken(claims, userDetails.getUsername(), jwtExpirationMs);
    }

    /**
     * Générer un refresh token
     */
    public String generateRefreshToken(UserDetails userDetails) {
        Map<String, Object> claims = new HashMap<>();
        return createToken(claims, userDetails.getUsername(), refreshTokenExpirationMs);
    }

    /**
     * Créer un token
     */
    private String createToken(Map<String, Object> claims, String subject, long expirationTime) {
        Date now = new Date();
        Date expiryDate = new Date(now.getTime() + expirationTime);

        return Jwts.builder()
                .setClaims(claims)
                .setSubject(subject)
                .setIssuedAt(now)
                .setExpiration(expiryDate)
                .signWith(getSigningKey(), SignatureAlgorithm.HS512)
                .compact();
    }

    /**
     * Obtenir l'email du token
     */
    public String getEmailFromToken(String token) {
        return getClaimFromToken(token, Claims::getSubject);
    }

    /**
     * Vérifier si le token est expiré
     */
    public boolean isTokenExpired(String token) {
        try {
            Date expiration = getExpirationDateFromToken(token);
            return expiration.before(new Date());
        } catch (Exception e) {
            return true;
        }
    }

    /**
     * Valider le token
     */
    public boolean validateToken(String token) {
        try {
            Jwts.parser()
                    .setSigningKey(getSigningKey())
                    .build()
                    .parseClaimsJws(token);
            return !isTokenExpired(token);
        } catch (Exception e) {
            return false;
        }
    }

    /**
     * Obtenir la date d'expiration du token
     */
    private Date getExpirationDateFromToken(String token) {
        return getClaimFromToken(token, Claims::getExpiration);
    }

    /**
     * Obtenir une claim du token
     */
    private <T> T getClaimFromToken(String token, Function<Claims, T> claimsResolver) {
        final Claims claims = getAllClaimsFromToken(token);
        return claimsResolver.apply(claims);
    }

    /**
     * Obtenir toutes les claims du token
     */
    private Claims getAllClaimsFromToken(String token) {
        return Jwts.parser()
                .setSigningKey(getSigningKey())
                .build()
                .parseClaimsJws(token)
                .getBody();
    }
}
