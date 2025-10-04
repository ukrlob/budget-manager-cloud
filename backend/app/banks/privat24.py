"""
Интеграция с PrivatBank (Приват24) API
Украинский банк с API для бизнеса
"""

import aiohttp
import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, date
from .base import BankConnector, BankError, ConnectionError, AuthenticationError, DataError

logger = logging.getLogger(__name__)


class Privat24Connector(BankConnector):
    """
    Коннектор для PrivatBank (Приват24) API
    """
    
    def __init__(self, credentials: Dict[str, Any]):
        super().__init__("Privat24", credentials)
        self.api_base_url = "https://api.privatbank.ua"
        self.merchant_id = credentials.get('merchant_id')
        self.merchant_password = credentials.get('merchant_password')
        self.card_number = credentials.get('card_number')
        self.session = None
        
    async def connect(self) -> bool:
        """
        Подключение к Privat24 API
        """
        try:
            logger.info(f"Подключение к {self.bank_name} API...")
            
            if not all([self.merchant_id, self.merchant_password, self.card_number]):
                raise AuthenticationError("Privat24 merchant_id, merchant_password и card_number не найдены")
            
            # Создаем HTTP сессию
            self.session = aiohttp.ClientSession(
                headers={
                    'Content-Type': 'application/json',
                    'Accept': 'application/json'
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
            # Privat24 API требует специальную аутентификацию
            # Для тестирования используем базовый endpoint
            async with self.session.get(f"{self.api_base_url}/p24api/rest_fiz") as response:
                if response.status == 200:
                    logger.info("Privat24 API подключен")
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
                raise ConnectionError("Не подключен к Privat24")
            
            # Privat24 API для получения информации о картах
            url = f"{self.api_base_url}/p24api/rest_fiz"
            data = {
                'merchant_id': self.merchant_id,
                'merchant_password': self.merchant_password,
                'card_number': self.card_number
            }
            
            async with self.session.post(url, json=data) as response:
                if response.status == 200:
                    response_data = await response.json()
                    accounts = []
                    
                    # Обрабатываем ответ Privat24
                    if 'accounts' in response_data:
                        for account in response_data['accounts']:
                            accounts.append({
                                'id': account.get('id', ''),
                                'name': f"Privat24 {account.get('type', 'Card')}",
                                'type': account.get('type', 'card'),
                                'balance': float(account.get('balance', 0)),
                                'currency': account.get('currency', 'UAH'),
                                'bank_name': 'PrivatBank',
                                'card_number': account.get('card_number', ''),
                                'expiry': account.get('expiry', '')
                            })
                    
                    logger.info(f"Получено {len(accounts)} счетов из Privat24")
                    return accounts
                else:
                    raise DataError(f"Ошибка получения счетов: {response.status}")
                    
        except Exception as e:
            logger.error(f"Ошибка получения счетов Privat24: {e}")
            raise DataError(f"Не удалось получить счета: {e}")
    
    async def get_transactions(self, account_id: str, from_date: Optional[datetime] = None, to_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """
        Получение транзакций по счету
        """
        try:
            if not self.is_connected:
                raise ConnectionError("Не подключен к Privat24")
            
            # Формируем даты для запроса
            if not from_date:
                from_date = datetime.now().replace(day=1)
            if not to_date:
                to_date = datetime.now()
            
            url = f"{self.api_base_url}/p24api/rest_fiz"
            data = {
                'merchant_id': self.merchant_id,
                'merchant_password': self.merchant_password,
                'card_number': self.card_number,
                'from_date': from_date.strftime('%d.%m.%Y'),
                'to_date': to_date.strftime('%d.%m.%Y')
            }
            
            async with self.session.post(url, json=data) as response:
                if response.status == 200:
                    response_data = await response.json()
                    transactions = []
                    
                    # Обрабатываем транзакции Privat24
                    if 'transactions' in response_data:
                        for tx in response_data['transactions']:
                            transactions.append({
                                'id': tx.get('id', ''),
                                'amount': float(tx.get('amount', 0)),
                                'description': tx.get('description', ''),
                                'date': datetime.strptime(tx.get('date', ''), '%d.%m.%Y').date(),
                                'category': self._categorize_transaction(tx),
                                'account_id': account_id,
                                'currency': tx.get('currency', 'UAH'),
                                'merchant': tx.get('merchant', ''),
                                'terminal': tx.get('terminal', '')
                            })
                    
                    logger.info(f"Получено {len(transactions)} транзакций из Privat24")
                    return transactions
                else:
                    raise DataError(f"Ошибка получения транзакций: {response.status}")
                    
        except Exception as e:
            logger.error(f"Ошибка получения транзакций Privat24: {e}")
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
            logger.error(f"Ошибка получения баланса Privat24: {e}")
            raise DataError(f"Не удалось получить баланс: {e}")
    
    def _categorize_transaction(self, transaction: Dict) -> str:
        """
        Категоризация транзакции на основе данных Privat24
        """
        description = transaction.get('description', '').lower()
        merchant = transaction.get('merchant', '').lower()
        
        # Простая категоризация на основе ключевых слов
        if any(word in description for word in ['продукты', 'супермаркет', 'магазин', 'еда']):
            return 'Продукты'
        elif any(word in description for word in ['ресторан', 'кафе', 'бар', 'еда']):
            return 'Развлечения'
        elif any(word in description for word in ['транспорт', 'такси', 'автобус', 'метро']):
            return 'Транспорт'
        elif any(word in description for word in ['аптека', 'медицина', 'врач', 'здоровье']):
            return 'Здоровье'
        elif any(word in description for word in ['покупки', 'одежда', 'обувь', 'товары']):
            return 'Покупки'
        elif any(word in description for word in ['коммунальные', 'электричество', 'газ', 'вода']):
            return 'Коммунальные услуги'
        elif any(word in description for word in ['зарплата', 'доход', 'пенсия', 'стипендия']):
            return 'Доходы'
        else:
            return 'Другое'
    
    async def get_exchange_rates(self) -> Dict[str, Any]:
        """
        Получение курсов валют (специфично для Privat24)
        """
        try:
            if not self.is_connected:
                raise ConnectionError("Не подключен к Privat24")
            
            async with self.session.get(f"{self.api_base_url}/p24api/pubinfo?json&exchange&coursid=5") as response:
                if response.status == 200:
                    rates_data = await response.json()
                    return rates_data
                else:
                    raise DataError(f"Ошибка получения курсов валют: {response.status}")
                    
        except Exception as e:
            logger.error(f"Ошибка получения курсов валют Privat24: {e}")
            raise DataError(f"Не удалось получить курсы валют: {e}")
    
    async def disconnect(self):
        """
        Отключение от API
        """
        if self.session:
            await self.session.close()
            self.session = None
        self.is_connected = False
        logger.info(f"Отключен от {self.bank_name}")
