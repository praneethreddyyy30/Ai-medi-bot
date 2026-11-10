@echo off
setlocal enabledelayedexpansion
echo ========================================================
echo  Starting MediAI: Polyglot Full Stack (Spring Boot + ML)
echo ========================================================

:: Check for .env file to load GEMINI_API_KEY
if exist ml-service\.env (
    for /f "usebackq tokens=1,* delims==" %%A in ("ml-service\.env") do (
        if not "%%A"=="" set "%%A=%%B"
    )
) else if exist .env (
    for /f "usebackq tokens=1,* delims==" %%A in (".env") do (
        if not "%%A"=="" set "%%A=%%B"
    )
)

echo [1/2] Starting Python XGBoost ML Microservice (Port 5001)...
start "MediAI-Python-ML-Service" cmd /k "cd ml-service && python ml_service.py"

timeout /t 3 /nobreak >nul

echo [2/2] Starting Spring Boot Backend (Port 8080)...
if exist maven_home\apache-maven-3.9.6\bin\mvn.cmd (
    start "MediAI-Spring-Boot-Backend" cmd /k "cd spring-boot-backend && ..\maven_home\apache-maven-3.9.6\bin\mvn.cmd spring-boot:run"
) else (
    start "MediAI-Spring-Boot-Backend" cmd /k "cd spring-boot-backend && mvnw.cmd spring-boot:run"
)

echo.
echo ========================================================
echo  All services are booting!
echo  Web Application:   http://localhost:8080
echo  H2 Database UI:    http://localhost:8080/h2-console
echo  ML Service Health: http://localhost:5001/health
echo ========================================================
