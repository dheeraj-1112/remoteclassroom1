$ErrorActionPreference = "Stop"

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "Created .env from .env.example. Review the values before continuing." -ForegroundColor Yellow
}

Write-Host "Starting Remote Classroom services..." -ForegroundColor Cyan
docker compose up --build
