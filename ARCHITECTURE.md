# 📋 Architecture Angular + Spring Boot + FastAPI

## 🎯 Vue d'ensemble

Ce projet est une plateforme web complète pour l'analyse des CVs utilisant l'IA. L'architecture est composée de trois couches:

### 1. **Frontend (Angular)**
- **Port**: 4200
- **Description**: Application web responsive avec modules lazy-loaded
- **Modules**:
  - `auth`: Gestion de l'authentification avec JWT
  - `dashboard`: Tableau de bord avec statistiques et graphiques
  - `candidates`: Gestion des candidats et détails
  - `upload`: Upload et analyse de CVs

### 2. **Backend Spring Boot (API REST)**
- **Port**: 8080
- **Description**: API REST sécurisée avec JWT
- **Features**:
  - Authentification et autorisation
  - Gestion des utilisateurs
  - Stockage des résultats d'analyse

### 3. **FastAPI (Scoring Service)**
- **Port**: 8000 (existant)
- **Description**: Service IA pour le scoring des CVs
- **Intégration**: Appelée par Spring Boot

---

## 🚀 Installation et démarrage

### Prérequis
- Node.js 18+
- Java 17+
- PostgreSQL 13+
- Python 3.9+

### 1️⃣ Base de données (PostgreSQL)

```bash
# Créer la base de données
createdb cv_analysis

# Ou avec psql
psql -U postgres -c "CREATE DATABASE cv_analysis;"
```

### 2️⃣ Backend Spring Boot

```bash
cd backend

# Compiler le projet
mvn clean package

# Démarrer le serveur
mvn spring-boot:run

# Ou directement
java -jar target/cv-analysis-api-1.0.0.jar
```

