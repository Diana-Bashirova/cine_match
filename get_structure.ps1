# ============================================
# Генерация структуры проекта CineMatch
# ============================================

$projectPath = "C:\Users\Админ\desktop\project\cine_match"
$outputFile = "$projectPath\project_structure.txt"

Write-Host "📁 Генерация структуры проекта..." -ForegroundColor Cyan
Write-Host ""

# Заголовок
@"
================================================================================
CineMatch Project Structure
Generated: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
================================================================================

"@ | Out-File -FilePath $outputFile -Encoding UTF8

# Дерево папок
Write-Host "📂 Сканирование папок и файлов..." -ForegroundColor Yellow
tree $projectPath /F /A | Out-File -FilePath $outputFile -Append -Encoding UTF8

# Дополнительные детали
@"

================================================================================
Ключевые файлы (содержимое первых строк):
================================================================================

--- apps/users/urls.py ---
"@ | Out-File -FilePath $outputFile -Append -Encoding UTF8

if (Test-Path "$projectPath\apps\users\urls.py") {
    Get-Content "$projectPath\apps\users\urls.py" | Select-Object -First 15 | Out-File -FilePath $outputFile -Append -Encoding UTF8
} else {
    "❌ Файл не найден!" | Out-File -FilePath $outputFile -Append -Encoding UTF8
}

@"

--- apps/rooms/views.py (первые 25 строк) ---
"@ | Out-File -FilePath $outputFile -Append -Encoding UTF8

if (Test-Path "$projectPath\apps\rooms\views.py") {
    Get-Content "$projectPath\apps\rooms\views.py" | Select-Object -First 25 | Out-File -FilePath $outputFile -Append -Encoding UTF8
} else {
    "❌ Файл не найден!" | Out-File -FilePath $outputFile -Append -Encoding UTF8
}

@"

--- apps/history/views.py (первые 25 строк) ---
"@ | Out-File -FilePath $outputFile -Append -Encoding UTF8

if (Test-Path "$projectPath\apps\history\views.py") {
    Get-Content "$projectPath\apps\history\views.py" | Select-Object -First 25 | Out-File -FilePath $outputFile -Append -Encoding UTF8
} else {
    "❌ Файл не найден!" | Out-File -FilePath $outputFile -Append -Encoding UTF8
}

@"

--- config/urls.py ---
"@ | Out-File -FilePath $outputFile -Append -Encoding UTF8

if (Test-Path "$projectPath\config\urls.py") {
    Get-Content "$projectPath\config\urls.py" | Select-Object -First 30 | Out-File -FilePath $outputFile -Append -Encoding UTF8
} else {
    "❌ Файл не найден!" | Out-File -FilePath $outputFile -Append -Encoding UTF8
}

Write-Host ""
Write-Host "✅ Структура сохранена в:" -ForegroundColor Green
Write-Host "   $outputFile" -ForegroundColor Cyan
Write-Host ""
Write-Host "📄 Открыть файл?" -ForegroundColor Yellow
$open = Read-Host "Введите Y (да) или N (нет)"
if ($open -eq 'Y' -or $open -eq 'y') {
    notepad $outputFile
}
