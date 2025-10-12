"""
Интеграция с Plaid API
Умная система с кэшированием и оптимизацией запросов
"""

import plaid
from plaid.api import plaid_api
from plaid.model.accounts_get_request import AccountsGetRequest
from plaid.model.transactions_get_request import TransactionsGetRequest
from plaid.model.transactions_get_request_options import TransactionsGetRequestOptions
from plaid import Configuration, ApiClient
from typing import List, Dict, Any, Optional
import asyncio
import logging
from datetime import datetime, timedelta
import json
import os
from .base import BankConnector, BankError, ConnectionError, AuthenticationError, DataError
from ..services.cache_service import PlaidCacheService

logger = logging.getLogger(__name__)

# Глобальный счетчик запросов
_global_request_count = 0
_global_monthly_cache = {}


class PlaidBankConnector(BankConnector):
    """
    Умный коннектор Plaid с оптимизацией запросов
    """
    
    def __init__(self, credentials: Dict[str, Any]):
        super().__init__("Plaid", credentials)
        
        # Настройка Plaid клиента
        self.client_id = credentials.get('client_id')
        self.secret = credentials.get('secret')
        self.environment = credentials.get('environment', 'sandbox')
        
        # Инициализация Plaid API
        configuration = Configuration(
            host=plaid.Environment.Production if self.environment == 'production' else plaid.Environment.Sandbox,
            api_key={
                'clientId': self.client_id,
                'secret': self.secret
            }
        )
        
        api_client = ApiClient(configuration)
        self.client = plaid_api.PlaidApi(api_client)
        
        # Персистентный кэш
        self.cache_service = PlaidCacheService()
        
        # Старый кэш для совместимости (будет удален)
        self.cache = {}
        self.cache_ttl = 300  # 5 минут
        self.request_count = 0
        self.monthly_limit = 100  # Бесплатный лимит
        
    async def connect(self) -> bool:
        """
        Подключение к Plaid (не требует отдельного подключения)
        """
        try:
            logger.info("Plaid подключение инициализировано")
            self.is_connected = True
            return True
        except Exception as e:
            logger.error(f"Ошибка инициализации Plaid: {e}")
            raise ConnectionError(f"Не удалось инициализировать Plaid: {e}")
    
    async def _check_rate_limit(self) -> bool:
        """
        Проверка лимитов запросов
        """
        current_month = datetime.now().strftime('%Y-%m')
        month_key = f"requests_{current_month}"
        
        if month_key not in self.cache:
            self.cache[month_key] = 0
        
        if self.cache[month_key] >= self.monthly_limit:
            logger.warning(f"Достигнут месячный лимит запросов: {self.monthly_limit}")
            return False
        
        return True
    
    async def _increment_request_count(self):
        """
        Увеличение счетчика запросов
        """
        global _global_request_count, _global_monthly_cache
        
        current_month = datetime.now().strftime('%Y-%m')
        month_key = f"requests_{current_month}"
        
        if month_key not in _global_monthly_cache:
            _global_monthly_cache[month_key] = 0
        
        _global_monthly_cache[month_key] += 1
        _global_request_count += 1
        self.request_count = _global_request_count
        
        logger.info(f"Запросов в этом месяце: {_global_monthly_cache[month_key]}/{self.monthly_limit}")
    
    async def _get_cached_data(self, key: str) -> Optional[Any]:
        """
        Получение данных из кэша
        """
        if key in self.cache:
            data, timestamp = self.cache[key]
            if datetime.now() - timestamp < timedelta(seconds=self.cache_ttl):
                logger.debug(f"Данные получены из кэша: {key}")
                return data
            else:
                del self.cache[key]
        return None
    
    async def _cache_data(self, key: str, data: Any):
        """
        Сохранение данных в кэш
        """
        self.cache[key] = (data, datetime.now())
        logger.debug(f"Данные сохранены в кэш: {key}")
    
    async def get_accounts(self) -> List[Dict[str, Any]]:
        """
        Получение счетов с персистентным кэшированием
        """
        try:
            bank_code = self.credentials.get('bank_code', 'UNKNOWN')
            
            # Проверяем кэш
            cached_data = await self.cache_service.get_cached_data(
                data_type='accounts',
                bank_code=bank_code,
                item_id=self.credentials.get('item_id')
            )
            
            if cached_data and cached_data.get('data'):
                logger.info(f"Счета получены из кэша для банка {bank_code}")
                return cached_data['data']
            
            # Проверяем лимиты
            if not await self._check_rate_limit():
                logger.warning("Используем кэшированные данные из-за лимитов")
                fallback_data = await self.cache_service.get_cached_data(
                    data_type='accounts_fallback',
                    bank_code=bank_code,
                    item_id=self.credentials.get('item_id')
                )
                return fallback_data.get('data', []) if fallback_data else []
            
            # Получаем access_token из credentials
            access_token = self.credentials.get('access_token')
            if not access_token:
                raise AuthenticationError("Access token не найден")
            
            # Запрос к Plaid API
            request = AccountsGetRequest(access_token=access_token)
            response = self.client.accounts_get(request)
            
            await self._increment_request_count()
            
            # Обработка ответа
            accounts = []
            for account in response['accounts']:
                # Правильное отображение балансов для разных типов счетов
                account_type = str(account['type'])
                subtype = str(account['subtype'])
                balances = account['balances']
                
                # Для кредитных карт показываем лимит и остаток по лимиту
                if account_type == 'credit' or (isinstance(subtype, str) and 'credit' in subtype.lower()):
                    # Для кредитных карт: available = доступный лимит, current = потраченная сумма
                    credit_limit = balances.get('limit')  # Общий лимит от Plaid
                    current_balance = balances.get('current', 0)  # Потраченная сумма
                    available_credit = balances.get('available', 0)  # Доступный лимит
                    
                    # Если limit не предоставлен Plaid, вычисляем как available + current
                    if credit_limit is None:
                        credit_limit = available_credit + current_balance
                    
                    accounts.append({
                        'id': account['account_id'],
                        'name': account['name'],
                        'type': account['type'],
                        'subtype': account['subtype'],
                        'current_balance': available_credit,  # Доступный лимит
                        'credit_limit': credit_limit,  # Общий лимит
                        'used_credit': current_balance,  # Использованный лимит
                        'currency': account['balances']['iso_currency_code'],
                        'bank_name': self.credentials.get('bank_name', account.get('institution_name', 'Unknown')),
                        'balance_type': 'credit_available'  # Тип баланса для фронтенда
                    })
                else:
                    # Для депозитных счетов показываем текущий баланс
                    accounts.append({
                        'id': account['account_id'],
                        'name': account['name'],
                        'type': account['type'],
                        'subtype': account['subtype'],
                        'current_balance': balances.get('current', 0),
                        'available_balance': balances.get('available', balances.get('current', 0)),
                        'currency': account['balances']['iso_currency_code'],
                        'bank_name': self.credentials.get('bank_name', account.get('institution_name', 'Unknown')),
                        'balance_type': 'deposit'  # Тип баланса для фронтенда
                    })
            
            # Сохраняем в кэш
            await self.cache_service.cache_data(
                data_type='accounts',
                data=accounts,
                bank_code=bank_code,
                item_id=self.credentials.get('item_id')
            )
            
            # Сохраняем fallback данные
            await self.cache_service.cache_data(
                data_type='accounts_fallback',
                data=accounts,
                bank_code=bank_code,
                item_id=self.credentials.get('item_id')
            )
            
            logger.info(f"Получено {len(accounts)} счетов через Plaid")
            return accounts
            
        except Exception as e:
            logger.error(f"Ошибка получения счетов Plaid: {e}")
            # Возвращаем кэшированные данные в случае ошибки
            fallback_data = await self.cache_service.get_cached_data(
                data_type='accounts_fallback',
                bank_code=self.credentials.get('bank_code', 'UNKNOWN'),
                item_id=self.credentials.get('item_id')
            )
            return fallback_data.get('data', []) if fallback_data else []
    
    async def get_transactions(self, account_id: str, start_date: Optional[datetime] = None, end_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """
        Получение транзакций с инкрементальным кэшированием
        """
        try:
            # Умное кэширование по датам
            if not start_date:
                start_date = datetime.now() - timedelta(days=30)
            if not end_date:
                end_date = datetime.now()
            
            bank_code = self.credentials.get('bank_code', 'UNKNOWN')
            
            # Проверяем файловый кэш
            cached_data = await self.cache_service.get_cached_data(
                data_type='transactions',
                bank_code=bank_code,
                account_id=account_id,
                item_id=self.credentials.get('item_id'),
                start_date=start_date.strftime('%Y-%m-%d'),
                end_date=end_date.strftime('%Y-%m-%d')
            )
            
            if cached_data and cached_data.get('data'):
                logger.info(f"Транзакции получены из кэша для счета {account_id}")
                return cached_data['data']
            
            # Проверяем лимиты
            if not await self._check_rate_limit():
                logger.warning("Используем кэшированные данные из-за лимитов")
                # Пытаемся получить любые кэшированные транзакции
                fallback_data = await self.cache_service.get_cached_data(
                    data_type='transactions_fallback',
                    bank_code=bank_code,
                    account_id=account_id,
                    item_id=self.credentials.get('item_id')
                )
                return fallback_data.get('data', []) if fallback_data else []
            
            # Получаем access_token
            access_token = self.credentials.get('access_token')
            if not access_token:
                raise AuthenticationError("Access token не найден")
            
            # Запрос к Plaid API
            options = TransactionsGetRequestOptions(account_ids=[account_id])
            request = TransactionsGetRequest(
                access_token=access_token,
                start_date=start_date,
                end_date=end_date,
                options=options
            )
            response = self.client.transactions_get(request)
            
            await self._increment_request_count()
            
            # Обработка ответа
            transactions = []
            for transaction in response['transactions']:
                transactions.append({
                    'id': transaction['transaction_id'],
                    'amount': transaction['amount'],
                    'name': transaction['name'],
                    'date': transaction['date'],
                    'category': transaction.get('category', ['Uncategorized']),
                    'account_id': account_id,
                    'currency': transaction.get('iso_currency_code', 'USD')
                })
            
            # Сохраняем в файловый кэш
            await self.cache_service.cache_data(
                data_type='transactions',
                data=transactions,
                bank_code=bank_code,
                account_id=account_id,
                item_id=self.credentials.get('item_id'),
                start_date=start_date.strftime('%Y-%m-%d'),
                end_date=end_date.strftime('%Y-%m-%d')
            )
            
            # Сохраняем fallback кэш
            await self.cache_service.cache_data(
                data_type='transactions_fallback',
                data=transactions,
                bank_code=bank_code,
                account_id=account_id,
                item_id=self.credentials.get('item_id')
            )
            
            logger.info(f"Получено {len(transactions)} транзакций через Plaid")
            return transactions
            
        except Exception as e:
            logger.error(f"Ошибка получения транзакций Plaid: {e}")
            # Пытаемся получить fallback данные из файлового кэша
            try:
                fallback_data = await self.cache_service.get_cached_data(
                    data_type='transactions_fallback',
                    bank_code=bank_code,
                    account_id=account_id,
                    item_id=self.credentials.get('item_id')
                )
                return fallback_data.get('data', []) if fallback_data else []
            except Exception as fallback_error:
                logger.error(f"Ошибка получения fallback данных: {fallback_error}")
                return []
    
    async def get_incremental_transactions(self, account_id: str, last_update: datetime) -> List[Dict[str, Any]]:
        """
        Получение только новых транзакций с последнего обновления
        """
        try:
            bank_code = self.credentials.get('bank_code', 'UNKNOWN')
            
            # Получаем инкрементальные данные из кэша
            incremental_data = await self.cache_service.get_incremental_data(
                data_type='transactions',
                bank_code=bank_code,
                last_update=last_update
            )
            
            if incremental_data and incremental_data.get('data'):
                logger.info(f"Получено {incremental_data['count']} новых транзакций из кэша")
                return incremental_data['data']
            
            # Если нет инкрементальных данных, получаем все транзакции
            logger.info("Инкрементальных данных нет, загружаем все транзакции")
            return await self.get_transactions(account_id)
            
        except Exception as e:
            logger.error(f"Ошибка инкрементальной загрузки транзакций: {e}")
            return []
    
    async def get_balance(self, account_id: str) -> Dict[str, Any]:
        """
        Получение баланса с кэшированием
        """
        try:
            cache_key = f"balance_{account_id}"
            
            # Проверяем кэш
            cached_balance = await self._get_cached_data(cache_key)
            if cached_balance:
                return cached_balance
            
            # Проверяем лимиты
            if not await self._check_rate_limit():
                logger.warning("Используем кэшированные данные из-за лимитов")
                return await self._get_cached_data("balance_fallback") or {}
            
            # Получаем access_token
            access_token = self.credentials.get('access_token')
            if not access_token:
                raise AuthenticationError("Access token не найден")
            
            # Запрос к Plaid API
            request = AccountsGetRequest(access_token=access_token)
            response = self.client.accounts_get(request)
            
            await self._increment_request_count()
            
            # Находим нужный счет
            for account in response['accounts']:
                if account['account_id'] == account_id:
                    balance_data = {
                        'account_id': account_id,
                        'current_balance': account['balances']['current'],
                        'available_balance': account['balances']['available'],
                        'currency': account['balances']['iso_currency_code'],
                        'last_updated': datetime.now().isoformat()
                    }
                    
                    # Сохраняем в кэш
                    await self._cache_data(cache_key, balance_data)
                    await self._cache_data("balance_fallback", balance_data)
                    
                    return balance_data
            
            return {}
            
        except Exception as e:
            logger.error(f"Ошибка получения баланса Plaid: {e}")
            return await self._get_cached_data("balance_fallback") or {}
    
    async def get_institution_info(self, institution_id: str) -> Dict[str, Any]:
        """
        Получение информации об учреждении
        """
        try:
            cache_key = f"institution_{institution_id}"
            
            # Проверяем кэш
            cached_info = await self._get_cached_data(cache_key)
            if cached_info:
                return cached_info
            
            # Проверяем лимиты
            if not await self._check_rate_limit():
                logger.warning("Используем кэшированные данные из-за лимитов")
                return await self._get_cached_data("institution_fallback") or {}
            
            # Запрос к Plaid API
            request = InstitutionsGetByIdRequest(
                institution_id=institution_id,
                country_codes=[CountryCode('US')]
            )
            response = self.client.institutions_get_by_id(request)
            
            await self._increment_request_count()
            
            # Обработка ответа
            institution_info = {
                'institution_id': response['institution']['institution_id'],
                'name': response['institution']['name'],
                'products': response['institution']['products'],
                'country_codes': response['institution']['country_codes'],
                'url': response['institution'].get('url'),
                'logo': response['institution'].get('logo')
            }
            
            # Сохраняем в кэш
            await self._cache_data(cache_key, institution_info)
            await self._cache_data("institution_fallback", institution_info)
            
            return institution_info
            
        except Exception as e:
            logger.error(f"Ошибка получения информации об учреждении: {e}")
            return await self._get_cached_data("institution_fallback") or {}
    
    async def get_rate_limit_status(self) -> Dict[str, Any]:
        """
        Получение статуса лимитов запросов
        """
        global _global_request_count, _global_monthly_cache
        
        current_month = datetime.now().strftime('%Y-%m')
        month_key = f"requests_{current_month}"
        
        requests_used = _global_monthly_cache.get(month_key, 0)
        requests_remaining = max(0, self.monthly_limit - requests_used)
        
        # Если счетчик показывает 0, но мы знаем что делали запросы, показываем минимум 1
        if requests_used == 0 and _global_request_count > 0:
            requests_used = min(_global_request_count, self.monthly_limit)
            requests_remaining = max(0, self.monthly_limit - requests_used)
        
        return {
            'monthly_limit': self.monthly_limit,
            'requests_used': requests_used,
            'requests_remaining': requests_remaining,
            'usage_percentage': (requests_used / self.monthly_limit) * 100,
            'reset_date': (datetime.now().replace(day=1) + timedelta(days=32)).replace(day=1).strftime('%Y-%m-%d')
        }
    
    async def optimize_requests(self) -> Dict[str, Any]:
        """
        Оптимизация запросов для экономии лимитов
        """
        optimization_tips = []
        
        # Анализ использования кэша
        cache_hit_rate = len([k for k, v in self.cache.items() if isinstance(v, tuple) and len(v) == 2]) / max(1, self.request_count)
        
        if cache_hit_rate < 0.5:
            optimization_tips.append("Увеличьте время кэширования для часто запрашиваемых данных")
        
        # Рекомендации по частоте запросов
        if self.request_count > self.monthly_limit * 0.8:
            optimization_tips.append("Сократите частоту запросов - приближаетесь к лимиту")
        
        # Рекомендации по группировке запросов
        optimization_tips.append("Группируйте запросы по счетам для экономии лимитов")
        optimization_tips.append("Используйте webhooks для обновлений в реальном времени")
        
        return {
            'cache_hit_rate': cache_hit_rate,
            'optimization_tips': optimization_tips,
            'recommended_cache_ttl': 600 if cache_hit_rate < 0.3 else 300
        }
    
    async def exchange_public_token(self, public_token: str) -> Optional[str]:
        """
        Обмен public_token на access_token через Plaid API
        """
        try:
            logger.info(f"Обмен public_token на access_token")
            
            # Импортируем необходимые модели Plaid
            from plaid.model.item_public_token_exchange_request import ItemPublicTokenExchangeRequest
            
            # Создаем запрос на обмен токена
            request = ItemPublicTokenExchangeRequest(
                public_token=public_token
            )
            
            # Выполняем обмен токена
            response = self.client.item_public_token_exchange(request)
            
            if response and response.access_token:
                logger.info("Токен успешно обменян")
                return response.access_token
            else:
                logger.error("Не удалось получить access_token")
                return None
                
        except Exception as e:
            logger.error(f"Ошибка обмена токена: {e}")
            return None
