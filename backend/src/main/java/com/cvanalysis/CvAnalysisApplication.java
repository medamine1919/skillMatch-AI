package com.cvanalysis;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.scheduling.annotation.EnableScheduling;

/**
 * Point d'ENTRÉE de l'application Spring Boot.
 *  - @SpringBootApplication : active la config automatique + le scan des
 *    composants (contrôleurs, services, repositories...).
 *  - @EnableScheduling : active les tâches planifiées @Scheduled
 *    (ici : la purge automatique de la corbeille chaque nuit).
 */
@SpringBootApplication
@EnableScheduling
public class CvAnalysisApplication {
    public static void main(String[] args) {
        // Démarre le serveur web embarqué (Tomcat) et toute l'application.
        SpringApplication.run(CvAnalysisApplication.class, args);
    }
}
