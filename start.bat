@echo off
REM Script de démarrage du projet CV Analysis pour Windows
setlocal

set "ROOT_DIR=%~dp0"

echo.
echo ================================
echo.
echo 🚀 Demarrage du projet CV Analysis
echo.
echo ================================
echo.

REM Vérifications
where node >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ Node.js n'est pas installe
    exit /b 1
)

where java >nul 2>nul
if %errorlevel% neq 0 (
    echo ❌ Java n'est pas installe
    exit /b 1
)

echo ✅ Verifications passees
echo.

REM Créer la base de données
echo 📦 Creation de la base de donnees PostgreSQL...
psql -U postgres -c "CREATE DATABASE cv_analysis;" 2>nul
echo ✅ Base de donnees prete
echo.

REM Lancer le backend
echo 🔧 Demarrage du Backend Spring Boot...
start "Backend Spring Boot" /D "%ROOT_DIR%backend" cmd /k mvn spring-boot:run
timeout /t 5
echo ✅ Backend lance
echo.

REM Lancer FastAPI
echo 🔧 Demarrage de FastAPI...
start "FastAPI" /D "%ROOT_DIR%" cmd /k "if exist .venv\Scripts\activate.bat call .venv\Scripts\activate.bat && uvicorn api_server:app --reload --host 0.0.0.0 --port 8000"
timeout /t 3
echo ✅ FastAPI lance
echo.

REM Installer et lancer le frontend
echo 🎨 Installation du Frontend...
pushd "%ROOT_DIR%frontend"
call npm install
echo ✅ Frontend pret
echo.

echo 🚀 Lancement du Frontend...
start "Angular Frontend" /D "%ROOT_DIR%frontend" cmd /k ng serve
popd
timeout /t 3
echo ✅ Frontend lance
echo.

echo ================================
echo ✨ Application prete!
echo ================================
echo.
echo 📱 Frontend: http://localhost:4200
echo 🔌 Backend:  http://localhost:8082/api
echo 🤖 FastAPI: http://localhost:8000
echo.
echo Les fenêtres terminales vont afficher les logs.
echo Fermez-les pour arrêter l'application.
echo.
pause
endlocal
