"""
Интеграция с Monobank API
Один из лучших API среди украинских банков
"""

import aiohttp
import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, date
from .base import BankConnector, BankError, ConnectionError, AuthenticationError, DataError

logger = logging.getLogger(__name__)


class MonobankConnector(BankConnector):
    """
    Коннектор для Monobank API
    """
    
    def __init__(self, credentials: Dict[str, Any]):
        super().__init__("Monobank", credentials)
        self.api_base_url = "https://api.monobank.ua"
        self.token = credentials.get('token')
        self.session = None
        
    async def connect(self) -> bool:
        """
        Подключение к Monobank API
        """
        try:
            logger.info(f"Подключение к {self.bank_name} API...")
            
            if not self.token:
                raise AuthenticationError("Monobank token не найден")
            
            # Создаем HTTP сессию
            self.session = aiohttp.ClientSession(
                headers={
                    'X-Token': self.token,
                    'Content-Type': 'application/json'
                }
            )
            
            # Проверяем подключение
            await self._test_connection()
            
            self.is_connected = True
            logger.info(f"Успешно подключен к {self.bank_name} API")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка подключения к {self.bank_name}: {e}")
            if self.session:
                await self.session.close()
                self.session = None
            raise ConnectionError(f"Не удалось подключиться к {self.bank_name}: {e}")
    
    async def _test_connection(self):
        """
        Тестирование подключения к API
        """
        try:
            async with self.session.get(f"{self.api_base_url}/personal/client-info") as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"Monobank API подключен. Клиент: {data.get('name', 'Unknown')}")
                elif response.status == 401:
                    raise AuthenticationError("Неверный токен Monobank")
                else:
                    raise ConnectionError(f"Ошибка API: {response.status}")
        except aiohttp.ClientError as e:
            raise ConnectionError(f"Ошибка сети: {e}")
    
    async def get_accounts(self) -> List[Dict[str, Any]]:
        """
        Получение списка счетов
        """
        try:
            if not self.is_connected:
                raise ConnectionError("Не подключен к Monobank")
            
            async with self.session.get(f"{self.api_base_url}/personal/client-info") as response:
                if response.status == 200:
                    data = await response.json()
                    accounts = []
                    
                    for account in data.get('accounts', []):
                        accounts.append({
                            'id': account['id'],
                            'name': self._get_account_name(account),
                            'type': self._get_account_type(account),
                            'balance': account['balance'] / 100,  # Monobank хранит в копейках
                            'currency': self._get_currency_code(account['currencyCode']),
                            'bank_name': 'Monobank',
                            'masked_pan': account.get('maskedPan', [])
                        })
                    
                    logger.info(f"Получено {len(accounts)} счетов из Monobank")
                    return accounts
                else:
                    raise DataError(f"Ошибка получения счетов: {response.status}")
                    
        except Exception as e:
            logger.error(f"Ошибка получения счетов Monobank: {e}")
            raise DataError(f"Не удалось получить счета: {e}")
    
    async def get_transactions(self, account_id: str, from_date: Optional[datetime] = None, to_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """
        Получение транзакций по счету
        """
        try:
            if not self.is_connected:
                raise ConnectionError("Не подключен к Monobank")
            
            # Monobank API требует timestamp в секундах
            if not from_date:
                from_date = datetime.now().replace(day=1)  # Начало месяца
            
            from_timestamp = int(from_date.timestamp())
            to_timestamp = int((to_date or datetime.now()).timestamp())
            
            url = f"{self.api_base_url}/personal/statement/{account_id}/{from_timestamp}/{to_timestamp}"
            
            async with self.session.get(url) as response:
                if response.status == 200:
                    transactions_data = await response.json()
                    transactions = []
                    
                    for tx in transactions_data:
                        transactions.append({
                            'id': tx['id'],
                            'amount': tx['amount'] / 100,  # Monobank хранит в копейках
                            'description': tx.get('description', ''),
                            'date': datetime.fromtimestamp(tx['time']).date(),
                            'category': self._categorize_transaction(tx),
                            'account_id': account_id,
                            'currency': self._get_currency_code(tx.get('currencyCode', 980))
                        })
                    
                    logger.info(f"Получено {len(transactions)} транзакций из Monobank")
                    return transactions
                else:
                    raise DataError(f"Ошибка получения транзакций: {response.status}")
                    
        except Exception as e:
            logger.error(f"Ошибка получения транзакций Monobank: {e}")
            raise DataError(f"Не удалось получить транзакции: {e}")
    
    async def get_balance(self, account_id: str) -> Dict[str, Any]:
        """
        Получение баланса счета
        """
        try:
            accounts = await self.get_accounts()
            
            for account in accounts:
                if account['id'] == account_id:
                    return {
                        'account_id': account_id,
                        'balance': account['balance'],
                        'currency': account['currency'],
                        'last_updated': datetime.now().isoformat()
                    }
            
            raise DataError(f"Счет {account_id} не найден")
            
        except Exception as e:
            logger.error(f"Ошибка получения баланса Monobank: {e}")
            raise DataError(f"Не удалось получить баланс: {e}")
    
    def _get_account_name(self, account: Dict) -> str:
        """
        Получение названия счета
        """
        account_type = self._get_account_type(account)
        currency = self._get_currency_code(account['currencyCode'])
        return f"Monobank {account_type} ({currency})"
    
    def _get_account_type(self, account: Dict) -> str:
        """
        Получение типа счета
        """
        account_type_map = {
            'black': 'Black',
            'white': 'White',
            'platinum': 'Platinum',
            'iron': 'Iron',
            'fop': 'ФОП',
            'yellow': 'Yellow'
        }
        
        return account_type_map.get(account.get('type', ''), 'Unknown')
    
    def _get_currency_code(self, currency_code: int) -> str:
        """
        Получение кода валюты
        """
        currency_map = {
            980: 'UAH',
            840: 'USD',
            978: 'EUR',
            826: 'GBP'
        }
        
        return currency_map.get(currency_code, 'UAH')
    
    def _categorize_transaction(self, transaction: Dict) -> str:
        """
        Категоризация транзакции на основе данных Monobank
        """
        mcc = transaction.get('mcc', 0)
        
        # MCC коды для категоризации
        mcc_categories = {
            # Продукты
            5411: 'Продукты',  # Супермаркеты
            5422: 'Продукты',  # Мясо
            5441: 'Продукты',  # Кондитерские
            
            # Транспорт
            4111: 'Транспорт',  # Транспорт
            4121: 'Транспорт',  # Такси
            4131: 'Транспорт',  # Автобусы
            
            # Развлечения
            5812: 'Развлечения',  # Рестораны
            5813: 'Развлечения',  # Бары
            5814: 'Развлечения',  # Фаст-фуд
            
            # Здоровье
            5912: 'Здоровье',  # Аптеки
            8011: 'Здоровье',  # Врачи
            
            # Покупки
            5310: 'Покупки',  # Универмаги
            5311: 'Покупки',  # Универмаги
            5411: 'Покупки',  # Супермаркеты
            
            # Коммунальные услуги
            4900: 'Коммунальные услуги',  # Коммунальные
            4814: 'Коммунальные услуги',  # Телефон
            
            # Доходы
            6011: 'Доходы',  # Банки
            6012: 'Доходы',  # Финансовые услуги
        }
        
        return mcc_categories.get(mcc, 'Другое')
    
    async def disconnect(self):
        """
        Отключение от API
        """
        if self.session:
            await self.session.close()
            self.session = None
        self.is_connected = False
        logger.info(f"Отключен от {self.bank_name}")
    
    async def get_webhook_url(self) -> str:
        """
        Получение URL для webhook (если настроен)
        """
        # Monobank поддерживает webhooks для уведомлений о транзакциях
        return f"{self.api_base_url}/personal/webhook"
    
    async def set_webhook(self, webhook_url: str) -> bool:
        """
        Настройка webhook для получения уведомлений
        """
        try:
            if not self.is_connected:
                raise ConnectionError("Не подключен к Monobank")
            
            data = {'webHookUrl': webhook_url}
            
            async with self.session.post(f"{self.api_base_url}/personal/webhook", json=data) as response:
                if response.status == 200:
                    logger.info(f"Webhook настроен: {webhook_url}")
                    return True
                else:
                    logger.error(f"Ошибка настройки webhook: {response.status}")
                    return False
                    
        except Exception as e:
            logger.error(f"Ошибка настройки webhook Monobank: {e}")
            return False
