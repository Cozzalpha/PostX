@echo off
echo ========================================================
echo      STARTING SOCIAL AGENT AI (5 SERVICES)
echo ========================================================

:: --- CONFIGURATION ---
set PROJECT_PATH="C:\Users\Praneel Jain\social_agent"

:: 0. Start Redis (The Database)
echo [0/4] Starting Redis...
:: Try to start existing container first to avoid name errors
docker start social-redis >nul 2>&1
if %errorlevel% neq 0 (
    echo Creating and starting new Redis container...
    docker run -d -p 6379:6379 --name social-redis redis
) else (
    echo Redis container 'social-redis' is running.
)

:: 1. Start Django Server (Website)
echo [1/4] Starting Django Server...
start "1. Django Website" cmd /k "cd /d %PROJECT_PATH% && venv\Scripts\activate && python manage.py runserver"

:: 2. Start Celery Worker (The Muscle)
echo [2/4] Starting Celery Worker...
start "2. Celery Worker" cmd /k "cd /d %PROJECT_PATH% && venv\Scripts\activate && celery -A config worker --pool=solo -l info"

:: 3. Start Celery Beat (The Clock)
echo [3/4] Starting Celery Beat...
start "3. Celery Beat" cmd /k "cd /d %PROJECT_PATH% && venv\Scripts\activate && celery -A config beat -l info"

:: 4. Start Ngrok (The Tunnel)
echo [4/4] Starting Ngrok...
start "4. Ngrok Tunnel" cmd /k "ngrok http 8000"

echo ========================================================
echo ALL SYSTEMS GO! 
echo 1. Copy the URL from the Ngrok Window.
echo 2. Update 'settings.py' and 'core/tasks.py' if the URL changed.
echo ========================================================
pause