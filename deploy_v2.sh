#!/bin/bash

# Скрипт развертывания Budget Manager Cloud v2.0 в Google Cloud

echo "🚀 Начинаем развертывание Budget Manager Cloud v2.0..."

# Настройки проекта
PROJECT_ID="budget-manager-cloud"
SERVICE_NAME="budget-manager-cloud-v2"
REGION="us-central1"
IMAGE_NAME="gcr.io/$PROJECT_ID/$SERVICE_NAME"

echo "📦 Сборка Docker образа..."
docker build -t $IMAGE_NAME .

echo "📤 Загрузка образа в Google Container Registry..."
docker push $IMAGE_NAME

echo "🚀 Развертывание в Google Cloud Run..."
gcloud run deploy $SERVICE_NAME \
    --image $IMAGE_NAME \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --memory 2Gi \
    --cpu 2 \
    --max-instances 10 \
    --set-env-vars="DATABASE_URL=postgresql://postgres:BudgetCloud2025!@34.46.9.135:5432/budget_cloud"

echo "✅ Развертывание завершено!"
echo "🌐 URL: https://$SERVICE_NAME-527220375721.$REGION.run.app"
echo ""
echo "🔧 Для настройки AI консультанта добавьте переменную GEMINI_API_KEY"
echo "🏦 Для банковских интеграций добавьте учетные данные банков"
