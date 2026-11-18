# Deploy Remote Classroom for ₹0 (Render + Supabase + Groq)

This is the fastest free-tier deployment profile supplied with this project. It is for a college demonstration, not a production service with uptime guarantees.

## Services used

- Render Static Site: React frontend (free).
- Render Docker Web Service: Django API (free, sleeps after inactivity).
- Supabase Free: PostgreSQL and private object storage.
- Groq developer API: hosted Whisper transcription for small video files. Account quota and model access apply.

The free deployment plays the original MP4/WEBM directly. FFmpeg HLS processing and a separate Celery worker are disabled because Render does not offer free background workers or persistent disks. The full local Docker profile keeps the FFmpeg + local Whisper + Celery pipeline.

## Step 1 — Supabase

1. Create a Free Supabase project. Choose a region near Render's Singapore region where available.
2. Open **Project Settings → Database → Connect** and copy the **Transaction pooler** URI. It should use port `6543` and `sslmode=require`. Replace the password placeholder. If your database password contains URL-reserved characters, URL-encode it before placing it in the URI.
3. Open **Storage** and create a bucket named `remote-classroom`. Keep the bucket **private**.
4. Open the Storage S3 connection/settings area and copy the S3 endpoint, access key ID, secret access key and region. Use the S3 credentials—not the Supabase `anon` or service-role API keys.
5. Do not put any of these secrets in React variables or GitHub.

## Step 2 — Groq API key

1. Create a Groq developer account and an API key.
2. Confirm `whisper-large-v3-turbo` is available to your account and check the account's current rate limits.
3. Use short sample recordings first. The free-tier direct-upload limit for Groq Speech-to-Text is 25 MB. This application enforces the same maximum.

## Step 3 — Push to GitHub

Create an empty GitHub repository (for example `remote-classroom`). From PowerShell in this project folder:

```powershell
git init
git add .
git commit -m "Prepare Remote Classroom free Render deployment"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/remote-classroom.git
git push -u origin main
```

Replace `YOUR-USERNAME`. Do not add `.env` files or secrets to the repository.

## Step 4 — Deploy the Render Blueprint

1. Sign in to Render and choose **New → Blueprint**.
2. Connect the GitHub repository and select its `render.yaml`.
3. Render should detect two services: `remote-classroom-api` (Docker web service, Free) and `remote-classroom-web` (Static Site, Free).
4. During Blueprint setup, enter these values when Render prompts for the `sync: false` variables:
   - `DATABASE_URL`: Supabase Transaction Pooler URI.
   - `AWS_STORAGE_BUCKET_NAME`: `remote-classroom`.
   - `AWS_ACCESS_KEY_ID`: Supabase S3 access key.
   - `AWS_SECRET_ACCESS_KEY`: Supabase S3 secret.
   - `AWS_S3_ENDPOINT_URL`: Supabase S3 endpoint, typically `https://PROJECT_REF.storage.supabase.co/storage/v1/s3` (copy the exact endpoint from Supabase).
   - `AWS_S3_REGION_NAME`: exact region shown by Supabase S3 settings.
   - `GROQ_API_KEY`: your Groq key.
   - `BOOTSTRAP_FACULTY_USERNAME`: choose a faculty login username.
   - `BOOTSTRAP_FACULTY_PASSWORD`: set a strong unique password; do not reuse a personal password.
   - `BOOTSTRAP_FACULTY_EMAIL`: a team email address.
5. Apply the Blueprint and let both services deploy.

If Render changes either service hostname (for example because the name is already taken), update the API service's `CORS_ALLOWED_ORIGINS` and `CSRF_TRUSTED_ORIGINS`, and update the static site's `VITE_API_URL` to the actual API address followed by `/api`. Save the environment changes and redeploy the static site so Vite embeds the new API URL.

## Step 5 — Smoke test

1. Open `https://YOUR-API.onrender.com/api/health/`. Expect JSON with `"status": "ok"`.
2. Open the frontend URL and sign in using the faculty credentials configured above.
3. Create a subject and note its subject code.
4. Register a student account from the Student registration tab and enroll that student in the subject.
5. As faculty, upload a short MP4 or WEBM recording no larger than 25 MB. Keep the page open while Whisper and TextRank run.
6. Sign in as the student and check that the lecture video and Lite Mode summary are available.
7. Schedule a future Google Meet or Zoom link. Confirm the enrolled student sees the live class and in-app notification.

## Free plan limits to remember

- Render Free web services sleep after 15 minutes without traffic and take about a minute to wake. The workspace has a monthly included pool of 750 Free instance hours. Free web services have ephemeral disks; never store lecture files or the only copy of the database on Render's local filesystem.
- Supabase Free includes 500 MB database storage and 1 GB file storage. Free projects can pause after a week of low database activity. Keep lecture test files small and delete unused ones from Storage.
- Groq's current Speech-to-Text docs list a 25 MB file cap for the free tier. Free model quotas/rate limits can change and are account-specific; inspect your Groq Limits page.
- Render Free does not provide free background workers or persistent disks. The free cloud profile therefore skips HLS transcoding and performs a small transcription request through Groq. The full local Docker build has the more complete offline/local processing pipeline.
- This configuration has not been deployed to your accounts from this workspace. A successful deploy still requires you to connect GitHub and enter your Supabase/Groq credentials in Render, then run the smoke test above.
