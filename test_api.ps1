# ============================================
# Автоматическая проверка всех API endpoints
# ============================================

$baseUrl = "http://127.0.0.1:8000/api"
$successCount = 0
$failCount = 0

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  CineMatch API - Автоматическая проверка" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# 1. Получаем токен
Write-Host "🔐 Получение токена..." -ForegroundColor Yellow
try {
    $tokenResponse = Invoke-RestMethod -Uri "$baseUrl/token/" `
        -Method POST `
        -ContentType "application/json" `
        -Body '{"username":"admin","password":"admin123"}'
    $token = $tokenResponse.access
    $headers = @{ "Authorization" = "Bearer $token" }
    Write-Host "✅ Токен получен" -ForegroundColor Green
} catch {
    Write-Host "❌ Не удалось получить токен: $_" -ForegroundColor Red
    exit 1
}
Write-Host ""

# 2. Список endpoints для проверки
$endpoints = @(
    # Users
    @{ Name = "GET /users/me/"; Method = "GET"; Url = "$baseUrl/users/me/"; Expected = 200 },
    @{ Name = "PATCH /users/me/preferences/"; Method = "PATCH"; Url = "$baseUrl/users/me/preferences/"; Body = '{"genres":["Action"]}' ; Expected = 200 },
    
    # Rooms
    @{ Name = "GET /rooms/"; Method = "GET"; Url = "$baseUrl/rooms/"; Expected = 200 },
    @{ Name = "GET /rooms/my-rooms/"; Method = "GET"; Url = "$baseUrl/rooms/my-rooms/"; Expected = 200 },
    @{ Name = "POST /rooms/create/"; Method = "POST"; Url = "$baseUrl/rooms/create/"; Body = '{"code":"auto_test"}'; Expected = 201 },
    
    # History
    @{ Name = "GET /history/"; Method = "GET"; Url = "$baseUrl/history/"; Expected = 200 },
    @{ Name = "GET /history/ratings/list/"; Method = "GET"; Url = "$baseUrl/history/ratings/list/"; Expected = 200 },
    
    # Recommendations
    @{ Name = "POST /recommendations/personal/"; Method = "POST"; Url = "$baseUrl/recommendations/personal/"; Body = '{"genres":["Action"],"context":{}}'; Expected = 200 },
    
    # Movies
    @{ Name = "GET /movies/"; Method = "GET"; Url = "$baseUrl/movies/"; Expected = 200 }
)

# 3. Тестирование каждого endpoint
Write-Host "🧪 Тестирование endpoints..." -ForegroundColor Yellow
Write-Host ""

foreach ($ep in $endpoints) {
    $params = @{
        Uri = $ep.Url
        Method = $ep.Method
        Headers = $headers
    }
    
    if ($ep.Body) {
        $params.ContentType = "application/json"
        $params.Body = $ep.Body
    }
    
    try {
        $response = Invoke-WebRequest @params -UseBasicParsing
        $statusCode = $response.StatusCode
        
        if ($statusCode -eq $ep.Expected) {
            Write-Host "✅ $($ep.Name) → $statusCode" -ForegroundColor Green
            $successCount++
        } else {
            Write-Host "⚠️  $($ep.Name) → $statusCode (ожидалось $($ep.Expected))" -ForegroundColor Yellow
            $failCount++
        }
    } catch {
        $statusCode = $_.Exception.Response.StatusCode.value__
        Write-Host "❌ $($ep.Name) → $statusCode" -ForegroundColor Red
        $failCount++
    }
}

# 4. Итоговая статистика
Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Результаты проверки" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "✅ Успешно: $successCount" -ForegroundColor Green
Write-Host "❌ Ошибок: $failCount" -ForegroundColor Red
Write-Host "📊 Всего: $($endpoints.Count)" -ForegroundColor Cyan
Write-Host ""

if ($failCount -eq 0) {
    Write-Host "🎉 Все endpoints работают корректно!" -ForegroundColor Green
} else {
    Write-Host "⚠️  Обнаружены проблемы. Проверьте логи выше." -ForegroundColor Yellow
}
