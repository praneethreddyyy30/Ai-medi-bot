@echo off
setlocal enabledelayedexpansion
echo ========================================================
echo  Starting MediAI: Enterprise Java 17 + Spring Boot 3
echo ========================================================

:: Check for .env file to load GEMINI_API_KEY if present
if exist .env (
    for /f "usebackq tokens=1,* delims==" %%A in (".env") do (
        if not "%%A"=="" set "%%A=%%B"
    )
)

echo Starting Spring Boot Backend (Port 8080)...
if exist maven_home\apache-maven-3.9.6\bin\mvn.cmd (
    cd spring-boot-backend && ..\maven_home\apache-maven-3.9.6\bin\mvn.cmd spring-boot:run
) else (
    cd spring-boot-backend && mvnw.cmd spring-boot:run
)

echo.
echo ========================================================
echo  Web Application:   http://localhost:8080
echo  H2 Database UI:    http://localhost:8080/h2-console
echo ========================================================
