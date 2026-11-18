# Remote Classroom

**Bandwidth-Adaptive Learning Platform for Rural Colleges**  
Final Year Project · B.Tech CSE (Batch 2023–2027)  
Team: Tech Fusion · Project ID: PIET/CS/2023-27/05  
Approved Problem Statement: PIET/CS/FYP/PS-096 — Remote Classroom for Rural Colleges  
Project Guide: Mr. Indra Kishor · Section: 7CSD

## 1. What this project does

Remote Classroom is a web-based learning platform for students who may not have reliable, high-speed internet. Faculty can create subjects, upload recorded lectures and schedule live sessions using a Google Meet or Zoom link. Students can enroll in subjects, open their recordings and read a text summary when watching a full video is difficult.

The distinctive workflow is the **Lite Mode pipeline**:

1. A faculty member uploads a lecture recording.
2. FFmpeg prepares multiple HLS video qualities for adaptive playback.
3. The background worker sends the audio in the recording to OpenAI Whisper for speech-to-text transcription.
4. The transcript is summarized using the TextRank extractive summarizer from Sumy.
5. The transcript and a concise summary are stored with the lecture. The summary is shown in Lite Mode.

The target summary is approximately 300–500 words. When the source transcript is shorter than 300 words, the application returns the available extractive content rather than inventing extra material.

## 2. Current build boundary

This repository is the implementation baseline for **Sprints I, II and III**.

| Sprint | Scope in this build |
|---|---|
| Sprint I | Problem definition, user roles, requirements, database design and SRS |
| Sprint II | Subject management, lecture upload/view, adaptive HLS processing, live-class link scheduling and notifications |
| Sprint III | Whisper transcription, TextRank summary generation, transcript/summary status and Lite Mode |
| Sprint IV | Per-lecture Doubt/Q&A module, final integration, broader testing, cloud deployment and final demonstration — intentionally held for the next sprint |

Do not describe Sprint IV functionality as completed. The separate Doubt/Q&A feature belongs to Sprint IV in the four-sprint plan. The initial implementation focuses on delivering the first three sprints cleanly.

## 3. Technology choices

The synopsis lists alternatives. This implementation selects one coherent option from those alternatives:

| Layer | Selected technology | Reason in this project |
|---|---|---|
| Frontend | React.js, HTML5, CSS3, JavaScript | Responsive student/faculty interface |
| Backend | Python + Django REST Framework | One backend language for APIs and the NLP pipeline |
| Database | PostgreSQL | Persistent relational storage for accounts, subjects, enrollment, lectures and timetable |
| Local file storage | Django media storage | Simple and reliable local development |
| Cloud file storage | AWS S3 (optional by environment configuration) | Store uploaded lecture files and generated HLS assets outside the application container |
| Adaptive video | FFmpeg + HLS | Creates multiple video renditions and an HLS master playlist |
| Speech-to-Text | OpenAI Whisper | Local/open-source transcription option named in the synopsis |
| Summarization | TextRank through Sumy | Extractive summarization baseline named in the synopsis |
| Background jobs | Celery + Redis | Keeps audio/video processing outside the web request |
| Live class | Faculty-provided Google Meet / Zoom URL | Link is scheduled and shared with enrolled students; meeting creation itself is handled in Meet/Zoom |
| Notifications | In-app notification; SMTP configurable | Students see timetable updates in their account |
| Development/deployment | VS Code, Git, Postman, Docker | Code management, API testing and repeatable deployment |

PostgreSQL is the source of truth for application records. CSV is not used as the live database because concurrent user, lecture and timetable records need relational constraints. CSV exports can be added later if the guide requires them.

## 4. Run the project on Windows

### Recommended route: Docker Desktop

Install Docker Desktop for Windows and make sure its WSL 2 engine is running. Then:

1. Extract this repository ZIP to a folder such as `C:\Projects\remote-classroom`.
2. Open PowerShell in that folder.
3. Copy `.env.example` to `.env`.
4. Run `docker compose up --build`.
5. Open the frontend at `http://localhost:5173`.
6. The API health check is at `http://localhost:8000/api/health/` and Django admin is at `http://localhost:8000/admin/`.

First build can take time because the backend image installs CPU-only PyTorch, Whisper and FFmpeg. The Whisper model is downloaded when the first transcription job runs.

### Create administrator and demo accounts

In a second PowerShell window, from the project folder:

```powershell
docker compose exec backend python manage.py createsuperuser
docker compose exec backend python manage.py seed_demo
```

For a local demo the seed command creates:

- Faculty: `faculty.demo`
- Student: `student.demo`
- Both passwords: `DemoOnlyChange123!` unless `DEMO_PASSWORD` is set before running the command.

These credentials are for local development only. Change or remove them before the project is exposed to the internet. A student can also register from the sign-in screen. Faculty accounts are created by an administrator so a public user cannot grant themselves faculty privileges.

### First end-to-end test

