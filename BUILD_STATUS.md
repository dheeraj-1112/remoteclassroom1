# Build status — initial Sprint I–III codebase

## Built into the source tree

- Django REST API, token authentication and student/faculty roles.
- Subject creation and student enrollment.
- Lecture upload and access control.
- Background FFmpeg HLS generation with multiple quality renditions and source-video fallback.
- Live-class scheduling with a faculty-provided Meet/Zoom joining URL.
- In-app notifications for students enrolled in the selected subject.
- Background OpenAI Whisper transcription and Sumy TextRank summarization.
- Lite Mode summary view, full transcript view and processing status/error display.
- PostgreSQL migration, demo-data command, backend API tests, React interface, Docker Compose setup, SRS, sprint plans, architecture and Postman collection.

## Deliberately not in this build

- Per-lecture Doubt/Q&A feature — scheduled for Sprint IV.
- Automatic Google Meet/Zoom room creation — faculty creates the meeting externally and pastes its URL.
- Fully provisioned cloud production environment — deployment instructions and production Compose template are included, but an AWS account, RDS, Redis, S3, CloudFront, domain and credentials must be configured by the team.

## Free Render demonstration profile

- Render Blueprint for the Django API and React static site.
- Supabase Free PostgreSQL and private S3-compatible object storage.
- Groq-hosted Whisper transcription for eligible small MP4/WEBM uploads (the Groq free-plan limits apply).
- TextRank/Sumy runs in the Django API.
- Free profile skips Celery workers and FFmpeg HLS. It serves the original MP4/WEBM rather than claiming adaptive HLS playback.

## Validation performed here

- Python source files passed syntax compilation.
- React JSX files passed syntax parsing with the installed TypeScript parser.
- Render Blueprint YAML parsed and the expected two services were confirmed.
- Postman collection and Docker Compose YAML files parsed successfully.

## Runtime validation still required

The current authoring environment did not have Docker or Django installed and could not complete npm dependency installation, so Django migrations/backend tests, full Vite build, browser tests, live Supabase connections, object storage uploads, Groq transcription and FFmpeg conversion have **not** been run here. The free Render profile can be deployed without Docker Desktop on your laptop because Render builds the Dockerfile remotely. Follow `DEPLOY_NOW.md` and complete the smoke test there. Install Docker Desktop only when you want to run the full local Docker profile with FFmpeg and local Whisper. Save screenshots and logs as Sprint evidence only after each test passes.
