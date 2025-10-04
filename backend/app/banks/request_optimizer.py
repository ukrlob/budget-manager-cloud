"""
Система оптимизации банковских запросов
Умное управление лимитами и кэшированием
"""

from typing import List, Dict, Any, Optional
import asyncio
import logging
from datetime import datetime, timedelta
import json
import hashlib
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)


class RequestPriority(Enum):
    """Приоритеты запросов"""
    CRITICAL = 1    # Критически важные (балансы, новые транзакции)
    HIGH = 2        # Важные (обновления счетов)
    MEDIUM = 3      # Средние (исторические данные)
    LOW = 4         # Низкие (аналитика, отчеты)


@dataclass
class RequestInfo:
    """Информация о запросе"""
    id: str
    bank_name: str
    method: str
    priority: RequestPriority
    timestamp: datetime
    success: bool
    response_time: float
    data_size: int


class RequestOptimizer:
    """
    Умная система оптимизации банковских запросов
    """
    
    def __init__(self):
        self.request_history = []
        self.cache = {}
        self.rate_limits = {
            'plaid': {'limit': 100, 'used': 0, 'reset_date': None},
            'selenium': {'limit': float('inf'), 'used': 0, 'reset_date': None},
            'api': {'limit': float('inf'), 'used': 0, 'reset_date': None}
        }
        self.optimization_rules = []
        self._setup_optimization_rules()
    
    def _setup_optimization_rules(self):
        """Настройка правил оптимизации"""
        self.optimization_rules = [
            {
                'name': 'plaid_rate_limit',
                'condition': lambda: self.rate_limits['plaid']['used'] >= self.rate_limits['plaid']['limit'] * 0.9,
                'action': 'switch_to_selenium',
                'message': 'Plaid лимит почти исчерпан, переключаемся на Selenium'
            },
            {
                'name': 'cache_hit_rate_low',
                'condition': lambda: self._get_cache_hit_rate() < 0.3,
                'action': 'increase_cache_ttl',
                'message': 'Низкий процент попаданий в кэш, увеличиваем время кэширования'
            },
            {
                'name': 'high_error_rate',
                'condition': lambda: self._get_error_rate() > 0.2,
                'action': 'reduce_request_frequency',
                'message': 'Высокий процент ошибок, снижаем частоту запросов'
            }
        ]
    
    async def should_make_request(self, bank_name: str, method: str, priority: RequestPriority) -> bool:
        """
        Определение, стоит ли делать запрос
        """
        try:
            # Проверяем лимиты
            if not await self._check_rate_limits(method):
                logger.warning(f"Лимит запросов исчерпан для {method}")
                return False
            
            # Проверяем кэш
            cache_key = self._generate_cache_key(bank_name, method, priority)
            if await self._is_cached_data_valid(cache_key):
                logger.info(f"Данные найдены в кэше для {bank_name}")
                return False
            
            # Проверяем приоритет
            if not await self._is_priority_justified(priority):
                logger.info(f"Приоритет {priority.name} не оправдывает запрос")
                return False
            
            # Проверяем правила оптимизации
            for rule in self.optimization_rules:
                if rule['condition']():
                    await self._apply_optimization_rule(rule)
                    if rule['action'] == 'switch_to_selenium' and method == 'plaid':
                        return False
            
            return True
            
        except Exception as e:
            logger.error(f"Ошибка проверки необходимости запроса: {e}")
            return True  # В случае ошибки делаем запрос
    
    async def _check_rate_limits(self, method: str) -> bool:
        """Проверка лимитов запросов"""
        if method not in self.rate_limits:
            return True
        
        limit_info = self.rate_limits[method]
        
        # Проверяем, нужно ли сбросить счетчик
        if limit_info['reset_date'] and datetime.now() >= limit_info['reset_date']:
            limit_info['used'] = 0
            limit_info['reset_date'] = None
        
        return limit_info['used'] < limit_info['limit']
    
    async def _is_cached_data_valid(self, cache_key: str) -> bool:
        """Проверка валидности кэшированных данных"""
        if cache_key not in self.cache:
            return False
        
        cached_data, timestamp, ttl = self.cache[cache_key]
        return datetime.now() - timestamp < timedelta(seconds=ttl)
    
    async def _is_priority_justified(self, priority: RequestPriority) -> bool:
        """Проверка оправданности приоритета"""
        # Критически важные запросы всегда оправданы
        if priority == RequestPriority.CRITICAL:
            return True
        
        # Для других приоритетов проверяем частоту запросов
        recent_requests = [
            req for req in self.request_history
            if datetime.now() - req.timestamp < timedelta(minutes=5)
        ]
        
        if len(recent_requests) > 10:
            return priority in [RequestPriority.CRITICAL, RequestPriority.HIGH]
        
        return True
    
    def _generate_cache_key(self, bank_name: str, method: str, priority: RequestPriority) -> str:
        """Генерация ключа кэша"""
        key_data = f"{bank_name}_{method}_{priority.name}_{datetime.now().strftime('%Y-%m-%d')}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    async def cache_data(self, cache_key: str, data: Any, ttl: int = 300):
        """Сохранение данных в кэш"""
        self.cache[cache_key] = (data, datetime.now(), ttl)
        logger.debug(f"Данные сохранены в кэш: {cache_key}")
    
    async def get_cached_data(self, cache_key: str) -> Optional[Any]:
        """Получение данных из кэша"""
        if await self._is_cached_data_valid(cache_key):
            data, _, _ = self.cache[cache_key]
            logger.debug(f"Данные получены из кэша: {cache_key}")
            return data
        return None
    
    async def record_request(self, request_info: RequestInfo):
        """Запись информации о запросе"""
        self.request_history.append(request_info)
        
        # Обновляем статистику лимитов
        if request_info.method in self.rate_limits:
            self.rate_limits[request_info.method]['used'] += 1
            
            # Устанавливаем дату сброса для Plaid
            if request_info.method == 'plaid' and not self.rate_limits['plaid']['reset_date']:
                next_month = datetime.now().replace(day=1) + timedelta(days=32)
                self.rate_limits['plaid']['reset_date'] = next_month.replace(day=1)
        
        # Очищаем старую историю
        cutoff_date = datetime.now() - timedelta(days=30)
        self.request_history = [
            req for req in self.request_history
            if req.timestamp > cutoff_date
        ]
    
    def _get_cache_hit_rate(self) -> float:
        """Получение процента попаданий в кэш"""
        if not self.request_history:
            return 0.0
        
        recent_requests = [
            req for req in self.request_history
            if datetime.now() - req.timestamp < timedelta(hours=1)
        ]
        
        if not recent_requests:
            return 0.0
        
        # Простая эвристика - если запросов мало, значит много попаданий в кэш
        return min(1.0, 1.0 - (len(recent_requests) / 100))
    
    def _get_error_rate(self) -> float:
        """Получение процента ошибок"""
        if not self.request_history:
            return 0.0
        
        recent_requests = [
            req for req in self.request_history
            if datetime.now() - req.timestamp < timedelta(hours=1)
        ]
        
        if not recent_requests:
            return 0.0
        
        failed_requests = [req for req in recent_requests if not req.success]
        return len(failed_requests) / len(recent_requests)
    
    async def _apply_optimization_rule(self, rule: Dict[str, Any]):
        """Применение правила оптимизации"""
        logger.info(f"Применяем правило: {rule['message']}")
        
        if rule['action'] == 'increase_cache_ttl':
            # Увеличиваем время кэширования
            for key in self.cache:
                data, timestamp, ttl = self.cache[key]
                self.cache[key] = (data, timestamp, ttl * 2)
        
        elif rule['action'] == 'reduce_request_frequency':
            # Увеличиваем TTL для всех кэшированных данных
            for key in self.cache:
                data, timestamp, ttl = self.cache[key]
                self.cache[key] = (data, timestamp, ttl * 1.5)
    
    async def get_optimization_report(self) -> Dict[str, Any]:
        """Получение отчета по оптимизации"""
        return {
            'cache_hit_rate': self._get_cache_hit_rate(),
            'error_rate': self._get_error_rate(),
            'rate_limits_status': self.rate_limits,
            'recent_requests_count': len([
                req for req in self.request_history
                if datetime.now() - req.timestamp < timedelta(hours=1)
            ]),
            'optimization_recommendations': await self._get_recommendations()
        }
    
    async def _get_recommendations(self) -> List[str]:
        """Получение рекомендаций по оптимизации"""
        recommendations = []
        
        cache_hit_rate = self._get_cache_hit_rate()
        if cache_hit_rate < 0.3:
            recommendations.append("Увеличьте время кэширования для часто запрашиваемых данных")
        
        error_rate = self._get_error_rate()
        if error_rate > 0.2:
            recommendations.append("Проверьте стабильность банковских подключений")
        
        plaid_usage = self.rate_limits['plaid']['used'] / self.rate_limits['plaid']['limit']
        if plaid_usage > 0.8:
            recommendations.append("Рассмотрите переход на Selenium для некоторых банков")
        
        if len(self.request_history) > 1000:
            recommendations.append("Очистите старую историю запросов для экономии памяти")
        
        return recommendations
    
    async def get_cost_analysis(self) -> Dict[str, Any]:
        """Анализ стоимости запросов"""
        plaid_requests = len([
            req for req in self.request_history
            if req.method == 'plaid' and datetime.now() - req.timestamp < timedelta(days=30)
        ])
        
        free_requests = 100
        paid_requests = max(0, plaid_requests - free_requests)
        monthly_cost = paid_requests * 0.50
        
        return {
            'plaid_requests_this_month': plaid_requests,
            'free_requests_used': min(plaid_requests, free_requests),
            'paid_requests': paid_requests,
            'estimated_monthly_cost': monthly_cost,
            'cost_per_request': 0.50 if paid_requests > 0 else 0,
            'savings_from_optimization': self._calculate_savings()
        }
    
    def _calculate_savings(self) -> float:
        """Расчет экономии от оптимизации"""
        # Простая эвристика - если кэш работает хорошо, экономим запросы
        cache_hit_rate = self._get_cache_hit_rate()
        potential_savings = cache_hit_rate * 0.50 * 50  # Предполагаем 50 запросов в месяц
        return potential_savings
