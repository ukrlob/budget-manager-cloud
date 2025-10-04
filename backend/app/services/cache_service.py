"""
Сервис кэширования для Plaid данных
Упрощенная версия с файловым кэшем для быстрого тестирования
"""

import json
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

class PlaidCacheService:
    """Сервис для управления кэшем Plaid данных (файловая версия)"""
    
    def __init__(self, cache_dir: str = None):
        if cache_dir is None:
            cache_dir = os.path.join(os.getcwd(), 'cache')
        
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
        
        # TTL для разных типов данных (в минутах)
        self.ttl_config = {
            'accounts': 60,      # 1 час
            'transactions': 30,  # 30 минут
            'balance': 15,       # 15 минут
            'institution': 1440  # 24 часа
        }
    
    def _get_cache_key(self, data_type: str, bank_code: str = None, 
                      account_id: str = None, item_id: str = None, **kwargs) -> str:
        """Генерация ключа кэша с учетом item_id для каждого банка"""
        key_parts = [data_type]
        if bank_code:
            key_parts.append(bank_code)
        if item_id:
            key_parts.append(f"item_{item_id}")
        if account_id:
            key_parts.append(account_id)
        
        # Добавляем дополнительные параметры
        for k, v in sorted(kwargs.items()):
            if v is not None:
                key_parts.append(f"{k}_{v}")
        
        return "_".join(key_parts)
    
    def _get_ttl(self, data_type: str) -> int:
        """Получение TTL для типа данных"""
        return self.ttl_config.get(data_type, 30)
    
    async def get_cached_data(self, data_type: str, bank_code: str = None, 
                            account_id: str = None, item_id: str = None, **kwargs) -> Optional[Dict[str, Any]]:
        """Получение данных из кэша"""
        try:
            cache_key = self._get_cache_key(data_type, bank_code, account_id, item_id, **kwargs)
            cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
            
            if os.path.exists(cache_file):
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cached_data = json.load(f)
                
                # Проверяем TTL
                expires_at = datetime.fromisoformat(cached_data.get('expires_at', ''))
                if datetime.utcnow() < expires_at:
                    logger.debug(f"Данные получены из кэша: {cache_key}")
                    return cached_data
                else:
                    # Удаляем истекший файл
                    os.remove(cache_file)
            
            return None
            
        except Exception as e:
            logger.error(f"Ошибка получения данных из кэша: {e}")
            return None
    
    async def cache_data(self, data_type: str, data: Any, bank_code: str = None, 
                        account_id: str = None, item_id: str = None, **kwargs) -> bool:
        """Сохранение данных в кэш"""
        try:
            cache_key = self._get_cache_key(data_type, bank_code, account_id, item_id, **kwargs)
            ttl_minutes = self._get_ttl(data_type)
            expires_at = datetime.utcnow() + timedelta(minutes=ttl_minutes)
            
            cache_file = os.path.join(self.cache_dir, f"{cache_key}.json")
            
            cache_data = {
                'cache_key': cache_key,
                'data_type': data_type,
                'bank_code': bank_code,
                'account_id': account_id,
                'data': data,
                'created_at': datetime.utcnow().isoformat(),
                'expires_at': expires_at.isoformat(),
                'last_updated': datetime.utcnow().isoformat()
            }
            
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, default=str, ensure_ascii=False, indent=2)
            
            logger.debug(f"Данные сохранены в кэш: {cache_key}")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка сохранения данных в кэш: {e}")
            return False
    
    async def invalidate_cache(self, data_type: str = None, bank_code: str = None, 
                             account_id: str = None) -> int:
        """Очистка кэша по критериям"""
        try:
            deleted_count = 0
            
            for filename in os.listdir(self.cache_dir):
                if filename.endswith('.json'):
                    filepath = os.path.join(self.cache_dir, filename)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            cache_data = json.load(f)
                        
                        should_delete = False
                        if data_type and cache_data.get('data_type') == data_type:
                            should_delete = True
                        if bank_code and cache_data.get('bank_code') == bank_code:
                            should_delete = True
                        if account_id and cache_data.get('account_id') == account_id:
                            should_delete = True
                        
                        if should_delete:
                            os.remove(filepath)
                            deleted_count += 1
                            
                    except Exception as e:
                        logger.warning(f"Ошибка обработки файла {filename}: {e}")
                        continue
            
            logger.info(f"Удалено {deleted_count} записей из кэша")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Ошибка очистки кэша: {e}")
            return 0
    
    async def cleanup_expired(self) -> int:
        """Очистка истекших записей"""
        try:
            deleted_count = 0
            current_time = datetime.utcnow()
            
            for filename in os.listdir(self.cache_dir):
                if filename.endswith('.json'):
                    filepath = os.path.join(self.cache_dir, filename)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            cache_data = json.load(f)
                        
                        expires_at = datetime.fromisoformat(cache_data.get('expires_at', ''))
                        if current_time > expires_at:
                            os.remove(filepath)
                            deleted_count += 1
                            
                    except Exception as e:
                        logger.warning(f"Ошибка обработки файла {filename}: {e}")
                        continue
            
            logger.info(f"Удалено {deleted_count} истекших записей из кэша")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Ошибка очистки истекших записей: {e}")
            return 0
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """Статистика кэша"""
        try:
            total_items = 0
            expired_items = 0
            current_time = datetime.utcnow()
            
            # Статистика по типам данных
            type_stats = {data_type: 0 for data_type in self.ttl_config.keys()}
            
            for filename in os.listdir(self.cache_dir):
                if filename.endswith('.json'):
                    filepath = os.path.join(self.cache_dir, filename)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            cache_data = json.load(f)
                        
                        total_items += 1
                        data_type = cache_data.get('data_type', 'unknown')
                        if data_type in type_stats:
                            type_stats[data_type] += 1
                        
                        expires_at = datetime.fromisoformat(cache_data.get('expires_at', ''))
                        if current_time > expires_at:
                            expired_items += 1
                            
                    except Exception as e:
                        logger.warning(f"Ошибка обработки файла {filename}: {e}")
                        continue
            
            return {
                'total_items': total_items,
                'expired_items': expired_items,
                'active_items': total_items - expired_items,
                'type_stats': type_stats,
                'cache_hit_rate': 0.0  # Будет рассчитываться отдельно
            }
            
        except Exception as e:
            logger.error(f"Ошибка получения статистики кэша: {e}")
            return {}
    
    async def get_incremental_data(self, data_type: str, bank_code: str, 
                                 last_update: datetime) -> Optional[Dict[str, Any]]:
        """Получение инкрементальных данных (только новые записи)"""
        try:
            incremental_data = []
            max_last_update = last_update
            
            for filename in os.listdir(self.cache_dir):
                if filename.endswith('.json'):
                    filepath = os.path.join(self.cache_dir, filename)
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            cache_data = json.load(f)
                        
                        if (cache_data.get('data_type') == data_type and 
                            cache_data.get('bank_code') == bank_code):
                            
                            last_updated = datetime.fromisoformat(cache_data.get('last_updated', ''))
                            expires_at = datetime.fromisoformat(cache_data.get('expires_at', ''))
                            
                            if (last_updated > last_update and 
                                datetime.utcnow() < expires_at):
                                
                                data = cache_data.get('data', [])
                                if data:
                                    incremental_data.extend(data if isinstance(data, list) else [data])
                                
                                if last_updated > max_last_update:
                                    max_last_update = last_updated
                                    
                    except Exception as e:
                        logger.warning(f"Ошибка обработки файла {filename}: {e}")
                        continue
            
            if incremental_data:
                return {
                    'data': incremental_data,
                    'last_update': max_last_update.isoformat(),
                    'count': len(incremental_data)
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Ошибка получения инкрементальных данных: {e}")
            return None
