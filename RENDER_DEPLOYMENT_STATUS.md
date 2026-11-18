# Render free deployment profile – implementation notes

## Config files added
- `render.yaml` – Render Blueprint (API + static frontend).
- `backend/Dockerfile.render` – slim backend image without local PyTorch/Whisper or FFmpeg.
- `backend/requirements-render.txt` – free-tier Python dependencies.
- `deploy/RENDER_FREE.md` – Supabase, Groq and Render setup steps.

## Application changes
- Supabase S3-compatible private storage settings are supported through environment variables.
- Supabase transaction pooler URL is supported with psycopg prepared statements disabled for transaction pooling.
- `FREE_TIER_MODE` skips Celery/HLS jobs and uses a direct, authenticated summary-generation action with hosted Whisper.
- Original MP4/WEBM playback is retained when adaptive HLS is not created.
- Lecture uploads are capped at 25 MB and MP4/WEBM for the free hosted transcription route.
- Faculty/admin bootstrap accounts can be created from Render environment variables, without Render Shell access.

## Preflight checks performed
- Python backend files passed `compileall` / bytecode syntax compilation.
- React JSX files passed syntax parsing with the installed TypeScript JSX parser.
- `render.yaml` parsed successfully and contains the expected Docker API service and static frontend service.
- The free deployment setup guide and environment variable checklist are included.

## Not claimed as verified
No Render, Supabase, Groq or GitHub account has been connected from this workspace. No online deployment has been performed. Docker and Django are not installed in this authoring environment, and npm dependencies could not be downloaded here. Therefore, Django migrations/tests, the Render Docker build, Supabase connectivity, object uploads, hosted transcription and browser end-to-end testing still need to be run after the user's accounts are connected. A successful syntax/configuration preflight is not the same as a live deployment test.
