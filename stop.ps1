# ============================================
# CineMatch - Остановка приложения
# ============================================

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  ⏹  CineMatch - Остановка приложения" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host " Остановка контейнеров..." -ForegroundColor Yellow
docker-compose down

Write-Host ""
Write-Host "✅ Приложение остановлено" -ForegroundColor Green
Write-Host ""
Write-Host " Для запуска: .\start.ps1" -ForegroundColor Yellow
