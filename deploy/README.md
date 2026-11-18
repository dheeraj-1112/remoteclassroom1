# Cloud deployment checklist

The project is built locally first. Do not deploy an untested container or expose Django with `DEBUG=true`.

## Suggested AWS layout

```text
Student / Faculty browser
         |
       HTTPS
         |
 Application Load Balancer / Nginx
       /             \
React static site    Django REST API
                         |
                  PostgreSQL (RDS)
                         |
                 Redis (managed)
                         |
                   Celery worker
                    /        \
          Whisper + TextRank   FFmpeg / HLS
                    \        /
                    AWS S3 + CloudFront
```

## Before launch

1. Create an RDS PostgreSQL database and a Redis endpoint.
2. Create a private S3 bucket for lecture uploads and generated HLS assets.
3. Create a CloudFront distribution with the S3 bucket as a private origin using Origin Access Control (OAC). Set `AWS_S3_CUSTOM_DOMAIN` to the CloudFront hostname. Keep `AWS_QUERYSTRING_AUTH=false` only when the CloudFront distribution is correctly allowed to read the private bucket.
4. Configure S3 CORS using `s3-cors.json` and replace the localhost origin with the deployed frontend origin.
5. Create `.env.production` based on `.env.example` and set:
   - `DJANGO_DEBUG=false`
   - a new random `DJANGO_SECRET_KEY`
   - `DJANGO_ALLOWED_HOSTS` to the deployed hostname(s)
   - `CSRF_TRUSTED_ORIGINS` to the HTTPS origin(s)
   - `CORS_ALLOWED_ORIGINS` to the frontend origin
   - `DATABASE_URL` to RDS
   - `CELERY_BROKER_URL` and `CELERY_RESULT_BACKEND` to the managed Redis service
   - `AWS_STORAGE_BUCKET_NAME`, `AWS_S3_REGION_NAME`, `AWS_S3_CUSTOM_DOMAIN`
   - SMTP credentials if email notifications are enabled later
6. Attach an IAM role to the app host with the minimum S3 permissions required. Do not commit static AWS access keys.
7. Configure the load balancer / reverse proxy for HTTPS, request body sizes (over the configured lecture upload size), and long-running upload/read timeouts.
8. Run database migrations and create a real administrator account. Do not run `seed_demo` on production.
9. Test HLS playback from the CloudFront origin from a browser outside the server network.
10. Configure database backups, application logs, worker monitoring and a retention policy for large video files.

## Deployment commands

After `.env.production` is configured and the host has Docker Compose:

```bash
docker compose -f docker-compose.production.yml build
docker compose -f docker-compose.production.yml up -d
```

Run an admin creation command against the backend container:

```bash
docker compose -f docker-compose.production.yml exec backend python manage.py createsuperuser
```

## Operational notes

- Whisper and FFmpeg are CPU/memory intensive. Start with one Celery worker process and monitor RAM before increasing concurrency.
- Use `WHISPER_MODEL=base` for an initial CPU demonstration. Larger models may improve transcription but increase resource use and processing time.
- Keep source lecture files and HLS renditions in durable object storage. Do not store only inside a disposable container layer.
- Set up a CloudFront cache policy that respects HLS playlist refreshes and handles `.m3u8`/`.ts` content types.
- Use managed Redis or a private Redis container reachable only by the application network.
- Add an antivirus/file-validation stage before accepting unrestricted public uploads if the deployment is opened beyond the project team.
- Schedule periodic security updates for Python, Node, Django, DRF, Nginx and base container images.

This is a deployment plan and configuration template, not a claim that an AWS environment has already been provisioned.
