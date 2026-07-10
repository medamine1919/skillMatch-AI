package com.cvanalysis.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.client.RestTemplate;

/**
 * Déclare un bean RestTemplate réutilisable dans toute l'application.
 * RestTemplate est le client HTTP qui permet au backend Java d'APPELER le
 * microservice IA Python (FastAPI). Le déclarer en @Bean permet de l'injecter
 * partout via @Autowired (au lieu d'en recréer un à chaque fois).
 */
@Configuration
public class RestTemplateConfig {

    @Bean
    public RestTemplate restTemplate() {
        return new RestTemplate();
    }
}
