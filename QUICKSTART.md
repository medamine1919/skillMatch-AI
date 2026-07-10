# 🚀 Guide de démarrage rapide

## Installation locale

### 1. **Cloner le repository**
```bash
git clone <repository-url>
cd cv_1
```

### 2. **Base de données**
```bash
# Créer la base PostgreSQL
createdb cv_analysis
```

### 3. **Backend Spring Boot**
```bash
cd backend
mvn spring-boot:run
```
Le serveur sera disponible sur: **http://localhost:8082**

### 4. **Frontend Angular**
```bash
cd ../frontend
npm install
npm start
```
L'application sera accessible sur: **http://localhost:4200**

### 5. **FastAPI** (si nécessaire)
```bash
cd ..
uvicorn api_server:app --reload --host 0.0.0.0 --port 8000
```
Service disponible sur: **http://localhost:8000**

---

## 🐳 Avec Docker Compose

```bash
docker-compose up -d
```

Ensuite:
- Frontend: http://localhost:4200
- API: http://localhost:8082/api
- FastAPI: http://localhost:8000
- PostgreSQL: localhost:5432

---

## 🔐 Connexion par défaut

À créer via le formulaire d'inscription ou via API:

```bash
curl -X POST http://localhost:8080/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Admin RH",
    "email": "admin@example.com",
    "password": "Admin123!"
  }'
```

---

## 📋 Endpoints principales

| Méthode | URL | Description |
|---------|-----|-------------|
| POST | /api/auth/login | Connexion utilisateur |
| POST | /api/auth/register | Inscription |
| POST | /api/auth/refresh | Renouveller le token |
| POST | /api/cv-analysis/analyze | Upload et analyser CV |
| GET | /api/cv-analysis/results | Obtenir les résultats |
| GET | /api/cv-analysis/candidates/:id | Détails candidat |

---

## ✨ Fonctionnalités

✅ Authentification JWT  
✅ Analyse de CVs avec IA  
✅ Graphiques et statistiques  
✅ Gestion des candidats  
✅ Export CSV  
✅ Interface responsive  
✅ Rôles utilisateurs (Admin RH, Recruteur)  

---

## 🛠️ Améliorations futures

- [ ] Export PDF des rapports
- [ ] Notifications real-time
- [ ] Intégration des appels vidéo
- [ ] Machine Learning pour les recommandations
- [ ] Multi-langue
- [ ] Tests E2E

---

Besoin d'aide? Consultez [ARCHITECTURE.md](./ARCHITECTURE.md)
