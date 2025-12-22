# Docker Setup Script for News Aggregator Pipeline
# This script stops and restarts Docker containers with pgvector support

Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 59) -ForegroundColor Cyan
Write-Host "News Aggregator - Docker Setup" -ForegroundColor Cyan
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 59) -ForegroundColor Cyan

# Navigate to docker directory
$dockerDir = Join-Path $PSScriptRoot "..\docker"
Push-Location $dockerDir

Write-Host "`n🔄 Stopping existing containers..." -ForegroundColor Yellow
docker-compose down

Write-Host "`n🚀 Starting containers with pgvector support..." -ForegroundColor Yellow
docker-compose up -d

Write-Host "`n⏳ Waiting for services to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

Write-Host "`n📊 Container Status:" -ForegroundColor Cyan
docker-compose ps

Write-Host "`n✅ Docker setup complete!" -ForegroundColor Green
Write-Host "`nNext steps:" -ForegroundColor Cyan
Write-Host "  1. Add Redis config to your .env file:" -ForegroundColor White
Write-Host "     REDIS_HOST=localhost" -ForegroundColor Gray
Write-Host "     REDIS_PORT=6379" -ForegroundColor Gray
Write-Host "`n  2. Run the migration script:" -ForegroundColor White
Write-Host "     python scripts/migrate_database.py" -ForegroundColor Gray
Write-Host "`n  3. Test the infrastructure:" -ForegroundColor White
Write-Host "     python scripts/test_infrastructure.py" -ForegroundColor Gray

Pop-Location
