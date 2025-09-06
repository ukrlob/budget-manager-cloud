# 🚀 Инструкции по созданию GitHub репозитория

## Шаг 1: Создание репозитория на GitHub

### Через веб-интерфейс GitHub:

1. **Перейдите на GitHub.com** и войдите в свой аккаунт
2. **Нажмите кнопку "New repository"** (зеленая кнопка справа)
3. **Заполните форму:**
   - Repository name: `budget-manager-cloud`
   - Description: `Educational project for learning modern web development - Budget Manager Cloud`
   - Visibility: **Public** (важно для демонстрации)
   - НЕ добавляйте README, .gitignore или лицензию (они уже созданы)
4. **Нажмите "Create repository"**

## Шаг 2: Загрузка файлов

### Вариант A: Через GitHub Desktop (рекомендуется)

1. **Скачайте GitHub Desktop:** https://desktop.github.com/
2. **Установите и войдите** в свой GitHub аккаунт
3. **В GitHub Desktop:**
   - File → Add Local Repository
   - Choose → выберите папку `C:\Users\ukrlo\Desktop\budget_cloud`
   - Нажмите "Add Repository"
4. **Опубликуйте репозиторий:**
   - Нажмите "Publish repository"
   - Убедитесь, что "Keep this code private" = **НЕ отмечено**
   - Нажмите "Publish repository"

### Вариант B: Через командную строку (если Git установлен)

```bash
# В папке проекта
git init
git add .
git commit -m "Initial commit: Project setup with online development"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/budget-manager-cloud.git
git push -u origin main
```

## Шаг 3: Настройка GitHub Pages

1. **Перейдите в настройки репозитория:**
   - В репозитории нажмите "Settings"
   - В левом меню выберите "Pages"
2. **Настройте источник:**
   - Source: "Deploy from a branch"
   - Branch: "main"
   - Folder: "/ (root)"
   - Нажмите "Save"
3. **Дождитесь деплоя** (обычно 1-2 минуты)
4. **Ваш сайт будет доступен по адресу:**
   `https://YOUR_USERNAME.github.io/budget-manager-cloud/`

## Шаг 4: Настройка GitHub Codespaces

1. **В репозитории нажмите кнопку "Code"**
2. **Выберите вкладку "Codespaces"**
3. **Нажмите "Create codespace on main"**
4. **Дождитесь загрузки** (может занять несколько минут)
5. **Начните разработку онлайн!**

## Шаг 5: Проверка

### Проверьте, что все работает:

1. **Репозиторий доступен:** https://github.com/YOUR_USERNAME/budget-manager-cloud
2. **GitHub Pages работает:** https://YOUR_USERNAME.github.io/budget-manager-cloud/
3. **Codespaces доступен:** кнопка "Code" → "Codespaces"
4. **Все файлы загружены:**
   - README.md
   - DEVELOPMENT_PLAN.md
   - index.html
   - .github/ папка
   - Все остальные файлы

## 🎉 Готово!

Теперь у вас есть:
- ✅ Публичный GitHub репозиторий
- ✅ Демо-страница на GitHub Pages
- ✅ Настроенный GitHub Codespaces
- ✅ Готовая структура для онлайн-разработки

## Следующие шаги:

1. **Начните разработку** в GitHub Codespaces
2. **Обновляйте прогресс** в DEVELOPMENT_PLAN.md
3. **Делайте регулярные коммиты** для отслеживания прогресса
4. **Используйте Issues** для планирования задач

---

**Проблемы?** Создайте Issue в репозитории или обратитесь за помощью!