**Configuration** (src/main/resources/application.yml):
- Base de données: PostgreSQL (localhost:5432)
- JWT Secret: À changer en production (variable d'environnement)
- Port: 8080

### 3️⃣ Frontend Angular

```bash
cd frontend

# Installer les dépendances
npm install

# Démarrer le serveur de développement
npm start

# Ou
ng serve
```

L'application sera accessible à: **http://localhost:4200**

### 4️⃣ FastAPI (existant)

```bash
cd ..  # Revenir à la racine

# Installer les dépendances
pip install -r requirements.txt

# Démarrer le serveur
python app.py
```

---

## 🔐 Authentification JWT

### Flux de connexion

1. **Utilisateur se connecte** avec email/password
2. **Spring Boot génère un JWT** valide 24h
3. **JWT est stocké** dans le localStorage
4. **Chaque requête** inclut le JWT dans le header `Authorization: Bearer <token>`
5. **JwtAuthenticationFilter** valide le token côté serveur

### Endpoints d'authentification

```
POST /api/auth/login
POST /api/auth/register
POST /api/auth/refresh
```

---

## 📚 Structure des dossiers

### Frontend
```
frontend/
├── src/
│   ├── app/
│   │   ├── modules/
│   │   │   ├── auth/              # Module d'authentification
│   │   │   ├── dashboard/         # Tableau de bord
│   │   │   ├── candidates/        # Gestion des candidats
│   │   │   ├── upload/            # Upload de CVs
│   │   │   └── error/             # Pages d'erreur
│   │   ├── services/              # Services (auth, cv-analysis)
│   │   ├── interceptors/          # JWT Interceptor
│   │   ├── guards/                # Auth Guard
│   │   └── app.module.ts
│   ├── environments/              # Configuration
│   └── index.html
├── package.json
└── angular.json
```

### Backend
```
backend/
├── src/
│   └── main/
│       ├── java/
│       │   └── com/cvanalysis/
│       │       ├── controller/    # REST Controllers
│       │       ├── service/       # Business Logic
│       │       ├── entity/        # JPA Entities
│       │       ├── dto/           # Data Transfer Objects
│       │       ├── repository/    # Spring Data Repositories
│       │       ├── security/      # JWT & Security
│       │       ├── config/        # Configuration
│       │       └── CvAnalysisApplication.java
│       └── resources/
│           └── application.yml    # Configuration
├── pom.xml
└── target/
```

---

## 🔌 API REST

### Authentification

```
POST /api/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123"
}

Response:
{
  "token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "refreshToken": "eyJ0eXAiOiJKV1QiLCJhbGc...",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "name": "Nom Utilisateur",
    "role": "RECRUITER"
  }
}
```

### CV Analysis

```
POST /api/cv-analysis/analyze
Authorization: Bearer <token>
Content-Type: multipart/form-data

file: <CV file>
requirements: <optional job description>

Response:
{
  "id": "1",
  "candidateName": "John Doe",
  "email": "john@example.com",
  "phone": "+1 234 567 8900",
  "scores": {
    "educationScore": 85,
    "experienceScore": 78,
    "skillsScore": 92,
    "softSkillsScore": 88,
    "overallScore": 85
  },
  "matchPercentage": 85,
  "recommendations": ["Candidate meets 85% of requirements..."],
  "analysis": {
    "skills": ["Python", "Angular", "Spring Boot"],
    "experience": [...],
    "education": [...],
    "softSkills": ["Leadership", "Communication"]
  }
}
```

---

## 🔒 Sécurité

### AuthGuard (Angular)
- Vérifie si l'utilisateur est connecté
- Redirige vers login si non authentifié
- Valide les rôles requis

### JwtAuthenticationFilter (Spring Boot)
- Extrait le JWT du header Authorization
- Valide la signature et l'expiration
- Charge les détails de l'utilisateur

### Rôles
- **ADMIN_RH**: Accès complet
- **RECRUITER**: Accès aux analyses
- **USER**: Accès limité

---

## 🚀 Déploiement (Production)

### Docker Compose

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:13
    environment:
      POSTGRES_DB: cv_analysis
      POSTGRES_PASSWORD: secure_password
    ports:
      - "5432:5432"

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8080:8080"
    environment:
      JWT_SECRET: your-secure-secret-key
      DATABASE_URL: jdbc:postgresql://postgres:5432/cv_analysis
    depends_on:
      - postgres

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "80:80"
    depends_on:
      - backend

  fastapi:
    build:
      context: .
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
```

---

## 🔧 Variables d'environnement

### Spring Boot (.env)
```
JWT_SECRET=your-very-secure-random-secret-key-here
JWT_EXPIRATION=86400000
DATABASE_URL=jdbc:postgresql://localhost:5432/cv_analysis
DATABASE_USER=postgres
DATABASE_PASSWORD=postgres
```

### Angular (environment.ts)
```typescript
export const environment = {
  production: false,
  apiUrl: 'http://localhost:8080',
  fastApiUrl: 'http://localhost:8000'
};
```

---

## 📊 Intégration FastAPI

Le backend Spring Boot appelle le service FastAPI pour le scoring:

```java
// CVAnalysisService.java
private CVAnalysisResponse callFastAPIForAnalysis(MultipartFile file, String requirements) {
    // TODO: Appel à FastAPI via RestTemplate
    // POST http://localhost:8000/analyze
    // Retourner les scores
}
```

---

## ✅ Checklist d'intégration

- [ ] Base de données PostgreSQL créée
- [ ] Backend Spring Boot configuré et démarré
- [ ] Frontend Angular installé et fonctionnel
- [ ] FastAPI intégré au backend
- [ ] JWT correctly implemented
- [ ] CORS configured correctly
- [ ] File upload working
- [ ] Database queries optimized
- [ ] Error handling implemented
- [ ] Unit tests written

---

## 🐛 Dépannage

### Port 8080 déjà utilisé
```bash
lsof -i :8080  # Trouver le processus
kill -9 <PID>  # Tuer le processus
```

### Erreur de connexion à PostgreSQL
```bash
# Vérifier que PostgreSQL est démarré
psql -U postgres
```

### CORS Error
- Vérifier `SecurityConfig.corsConfigurationSource()`
- Assurez-vous que les origines sont correctes

---

## 📞 Support

Pour plus d'informations, consultez:
- Angular: https://angular.io
- Spring Boot: https://spring.io/projects/spring-boot
- JWT: https://tools.ietf.org/html/rfc7519

---

**Dernière mise à jour**: Mai 2026
