# Скрипт быстрого развертывания системы анализа скриншотов
# Запускать с правами администратора

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Развертывание системы анализа скриншотов" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Проверка Docker
Write-Host "Проверка Docker..." -ForegroundColor Yellow
try {
    $dockerVersion = docker --version
    Write-Host "✓ Docker установлен: $dockerVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ Docker не найден! Установите Docker Desktop." -ForegroundColor Red
    exit 1
}

# Создание структуры директорий
Write-Host ""
Write-Host "Создание структуры директорий..." -ForegroundColor Yellow

$directories = @(
    "storage\screenshots",
    "storage\database",
    "storage\uploads",
    "incoming"
)

foreach ($dir in $directories) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Host "  ✓ Создано: $dir" -ForegroundColor Green
    } else {
        Write-Host "  ⊙ Существует: $dir" -ForegroundColor Gray
    }
}

# Проверка .env файла
Write-Host ""
Write-Host "Проверка конфигурации..." -ForegroundColor Yellow

if (-not (Test-Path ".env")) {
    Write-Host "⚠️  Файл .env не найден!" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Создайте файл .env вручную или запустите setup.py:" -ForegroundColor Cyan
    Write-Host "  python setup.py" -ForegroundColor White
    Write-Host ""
    
    $createEnv = Read-Host "Создать пример .env файла? (y/n)"
    if ($createEnv -eq "y") {
        Copy-Item ".env.example" ".env"
        Write-Host "✓ Создан .env файл. Отредактируйте его перед запуском!" -ForegroundColor Green
        Write-Host "  Не забудьте установить ADMIN_PASSWORD_HASH и AUTH_SALT" -ForegroundColor Yellow
    }
} else {
    Write-Host "✓ Файл .env найден" -ForegroundColor Green
}

# Проверка docker-compose.yml
Write-Host ""
Write-Host "Проверка docker-compose.yml..." -ForegroundColor Yellow

if (-not (Test-Path "docker-compose.yml")) {
    Write-Host "❌ Файл docker-compose.yml не найден!" -ForegroundColor Red
    exit 1
} else {
    Write-Host "✓ docker-compose.yml найден" -ForegroundColor Green
}

# Предупреждение о настройке пути
Write-Host ""
Write-Host "ВАЖНО: Проверьте docker-compose.yml!" -ForegroundColor Yellow
Write-Host "Измените путь монтирования тома для data-collector:" -ForegroundColor White
Write-Host "  volumes:" -ForegroundColor Gray
Write-Host "    - D:/Скрин:/app/incoming:ro  # <-- Укажите ваш путь" -ForegroundColor Gray
Write-Host ""

$continue = Read-Host "Продолжить развертывание? (y/n)"
if ($continue -ne "y") {
    Write-Host "❌ Развертывание отменено" -ForegroundColor Red
    exit 0
}

# Сборка и запуск
Write-Host ""
Write-Host "Сборка Docker образов..." -ForegroundColor Yellow
docker-compose build

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Ошибка сборки!" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Запуск контейнеров..." -ForegroundColor Yellow
docker-compose up -d

if ($LASTEXITCODE -ne 0) {
    Write-Host "❌ Ошибка запуска!" -ForegroundColor Red
    exit 1
}

# Ожидание запуска
Write-Host ""
Write-Host "Ожидание запуска сервисов..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# Проверка статуса
Write-Host ""
Write-Host "Статус контейнеров:" -ForegroundColor Yellow
docker-compose ps

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "✅ Развертывание завершено!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Дашборд доступен по адресу:" -ForegroundColor Cyan
Write-Host "  http://localhost:8501" -ForegroundColor White
Write-Host ""
Write-Host "Для просмотра логов:" -ForegroundColor Cyan
Write-Host "  docker-compose logs -f" -ForegroundColor White
Write-Host ""
Write-Host "Для остановки системы:" -ForegroundColor Cyan
Write-Host "  docker-compose down" -ForegroundColor White
Write-Host ""
