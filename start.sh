#!/bin/bash

# Script de démarrage du projet CV Analysis
# Utilisation: ./start.sh

set -e

echo "================================"
echo "🚀 Démarrage du projet CV Analysis"
echo "================================"
echo ""

# Vérifications préalables
if ! command -v node &> /dev/null; then
    echo "❌ Node.js n'est pas installé"
    exit 1
fi

if ! command -v java &> /dev/null; then
    echo "❌ Java n'est pas installé"
    exit 1
fi

if ! command -v psql &> /dev/null; then
    echo "⚠️  PostgreSQL n'est pas trouvé. Assurez-vous que PostgreSQL est lancé."
fi

echo "✅ Vérifications passées"
echo ""

# Créer la base de données si elle n'existe pas
echo "📦 Vérification de la base de données PostgreSQL..."
psql -U postgres -tc "SELECT 1 FROM pg_database WHERE datname = 'cv_analysis'" | grep -q 1 || psql -U postgres -c "CREATE DATABASE cv_analysis"
echo "✅ Base de données prête"
echo ""

# Lancer le backend
echo "🔧 Démarrage du Backend Spring Boot..."
cd backend
mvn clean install -DskipTests &
BACKEND_PID=$!
echo "✅ Backend en cours de compilation (PID: $BACKEND_PID)"
echo ""

# Lancer le frontend
echo "🎨 Installation des dépendances du Frontend..."
cd ../frontend
npm install &
FRONTEND_INSTALL_PID=$!
echo "✅ Installation en cours (PID: $FRONTEND_INSTALL_PID)"
echo ""

# Attendre la compilation du backend
echo "⏳ En attente de compilation du backend..."
wait $BACKEND_PID
echo "✅ Backend compilé"

# Démarrer le backend
echo "🚀 Lancement du Backend sur le port 8082..."
cd ../backend
mvn spring-boot:run > backend.log 2>&1 &
BACKEND_RUN_PID=$!
sleep 3
echo "✅ Backend lancé (PID: $BACKEND_RUN_PID)"
echo ""

# Démarrer FastAPI
echo "🚀 Lancement de FastAPI sur le port 8000..."
cd ..
if [ -f ".venv/bin/activate" ]; then
    . .venv/bin/activate
fi
uvicorn api_server:app --reload --host 0.0.0.0 --port 8000 > fastapi.log 2>&1 &
FASTAPI_RUN_PID=$!
sleep 3
echo "✅ FastAPI lancé (PID: $FASTAPI_RUN_PID)"
echo ""

# Attendre installation frontend
echo "⏳ En attente d'installation du Frontend..."
wait $FRONTEND_INSTALL_PID
echo "✅ Frontend prêt"

# Démarrer le frontend
echo "🚀 Lancement du Frontend sur le port 4200..."
cd ../frontend
ng serve > frontend.log 2>&1 &
FRONTEND_PID=$!
sleep 3
echo "✅ Frontend lancé (PID: $FRONTEND_PID)"
echo ""

echo "================================"
echo "✨ Application prête!"
echo "================================"
echo ""
echo "📱 Frontend: http://localhost:4200"
echo "🔌 Backend:  http://localhost:8082/api"
echo "🤖 FastAPI: http://localhost:8000"
echo ""
echo "Log files:"
echo "- Backend: backend/backend.log"
echo "- Frontend: frontend/frontend.log"
echo "- FastAPI: fastapi.log"
echo ""
echo "Pour arrêter: Ctrl+C"
echo ""

# Garder les processus actifs
wait
