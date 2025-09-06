# 🔧 Настройка Git для проекта

## Установка Git

### Windows
1. Скачайте Git с официального сайта: https://git-scm.com/download/win
2. Запустите установщик и следуйте инструкциям
3. Перезапустите терминал/PowerShell
4. Проверьте установку: `git --version`

### Альтернативный способ (через GitHub Desktop)
1. Скачайте GitHub Desktop: https://desktop.github.com/
2. Установите приложение
3. Войдите в свой GitHub аккаунт
4. Создайте новый репозиторий через интерфейс

## Создание GitHub репозитория

### Способ 1: Через веб-интерфейс GitHub
1. Перейдите на https://github.com
2. Нажмите кнопку "New repository"
3. Название: `budget-manager-cloud`
4. Описание: `Educational project for learning modern web development`
5. Выберите "Public" (публичный)
6. НЕ добавляйте README, .gitignore или лицензию (они уже есть)
7. Нажмите "Create repository"

### Способ 2: Через GitHub CLI (если установлен)
```bash
gh repo create budget-manager-cloud --public --description "Educational project for learning modern web development"
```

## Загрузка файлов

### После установки Git:
```bash
# Инициализация
git init

# Добавление файлов
git add .

# Первый коммит
git commit -m "Initial commit: Project setup with online development"

# Подключение к GitHub
git remote add origin https://github.com/YOUR_USERNAME/budget-manager-cloud.git

# Загрузка
git push -u origin main
```

### Через GitHub Desktop:
1. Откройте GitHub Desktop
2. File → Add Local Repository
3. Выберите папку проекта
4. Publish repository
5. Выберите "Keep this code private" = NO (публичный)
6. Нажмите "Publish repository"

## Проверка

После загрузки проверьте:
- Репозиторий доступен по адресу: https://github.com/YOUR_USERNAME/budget-manager-cloud
- Все файлы загружены
- README.md отображается на главной странице

## Следующие шаги

1. Настроить GitHub Pages для демо-версии
2. Настроить GitHub Codespaces для онлайн-разработки
3. Начать разработку!
