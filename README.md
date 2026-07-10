# 📊 Plateforme d'Analyse de CVs avec IA

Système web complet pour l'analyse automatisée de CVs utilisant le Machine Learning et les APIs REST.

## 🎯 Vue d'ensemble

```
┌─────────────────────────────────────────────────────────────────┐
│                   PLATEFORME D'ANALYSE DE CVs                   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────────────┐    ┌──────────────────────────┐      │
│  │   FRONTEND ANGULAR   │    │  BACKEND SPRING BOOT     │      │
│  │   (Port 4200)        │◄──►│  (Port 8080)             │      │
│  │  • Login/Register    │    │  • JWT Authentication    │      │
│  │  • Dashboard         │    │  • CV Analysis APIs      │      │
│  │  • Upload CV         │    │  • Gestion Utilisateurs  │      │
│  │  • Détails Candidats │    │  • PostgreSQL ORM        │      │
│  └──────────────────────┘    └──────────────────────────┘      │
│           │                            │                        │
│           │                            ├──► PostgreSQL          │
│           │                            │   (cv_analysis)        │
│           │                            │                        │
│           └────────────────────────────┤                        │
│                                        ▼                        │
│                           ┌──────────────────────┐              │
│                           │   FASTAPI SERVICE    │              │
│                           │   (Port 8000)        │              │
│                           │  • Scoring Candidats │              │
│                           │  • ML/LLM Processing │              │
│                           │  • Extraction Données│              │
│                           └──────────────────────┘              │
└─────────────────────────────────────────────────────────────────┘
```

## ✨ Fonctionnalités

### 🔐 Authentification & Sécurité
- ✅ Login/Register avec email et mot de passe
- ✅ JWT tokens (accès 24h, refresh 7 jours)
- ✅ Roles-based access control (ADMIN_RH, RECRUITER, USER)
- ✅ Protection des routes avec AuthGuard
- ✅ Token refresh automatique avec JwtInterceptor
- ✅ CORS configuré pour Angular frontend

### 📄 Gestion des CVs
- ✅ Upload fichiers (PDF, DOC, DOCX)
- ✅ Validation client et serveur
- ✅ Analyse IA automatique
- ✅ Stockage en base de données
- ✅ Historique d'analyses par utilisateur

### 📊 Dashboard & Reporting
- ✅ Statistiques globales (total candidats, % match, score moyen)
- ✅ Graphiques (distribution scores, match par candidat)
- ✅ Tableau des résultats avec tri/filtrage
- ✅ Export CSV des résultats
- ✅ Téléchargement de rapports PDF

### 👥 Gestion des Candidats
- ✅ Liste complète des candidats analysés
- ✅ Page détail avec scores, compétences, expériences
- ✅ Soft skills détectés
- ✅ Recommandations personnalisées
- ✅ Téléchargement rapport candidat

### 🎨 Interface Utilisateur
- ✅ Design moderne et responsive
- ✅ Gradient colors (violet/rose)
- ✅ Navigation intuitive
- ✅ Animations fluides
- ✅ Entièrement en français

## 🚀 Installation rapide

### Prérequis
- **Node.js** 18+
- **Java** 17+
- **PostgreSQL** 13+
- **Python** 3.9+ (FastAPI existant)

### Démarrage local (Recommandé)

#### Windows:
```bash
start.bat
```

#### macOS/Linux:
```bash
chmod +x start.sh
./start.sh
```

#### Ou manuellement - Terminal 1:
cd backend
mvn spring-boot:run
```

#### Terminal 2 - Frontend:
```bash
cd frontend
npm install
npm start
```

#### Terminal 3 - FastAPI (existant):
```bash
uvicorn api_server:app --reload --host 0.0.0.0 --port 8000
```

### Accès
- 🎨 **Frontend**: http://localhost:4200
- 🔌 **Backend**: http://localhost:8082/api
- 🤖 **FastAPI**: http://localhost:8000

## 🐳 Déploiement avec Docker

```bash
docker-compose up -d
```

Accès: http://localhost:4200

## 📚 Documentation

- **[QUICKSTART.md](./QUICKSTART.md)** - Guide de démarrage rapide
- **[ARCHITECTURE.md](./ARCHITECTURE.md)** - Architecture technique détaillée
- **[SUMMARY.md](./SUMMARY.md)** - Résumé complet du projet

## 🔑 Endpoints API

### Authentification
```
POST /api/auth/login           - Connexion utilisateur
POST /api/auth/register        - Inscription
POST /api/auth/refresh         - Renouvellement du token
```

### Analyse des CVs
```
POST   /api/cv-analysis/analyze              - Upload et analyser CV
GET    /api/cv-analysis/results              - Lister tous les résultats
GET    /api/cv-analysis/results/{id}         - Détails d'une analyse
GET    /api/cv-analysis/candidates/{id}      - Détails du candidat
GET    /api/cv-analysis/results/{id}/report  - Télécharger rapport PDF
GET    /api/cv-analysis/results/export/csv   - Exporter résultats CSV
```

## 📊 Structure du projet

```
cv_1/
├── frontend/                    # Application Angular (TypeScript)
│   ├── src/app/modules/         # Modules (auth, dashboard, etc.)
│   ├── src/app/services/        # Services (auth, cv-analysis)
│   ├── src/app/interceptors/    # JwtInterceptor
│   ├── src/app/guards/          # AuthGuard
│   └── src/environments/        # Configuration dev/prod
│
├── backend/                     # API Spring Boot (Java 17)
│   ├── src/main/java/
│   │   └── com/cvanalysis/
│   │       ├── controller/      # REST Controllers
│   │       ├── service/         # Business Logic
│   │       ├── entity/          # JPA Entities
│   │       ├── dto/             # Data Transfer Objects
│   │       ├── repository/      # Spring Data Repositories
│   │       ├── security/        # JWT & Security Config
│   │       └── config/          # Configuration
│   └── src/main/resources/      # Configuration files
│
├── QUICKSTART.md                # Guide rapide
├── ARCHITECTURE.md              # Documentation technique
├── SUMMARY.md                   # Résumé du projet
├── docker-compose.yml           # Orchestration Docker
├── start.sh                     # Script de démarrage (Linux/Mac)
└── start.bat                    # Script de démarrage (Windows)
```

## 🔒 Sécurité

### JWT Flow
1. Utilisateur se connecte → Backend génère JWT + RefreshToken
2. Frontend stocke le token dans localStorage
3. JwtInterceptor ajoute le token à chaque requête
4. JwtAuthenticationFilter valide le token côté serveur
5. Accès accordé/refusé selon les rôles

### Rôles & Permissions
- **ADMIN_RH**: Accès complet (analyses, utilisateurs, exports)
- **RECRUITER**: Analyses et consultations (pas de gestion utilisateurs)
- **USER**: Accès limité (propres CVs uniquement)

### Protection des Routes
```
Public:        /api/auth/**
Protected:     /api/cv-analysis/**  (nécessite JWT + rôle)
CORS:          Configuré pour http://localhost:4200
```

## 💾 Base de données

### Création
```bash
createdb cv_analysis
```

### Tables (Créées automatiquement par Hibernate)
- **users** - Utilisateurs avec rôles
- **cv_analysis_results** - Résultats d'analyse avec scores

## 📋 Configuration

### Backend (backend/src/main/resources/application.yml)
```yaml
spring:
  datasource:
    url: jdbc:postgresql://localhost:5432/cv_analysis
    username: postgres
    password: postgres

jwt:
  secret: your-secure-secret-key
  expiration: 86400000  # 24h
```

### Frontend (frontend/src/environments/environment.ts)
```typescript
export const environment = {
  apiUrl: 'http://localhost:8080',
  fastApiUrl: 'http://localhost:8000'
};
```

## 🐛 Dépannage

### Port déjà utilisé
```bash
# Windows
netstat -ano | findstr :8080
taskkill /PID <PID> /F

# macOS/Linux
lsof -i :8080
kill -9 <PID>
```

### Erreur de connexion PostgreSQL
```bash
# Vérifier que PostgreSQL est en cours d'exécution
psql -U postgres

# Créer la base si elle n'existe pas
createdb cv_analysis
```

### CORS Error
Vérifier que l'origine frontend est dans SecurityConfig.corsConfigurationSource()

## 🎯 Prochaines étapes

- [ ] Ajouter tests unitaires/E2E
- [ ] Implémenter export PDF complet
- [ ] Ajouter notifications real-time
- [ ] Intégration webhooks FastAPI
- [ ] Dashboard administrateur
- [ ] Export/Import en masse
- [ ] Multi-langue (i18n)

## 📞 Support

Pour les questions sur:
- **Angular**: https://angular.io/docs
- **Spring Boot**: https://spring.io/projects/spring-boot
- **PostgreSQL**: https://www.postgresql.org/docs
- **Docker**: https://docs.docker.com

## 📄 Licence

[Spécifiez votre licence ici]

---

**Version**: 1.0.0  
**Dernière mise à jour**: Mai 2026

**🎉 Prêt à être utilisé. Commencez par le [QUICKSTART](./QUICKSTART.md)!**
