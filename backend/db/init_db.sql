-- Script d'initialisation PostgreSQL pour le projet CV Analysis
-- Exécuter en tant que superutilisateur (postgres)

CREATE DATABASE cv_analysis;

-- Créer un utilisateur avec mot de passe (changez le mot de passe en production)
CREATE USER cv_user WITH ENCRYPTED PASSWORD 'cv_pass';

GRANT ALL PRIVILEGES ON DATABASE cv_analysis TO cv_user;

-- Optionnel: vous pouvez aussi créer des schémas ou tables supplémentaires ici.
