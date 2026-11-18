# Free Render deployment (₹0 demo setup)

This profile is deliberately lighter than the local Docker Compose build. It is intended for a college demonstration, not a production service with guaranteed uptime.

## What runs where

- Render Static Site: React frontend.
- Render Free Web Service: lightweight Django REST API (512 MB RAM; spins down when idle).
- Supabase Free: PostgreSQL and private object storage for lecture videos.
- Groq Free API plan: hosted Whisper transcription for small uploaded videos (max 25 MB per transcription request; account rate limits apply).
- Sumy/TextRank: summarization runs in the Django API after the transcript is returned.

HLS/FFmpeg transcoding and the Celery worker are disabled on this free profile. The original MP4/WEBM file is played directly. The full local Docker profile still contains FFmpeg + open-source Whisper + Celery/HLS processing.

## 1. Create Supabase project

1. Create a project on Supabase Free.
2. In Project Settings → Database, select the **Transaction pooler** connection string. Copy the URI and replace the placeholder password. It should have `sslmode=require` and normally uses port `6543`.
3. In Storage, create a **private** bucket named `remote-classroom`.
4. In Storage settings, enable S3 protocol access. Generate an S3 Access Key ID and Secret Access Key. Copy the S3 endpoint and the exact region shown in Supabase's S3 configuration screen.
5. Keep the access key and secret private. Do not put them in React/Vite environment variables or commit them to GitHub.

Supabase supports S3-compatible storage and signed URLs. The bucket is private so lecture URLs are signed by the backend for enrolled users.

## 2. Create a Groq API key

1. Create a Groq developer account and generate an API key.
2. Check that the account can use `whisper-large-v3-turbo` on the Free plan and review current Audio Seconds / Day limits.
3. This API key must be configured only as `GROQ_API_KEY` on the Render backend. Never expose it in frontend code.
4. The free endpoint accepts files up to 25 MB. Upload MP4/WEBM clips for the first demo; use a short 2–5 minute sample compressed below 25 MB.

## 3. Push this folder to GitHub

From PowerShell inside the extracted `remote-classroom` folder:

```powershell
git init
git add .
git commit -m "Prepare Remote Classroom free Render deployment"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/remote-classroom.git
git push -u origin main
```

Create an empty GitHub repository first. Do not add `.env` or secret files.

## 4. Deploy the Blueprint

1. Sign in to Render and choose **New → Blueprint**.
2. Connect the GitHub repository and select its `render.yaml`.
3. Review the services: `remote-classroom-api` and `remote-classroom-web` should both be on Free.
4. Fill the requested secret values:
   - `DATABASE_URL`: Supabase Transaction Pooler URI.
   - `AWS_STORAGE_BUCKET_NAME`: `remote-classroom`.
   - `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`.
   - `AWS_S3_ENDPOINT_URL`: Supabase S3 endpoint, e.g. `https://PROJECT_REF.storage.supabase.co/storage/v1/s3`.
   - `AWS_S3_REGION_NAME`: exact region from Supabase S3 settings.
   - `GROQ_API_KEY`.
   - `BOOTSTRAP_FACULTY_USERNAME`, `BOOTSTRAP_FACULTY_PASSWORD`, `BOOTSTRAP_FACULTY_EMAIL` for a faculty account.
   - Optionally set the `BOOTSTRAP_ADMIN_*` values for a separate admin account.
5. Apply the Blueprint and wait for both deploys to finish.

If Render assigns different hostnames, update these backend variables to match the actual URLs:
- `DJANGO_ALLOWED_HOSTS`: backend hostname only (no `https://`).
- `CORS_ALLOWED_ORIGINS`: frontend origin.
- `CSRF_TRUSTED_ORIGINS`: include the frontend and backend HTTPS origins.
And update `VITE_API_URL` on the frontend to `https://ACTUAL-BACKEND-HOST/api`, then trigger a frontend redeploy.

## 5. First test

1. Open `https://remote-classroom-api.onrender.com/api/health/` and confirm `status: ok`.
2. Open the frontend URL and sign in with the bootstrap faculty account.
3. Create a subject and sign out.
4. Register a student account, enroll in the subject, then sign out.
5. Sign back in as faculty and upload a short MP4/WEBM video under 25 MB.
6. Wait for the Whisper transcript and TextRank summary to return. Open the lecture as the student and test original video playback and Lite Mode.
7. Schedule a Google Meet/Zoom joining URL and verify the student notification.

## Important free-tier boundaries

- Render Free web services sleep after 15 minutes without traffic and may take about a minute to wake up.
- Render Free web services have ephemeral filesystems, so lecture media must use Supabase Storage.
- Render Free does not provide free background workers or persistent disks. This profile therefore skips HLS transcoding and runs transcription as a bounded request.
- Supabase Free database is 500 MB and storage is 1 GB; Free projects may pause after a week of low activity. Review the current dashboard quotas before uploading many recordings.
- Groq has free-plan rate limits and 25 MB audio/video input limit; the account's current limits are authoritative.
- This is a demonstration deployment. Keep video content small and avoid uploading private classroom recordings without the appropriate permissions.