1. Sign in as `faculty.demo`.
2. Open **Subjects** and confirm the sample subject `CSE-RC101` is present.
3. Open **Lectures** and upload a short, clear-audio MP4 recording (start with a 2–5 minute test video).
4. Wait for the HLS and summary statuses to change from `waiting`/`processing` to `ready`. Processing happens in the `worker` container. Check its logs with `docker compose logs -f worker`.
5. Sign out and sign in as `student.demo`.
6. Open the lecture. Test adaptive video playback and Lite Mode (summary and transcript).
7. As faculty, create a live class with a valid Google Meet or Zoom joining URL. The enrolled student should see an in-app notification and the session in Live classes.

### Useful commands

```powershell
# Show all service logs
docker compose logs -f

# See only Whisper / FFmpeg worker output
docker compose logs -f worker

# Run backend tests
docker compose exec backend python manage.py test classroom

# Check migration state
docker compose exec backend python manage.py showmigrations

# Create a new admin account
docker compose exec backend python manage.py createsuperuser

# Stop containers but keep database/media volumes
docker compose down

# Remove containers AND local database/media data (destructive)
docker compose down -v
```

## 5. Local setup without Docker

This route is more error-prone on Windows because FFmpeg, PostgreSQL, Redis and Whisper/PyTorch must all be installed separately. Docker is recommended. If using native setup, use Python 3.12, Node.js 22, PostgreSQL 16, Redis 7 and FFmpeg, then:

```powershell
$env:CELERY_BROKER_URL = "redis://127.0.0.1:6379/0"
$env:CELERY_RESULT_BACKEND = "redis://127.0.0.1:6379/1"
$env:WHISPER_MODEL = "base"
cd backend
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m nltk.downloader punkt punkt_tab
python manage.py migrate
python manage.py runserver
```

Run Redis and a worker in a second terminal:

```powershell
cd backend
.\.venv\Scripts\Activate.ps1
celery -A config worker --loglevel=INFO --pool=solo
```

Run the frontend in another terminal:

```powershell
cd frontend
npm install
npm run dev
```

Set the environment variables from the root `.env.example` in your shell before starting the services.

## 6. Environment configuration

Important values in `.env`:

- `DJANGO_SECRET_KEY`: replace with a long random value before deployment.
- `DJANGO_DEBUG`: must be `false` in production.
- `DJANGO_ALLOWED_HOSTS`: exact hostnames used by the deployment.
- `DB_*`: PostgreSQL connection for Docker local development, or `DATABASE_URL` for a managed database.
- `CELERY_BROKER_URL`: Redis broker used by the processing worker.
- `WHISPER_MODEL`: `tiny`, `base` or `small`. `base` is the default balance for a laptop/CPU demo. Larger models need more RAM and processing time.
- `MAX_LECTURE_UPLOAD_MB`: application upload limit (Nginx / reverse proxy limits must be at least as large).
- `AWS_STORAGE_BUCKET_NAME`: leave blank for local files; set it and AWS credentials/role for S3.
- `EMAIL_*`: SMTP settings for email notifications. Local development writes outgoing email to the backend console.

## 7. Free Render deployment for the college demo

For a zero-budget demo, use the separate `render.yaml` Blueprint and follow the step-by-step [`DEPLOY_NOW.md`](DEPLOY_NOW.md) checklist (full notes are in `deploy/RENDER_FREE.md`). This profile uses Render Static Site + Free Web Service, Supabase Free PostgreSQL/private storage and the Groq free-plan Whisper endpoint. It does not run Celery or FFmpeg HLS on Render Free; it streams the original MP4/WEBM and uses a bounded Whisper request for Lite Mode. The local Docker profile remains the full Whisper + FFmpeg + Celery implementation.

## 8. Full cloud deployment direction

The repository contains `docker-compose.production.yml` as a deployment starting point. A practical AWS deployment can use:

- EC2 or another container host for Django, React/Nginx and the Celery worker.
- AWS RDS PostgreSQL for persistent relational data.
- AWS S3 for source lecture recordings and generated HLS assets.
- ElastiCache Redis or another managed Redis service for Celery.
- HTTPS through an application load balancer or reverse proxy.
- IAM role credentials rather than hard-coded AWS access keys where possible.

Before public deployment, configure the S3 bucket's CORS rules for HLS playback, a suitable CloudFront distribution/access policy, SMTP credentials, HTTPS, secure secrets and database backups. Do not make a production bucket publicly writable. This repository does not claim that a cloud instance has already been deployed; deployment needs your AWS account, credentials, domain and budget.

## 9. Project structure

```text
remote-classroom/
├── backend/
│   ├── config/                 # Django settings, URLs, Celery setup
│   ├── classroom/               # models, serializers, API, tasks
│   │   ├── services/            # TextRank summarizer
│   │   ├── migrations/           # database schema
│   │   └── management/commands/  # local demo account seed
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/components/          # HLS player and modal
│   ├── src/App.jsx               # student/faculty interface
│   └── Dockerfile
├── docs/                        # SRS and sprint documents
├── deploy/                      # deployment notes
├── docker-compose.yml
└── .env.example
```

## 9. Academic honesty and progress records

Use the source code as a starting point, but understand and be able to explain each module in your project review. Record actual dates, screenshots, test outputs, and work completed in your sprint evidence. Do not submit a planned feature as completed unless you have run it and verified it on your machine.
