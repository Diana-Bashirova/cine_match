# ============================================
# CineMatch - Быстрый запуск
# ============================================

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  🎬 CineMatch - Запуск приложения" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Проверка Docker
Write-Host "🔍 Проверка Docker..." -ForegroundColor Yellow
try {
    docker --version | Out-Null
    Write-Host "✅ Docker найден" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker не установлен! Скачайте с https://docker.com" -ForegroundColor Red
    exit 1
}

# Проверка docker-compose
try {
    docker-compose --version | Out-Null
    Write-Host "✅ Docker Compose найден" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker Compose не установлен!" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "📦 Запуск контейнеров..." -ForegroundColor Yellow
docker-compose up --build -d

Write-Host ""
Write-Host "⏳ Ожидание запуска сервера..." -ForegroundColor Yellow
Start-Sleep -Seconds 15

# Проверка работоспособности
Write-Host "🔍 Проверка сервера..." -ForegroundColor Yellow
try {
    $response = Invoke-WebRequest -Uri "http://127.0.0.1:3000" -UseBasicParsing -TimeoutSec 5
    if ($response.StatusCode -eq 200) {
        Write-Host "✅ Сервер запущен!" -ForegroundColor Green
    }
} catch {
    Write-Host "⚠️  Сервер ещё запускается..." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  🎉 Приложение запущено!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "🌐 Откройте в браузере:" -ForegroundColor Cyan
Write-Host "   http://127.0.0.1:3000" -ForegroundColor White
Write-Host ""
Write-Host "📚 Swagger API:" -ForegroundColor Cyan
Write-Host "   http://127.0.0.1:8000/api/schema/swagger-ui/" -ForegroundColor White
Write-Host ""
Write-Host "🔑 Тестовые аккаунты:" -ForegroundColor Cyan
Write-Host "   Логин: admin | Пароль: admin123" -ForegroundColor White
Write-Host ""
Write-Host "⏹  Для остановки: .\stop.ps1" -ForegroundColor Yellow
Write-Host ""

# Открыть браузер
Start-Process "http://127.0.0.1:3000"
