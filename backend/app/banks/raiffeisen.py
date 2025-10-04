"""
Интеграция с Raiffeisen Bank API
Украинский банк с современным API
"""

import aiohttp
import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, date
from .base import BankConnector, BankError, ConnectionError, AuthenticationError, DataError

logger = logging.getLogger(__name__)


class RaiffeisenConnector(BankConnector):
    """
    Коннектор для Raiffeisen Bank API
    """
    
    def __init__(self, credentials: Dict[str, Any]):
        super().__init__("Raiffeisen", credentials)
        self.api_base_url = "https://api.raiffeisen.ua"
        self.client_id = credentials.get('client_id')
        self.client_secret = credentials.get('client_secret')
        self.access_token = None
        self.session = None
        
    async def connect(self) -> bool:
        """
        Подключение к Raiffeisen Bank API
        """
        try:
            logger.info(f"Подключение к {self.bank_name} API...")
            
            if not self.client_id or not self.client_secret:
                raise AuthenticationError("Raiffeisen client_id и client_secret не найдены")
            
            # Создаем HTTP сессию
            self.session = aiohttp.ClientSession()
            
            # Получаем access token
            await self._get_access_token()
            
            self.is_connected = True
            logger.info(f"Успешно подключен к {self.bank_name} API")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка подключения к {self.bank_name}: {e}")
            if self.session:
                await self.session.close()
                self.session = None
            raise ConnectionError(f"Не удалось подключиться к {self.bank_name}: {e}")
    
    async def _get_access_token(self):
        """
        Получение access token через OAuth2
        """
        try:
            auth_data = {
                'grant_type': 'client_credentials',
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'scope': 'accounts transactions'
            }
            
            async with self.session.post(
                f"{self.api_base_url}/oauth/token",
                data=auth_data
            ) as response:
                if response.status == 200:
                    token_data = await response.json()
                    self.access_token = token_data['access_token']
                    
                    # Обновляем заголовки сессии
                    self.session.headers.update({
                        'Authorization': f'Bearer {self.access_token}',
                        'Content-Type': 'application/json',
                        'Accept': 'application/json'
                    })
                    
                    logger.info("Raiffeisen access token получен")
                else:
                    raise AuthenticationError(f"Ошибка получения токена: {response.status}")
                    
        except Exception as e:
            raise AuthenticationError(f"Не удалось получить access token: {e}")
    
    async def get_accounts(self) -> List[Dict[str, Any]]:
        """
        Получение списка счетов
        """
        try:
            if not self.is_connected:
                raise ConnectionError("Не подключен к Raiffeisen")
            
            async with self.session.get(f"{self.api_base_url}/api/v1/accounts") as response:
                if response.status == 200:
                    data = await response.json()
                    accounts = []
                    
                    for account in data.get('accounts', []):
                        accounts.append({
                            'id': account['id'],
                            'name': f"Raiffeisen {account.get('name', 'Account')}",
                            'type': account.get('type', 'current'),
                            'balance': float(account.get('balance', 0)),
                            'currency': account.get('currency', 'UAH'),
                            'bank_name': 'Raiffeisen Bank',
                            'account_number': account.get('account_number', ''),
                            'iban': account.get('iban', ''),
                            'status': account.get('status', 'active')
                        })
                    
                    logger.info(f"Получено {len(accounts)} счетов из Raiffeisen")
                    return accounts
                else:
                    raise DataError(f"Ошибка получения счетов: {response.status}")
                    
        except Exception as e:
            logger.error(f"Ошибка получения счетов Raiffeisen: {e}")
            raise DataError(f"Не удалось получить счета: {e}")
    
    async def get_transactions(self, account_id: str, from_date: Optional[datetime] = None, to_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """
        Получение транзакций по счету
        """
        try:
            if not self.is_connected:
                raise ConnectionError("Не подключен к Raiffeisen")
            
            # Формируем параметры запроса
            params = {'account_id': account_id}
            if from_date:
                params['from_date'] = from_date.isoformat()
            if to_date:
                params['to_date'] = to_date.isoformat()
            
            async with self.session.get(f"{self.api_base_url}/api/v1/transactions", params=params) as response:
                if response.status == 200:
                    data = await response.json()
                    transactions = []
                    
                    for tx in data.get('transactions', []):
                        transactions.append({
                            'id': tx['id'],
                            'amount': float(tx['amount']),
                            'description': tx.get('description', ''),
                            'date': datetime.fromisoformat(tx['date'].replace('Z', '+00:00')).date(),
                            'category': self._categorize_transaction(tx),
                            'account_id': account_id,
                            'currency': tx.get('currency', 'UAH'),
                            'status': tx.get('status', 'completed'),
                            'merchant': tx.get('merchant', ''),
                            'location': tx.get('location', '')
                        })
                    
                    logger.info(f"Получено {len(transactions)} транзакций из Raiffeisen")
                    return transactions
                else:
                    raise DataError(f"Ошибка получения транзакций: {response.status}")
                    
        except Exception as e:
            logger.error(f"Ошибка получения транзакций Raiffeisen: {e}")
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
            logger.error(f"Ошибка получения баланса Raiffeisen: {e}")
            raise DataError(f"Не удалось получить баланс: {e}")
    
    def _categorize_transaction(self, transaction: Dict) -> str:
        """
        Категоризация транзакции на основе данных Raiffeisen
        """
        description = transaction.get('description', '').lower()
        category = transaction.get('category', '').lower()
        merchant = transaction.get('merchant', '').lower()
        
        # Используем категорию от банка, если есть
        if category:
            category_map = {
                'groceries': 'Продукты',
                'restaurants': 'Развлечения',
                'transport': 'Транспорт',
                'healthcare': 'Здоровье',
                'shopping': 'Покупки',
                'utilities': 'Коммунальные услуги',
                'entertainment': 'Развлечения',
                'salary': 'Доходы',
                'transfer': 'Переводы',
                'atm': 'Снятие наличных',
                'fuel': 'Транспорт',
                'pharmacy': 'Здоровье',
                'supermarket': 'Продукты'
            }
            return category_map.get(category, 'Другое')
        
        # Fallback на описание и merchant
        full_text = f"{description} {merchant}".lower()
        
        if any(word in full_text for word in ['продукты', 'супермаркет', 'магазин', 'еда', 'продуктовый']):
            return 'Продукты'
        elif any(word in full_text for word in ['ресторан', 'кафе', 'бар', 'еда', 'ресторан']):
            return 'Развлечения'
        elif any(word in full_text for word in ['транспорт', 'такси', 'автобус', 'метро', 'бензин', 'заправка']):
            return 'Транспорт'
        elif any(word in full_text for word in ['аптека', 'медицина', 'врач', 'здоровье', 'больница']):
            return 'Здоровье'
        elif any(word in full_text for word in ['покупки', 'одежда', 'обувь', 'товары', 'магазин']):
            return 'Покупки'
        elif any(word in full_text for word in ['коммунальные', 'электричество', 'газ', 'вода', 'отопление']):
            return 'Коммунальные услуги'
        elif any(word in full_text for word in ['зарплата', 'доход', 'пенсия', 'стипендия', 'зарплата']):
            return 'Доходы'
        elif any(word in full_text for word in ['банкомат', 'atm', 'снятие', 'наличные']):
            return 'Снятие наличных'
        else:
            return 'Другое'
    
    async def get_cards(self) -> List[Dict[str, Any]]:
        """
        Получение информации о картах (специфично для Raiffeisen)
        """
        try:
            if not self.is_connected:
                raise ConnectionError("Не подключен к Raiffeisen")
            
            async with self.session.get(f"{self.api_base_url}/api/v1/cards") as response:
                if response.status == 200:
                    data = await response.json()
                    cards = []
                    
                    for card in data.get('cards', []):
                        cards.append({
                            'id': card['id'],
                            'masked_pan': card.get('masked_pan', ''),
                            'type': card.get('type', ''),
                            'status': card.get('status', ''),
                            'currency': card.get('currency', 'UAH'),
                            'expiry_date': card.get('expiry_date', ''),
                            'balance': float(card.get('balance', 0))
                        })
                    
                    logger.info(f"Получено {len(cards)} карт из Raiffeisen")
                    return cards
                else:
                    raise DataError(f"Ошибка получения карт: {response.status}")
                    
        except Exception as e:
            logger.error(f"Ошибка получения карт Raiffeisen: {e}")
            raise DataError(f"Не удалось получить карты: {e}")
    
    async def get_exchange_rates(self) -> Dict[str, Any]:
        """
        Получение курсов валют (специфично для Raiffeisen)
        """
        try:
            if not self.is_connected:
                raise ConnectionError("Не подключен к Raiffeisen")
            
            async with self.session.get(f"{self.api_base_url}/api/v1/exchange-rates") as response:
                if response.status == 200:
                    rates_data = await response.json()
                    return rates_data
                else:
                    raise DataError(f"Ошибка получения курсов валют: {response.status}")
                    
        except Exception as e:
            logger.error(f"Ошибка получения курсов валют Raiffeisen: {e}")
            raise DataError(f"Не удалось получить курсы валют: {e}")
    
    async def disconnect(self):
        """
        Отключение от API
        """
        if self.session:
            await self.session.close()
            self.session = None
        self.is_connected = False
        self.access_token = None
        logger.info(f"Отключен от {self.bank_name}")
