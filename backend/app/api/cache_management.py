"""
API для управления кэшем Plaid данных
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from ..services.cache_service import PlaidCacheService
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

# Глобальный экземпляр сервиса кэша (создается при первом использовании)
cache_service = None

def get_cache_service():
    global cache_service
    if cache_service is None:
        cache_service = PlaidCacheService()
    return cache_service

@router.get("/cache/stats")
async def get_cache_stats():
    """Получение статистики кэша"""
    try:
        cache_svc = get_cache_service()
        stats = await cache_svc.get_cache_stats()
        return {
            "success": True,
            "stats": stats,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Ошибка получения статистики кэша: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/cache/cleanup")
async def cleanup_cache():
    """Очистка истекших записей из кэша"""
    try:
        cache_svc = get_cache_service()
        deleted_count = await cache_svc.cleanup_expired()
        return {
            "success": True,
            "deleted_count": deleted_count,
            "message": f"Удалено {deleted_count} истекших записей"
        }
    except Exception as e:
        logger.error(f"Ошибка очистки кэша: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/cache/invalidate")
async def invalidate_cache(
    data_type: Optional[str] = None,
    bank_code: Optional[str] = None,
    account_id: Optional[str] = None
):
    """Очистка кэша по критериям"""
    try:
        cache_svc = get_cache_service()
        deleted_count = await cache_svc.invalidate_cache(
            data_type=data_type,
            bank_code=bank_code,
            account_id=account_id
        )
        
        criteria = []
        if data_type:
            criteria.append(f"тип: {data_type}")
        if bank_code:
            criteria.append(f"банк: {bank_code}")
        if account_id:
            criteria.append(f"счет: {account_id}")
        
        criteria_str = ", ".join(criteria) if criteria else "все записи"
        
        return {
            "success": True,
            "deleted_count": deleted_count,
            "message": f"Удалено {deleted_count} записей ({criteria_str})"
        }
    except Exception as e:
        logger.error(f"Ошибка очистки кэша: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/cache/incremental/{bank_code}")
async def get_incremental_data(
    bank_code: str,
    data_type: str = "transactions",
    last_update: Optional[str] = None
):
    """Получение инкрементальных данных"""
    try:
        if last_update:
            last_update_dt = datetime.fromisoformat(last_update.replace('Z', '+00:00'))
        else:
            last_update_dt = datetime.utcnow() - timedelta(days=1)
        
        cache_svc = get_cache_service()
        incremental_data = await cache_svc.get_incremental_data(
            data_type=data_type,
            bank_code=bank_code,
            last_update=last_update_dt
        )
        
        if incremental_data:
            return {
                "success": True,
                "data": incremental_data,
                "has_new_data": True
            }
        else:
            return {
                "success": True,
                "data": None,
                "has_new_data": False,
                "message": "Нет новых данных"
            }
    except Exception as e:
        logger.error(f"Ошибка получения инкрементальных данных: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/cache/health")
async def cache_health_check():
    """Проверка здоровья кэша"""
    try:
        cache_svc = get_cache_service()
        stats = await cache_svc.get_cache_stats()
        
        # Простая проверка здоровья
        is_healthy = stats.get('total_items', 0) >= 0
        
        return {
            "success": True,
            "healthy": is_healthy,
            "stats": stats,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Ошибка проверки здоровья кэша: {e}")
        return {
            "success": False,
            "healthy": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }
