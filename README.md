# PostX
A complete Social Media Automation solution designed for agencies. Allows admins to manage multiple clients, define brand voices, and automate content delivery pipelines with built-in AI generation and image handling.

🤖 Social Agent AI
An autonomous social media marketing platform built with Django, Celery, and Google Gemini.

Social Agent AI acts as a full-time social media manager. It schedules, generates, and publishes Instagram content automatically. It supports multi-tenant agencies (Admin vs. Clients), automated campaign generation, and human-in-the-loop approval workflows.

✨ Features
🚀 Auto-Campaigns: define a topic (e.g., "Healthy Living") and duration (e.g., 7 days). The bot generates unique daily posts automatically.
🧠 AI-Powered Content: Uses Google Gemini 1.5 Flash to write high-converting captions using the AIDA framework, custom emojis, and hashtags.
📅 Smart Scheduling: Calculates optimal posting times based on start time and intervals.
✅ Approval Workflow: Content isn't posted blindly.
Draft → AI Generation → Waiting Approval (Human Review) → Auto-Post.
👥 Multi-User Support:
Super Admin: Manages all clients and campaigns.
Client Mode: Clients log in to see only their specific dashboard and approve their own posts.
📸 Smart Image Handling: Supports custom uploads per post, campaign image pools (shuffles images), and falls back to the Client Logo if no image is provided.

🛠️ Tech Stack
Backend: Django 5 (Python)
Task Queue: Celery 5
Message Broker: Redis
AI Model: Google Gemini 1.5 Flash
Database: SQLite (Dev) / PostgreSQL (Prod ready)
Frontend: HTML5 + TailwindCSS via CDN
Integration: Instagram Graph API

📋 Prerequisites
Before running the project, ensure you have:
Python 3.10+: Download
Docker Desktop: Download (Required to run Redis easily)
Ngrok: Download (Required so Facebook can download local images)
Meta Developer Account: An App with pages_manage_posts and instagram_content_publish permissions.
Google AI Studio Key: A free API key for Gemini.

🚀 Installation & Setup
1. Clone & Environment
Bash
git clone https://github.com/yourusername/social-agent-ai.git
cd social-agent-ai

# Windows
python -m venv venv
venv\Scripts\activate

# Mac/Linux
python3 -m venv venv
source venv/bin/activate

2. Install Dependencies
Bash
pip install -r requirements.txt

3. Database Initialization
Bash
python manage.py makemigrations
python manage.py migrate
python manage.py createsuperuser

4. Configuration
Ngrok: Start ngrok to get your public URL:
Bash
ngrok http 8000
Update Settings:

Open config/settings.py and add your Ngrok URL to CSRF_TRUSTED_ORIGINS and ALLOWED_HOSTS.
Open core/tasks.py and update NGROK_URL and GEMINI_API_KEY.

🏎️ Running the Engine
The system requires 4 services running simultaneously. You can use the included start_social_agent.bat (Windows) or run them manually:

Manual Startup (4 Terminals)
Terminal 1: Redis (Database for Tasks)
Bash
docker run -d -p 6379:6379 --name social-redis redis

Terminal 2: Django (Website)
Bash
python manage.py runserver

Terminal 3: Celery Worker (The AI & Upload Logic)
Bash
celery -A config worker --pool=solo -l info

Terminal 4: Celery Beat (The Scheduler)
Bash
celery -A config beat -l info

📖 How to Use
1. Setup a Client (Admin Step)
Log in to /admin with your Superuser account.
Create a User for your client (e.g., urban_eats).
Go to Clients -> Add Client.
Link the User urban_eats.
Add the Long-Lived Instagram Access Token & Business ID.
Upload a Logo (Crucial for fallback images).

3. Launch a Campaign
Log in to the dashboard (/).
Click "Start Auto-Campaign".
Choose "Topic Series" (e.g., "New Menu Launch") or "General Awareness".
Upload a few images (optional) and set "3 posts per day".
Click Launch.
The system will generate posts for the entire duration immediately.

3. Approval Flow
Posts appear on the dashboard as "AI Done (Needs Review)" (Yellow).
Review the AI-generated caption.
Click Approve (Green) to schedule it for upload.
OR Click Rewrite to have AI try again.

TroubleShooting
Error, Solution
Error 10061 ... target machine actively refused it, Redis is not running. Run docker start social-redis.
Facebook Container Error: Image URL not accessible, Ngrok is down or you forgot to update NGROK_URL in tasks.py.
Module 'social_agent' not found, You are running Celery wrong. Use -A config, not -A social_agent."
OperationalError: no such table, You forgot to run python manage.py migrate.
