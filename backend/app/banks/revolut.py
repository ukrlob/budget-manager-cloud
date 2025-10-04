"""
Интеграция с Revolut API
Европейский банк с отличным API
"""

import aiohttp
import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, date
from .base import BankConnector, BankError, ConnectionError, AuthenticationError, DataError

logger = logging.getLogger(__name__)


class RevolutConnector(BankConnector):
    """
    Коннектор для Revolut API
    """
    
    def __init__(self, credentials: Dict[str, Any]):
        super().__init__("Revolut", credentials)
        self.api_base_url = "https://b2b.revolut.com/api/1.0"
        self.client_id = credentials.get('client_id')
        self.client_secret = credentials.get('client_secret')
        self.access_token = None
        self.session = None
        
    async def connect(self) -> bool:
        """
        Подключение к Revolut API
        """
        try:
            logger.info(f"Подключение к {self.bank_name} API...")
            
            if not self.client_id or not self.client_secret:
                raise AuthenticationError("Revolut client_id и client_secret не найдены")
            
            # Создаем HTTP сессию
            self.session = aiohttp.ClientSession()
            
            # Получаем access token
            await self._get_access_token()
            
            self.is_connected = True
            logger.info(f"Успешно подключен к {self.bank_name} API")
            return True
            
        except Exception as e:
            logger.error(f"Oшибка подключения к {self.bank_name}: {e}")
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
                'client_secret': self.client_secret
            }
            
            async with self.session.post(
                f"{self.api_base_url}/auth/token",
                data=auth_data
            ) as response:
                if response.status == 200:
                    token_data = await response.json()
                    self.access_token = token_data['access_token']
                    
                    # Обновляем заголовки сессии
                    self.session.headers.update({
                        'Authorization': f'Bearer {self.access_token}',
                        'Content-Type': 'application/json'
                    })
                    
                    logger.info("Revolut access token получен")
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
                raise ConnectionError("Не подключен к Revolut")
            
            async with self.session.get(f"{self.api_base_url}/accounts") as response:
                if response.status == 200:
                    data = await response.json()
                    accounts = []
                    
                    for account in data:
                        accounts.append({
                            'id': account['id'],
                            'name': account.get('name', 'Revolut Account'),
                            'type': account.get('type', 'current'),
                            'balance': float(account['balance']),
                            'currency': account['currency'],
                            'bank_name': 'Revolut',
                            'state': account.get('state', 'active')
                        })
                    
                    logger.info(f"Получено {len(accounts)} счетов из Revolut")
                    return accounts
                else:
                    raise DataError(f"Ошибка получения счетов: {response.status}")
                    
        except Exception as e:
            logger.error(f"Ошибка получения счетов Revolut: {e}")
            raise DataError(f"Не удалось получить счета: {e}")
    
    async def get_transactions(self, account_id: str, from_date: Optional[datetime] = None, to_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """
        Получение транзакций по счету
        """
        try:
            if not self.is_connected:
                raise ConnectionError("Не подключен к Revolut")
            
            # Формируем параметры запроса
            params = {}
            if from_date:
                params['from'] = from_date.isoformat()
            if to_date:
                params['to'] = to_date.isoformat()
            
            url = f"{self.api_base_url}/transactions"
            if account_id:
                url += f"?account={account_id}"
            
            async with self.session.get(url, params=params) as response:
                if response.status == 200:
                    transactions_data = await response.json()
                    transactions = []
                    
                    for tx in transactions_data:
                        transactions.append({
                            'id': tx['id'],
                            'amount': float(tx['amount']),
                            'description': tx.get('description', ''),
                            'date': datetime.fromisoformat(tx['created_at'].replace('Z', '+00:00')).date(),
                            'category': self._categorize_transaction(tx),
                            'account_id': account_id,
                            'currency': tx.get('currency', 'EUR'),
                            'state': tx.get('state', 'completed')
                        })
                    
                    logger.info(f"Получено {len(transactions)} транзакций из Revolut")
                    return transactions
                else:
                    raise DataError(f"Ошибка получения транзакций: {response.status}")
                    
        except Exception as e:
            logger.error(f"Ошибка получения транзакций Revolut: {e}")
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
            logger.error(f"Ошибка получения баланса Revolut: {e}")
            raise DataError(f"Не удалось получить баланс: {e}")
    
    def _categorize_transaction(self, transaction: Dict) -> str:
        """
        Категоризация транзакции на основе данных Revolut
        """
        # Revolut предоставляет категоризацию в поле 'merchant'
        merchant = transaction.get('merchant', {})
        category = merchant.get('category', '')
        
        # Маппинг категорий Revolut
        category_map = {
            'groceries': 'Продукты',
            'restaurants': 'Развлечения',
            'transport': 'Транспорт',
            'healthcare': 'Здоровье',
            'shopping': 'Покупки',
            'utilities': 'Коммунальные услуги',
            'entertainment': 'Развлечения',
            'travel': 'Путешествия',
            'fuel': 'Транспорт',
            'pharmacy': 'Здоровье',
            'supermarket': 'Продукты',
            'atm': 'Снятие наличных',
            'transfer': 'Переводы',
            'salary': 'Доходы',
            'investment': 'Инвестиции'
        }
        
        return category_map.get(category.lower(), 'Другое')
    
    async def get_exchange_rates(self) -> Dict[str, Any]:
        """
        Получение курсов валют (специфично для Revolut)
        """
        try:
            if not self.is_connected:
                raise ConnectionError("Не подключен к Revolut")
            
            async with self.session.get(f"{self.api_base_url}/rate") as response:
                if response.status == 200:
                    rates_data = await response.json()
                    return rates_data
                else:
                    raise DataError(f"Ошибка получения курсов валют: {response.status}")
                    
        except Exception as e:
            logger.error(f"Ошибка получения курсов валют Revolut: {e}")
            raise DataError(f"Не удалось получить курсы валют: {e}")
    
    async def get_cards(self) -> List[Dict[str, Any]]:
        """
        Получение информации о картах (специфично для Revolut)
        """
        try:
            if not self.is_connected:
                raise ConnectionError("Не подключен к Revolut")
            
            async with self.session.get(f"{self.api_base_url}/cards") as response:
                if response.status == 200:
                    cards_data = await response.json()
                    cards = []
                    
                    for card in cards_data:
                        cards.append({
                            'id': card['id'],
                            'masked_pan': card.get('maskedPan', ''),
                            'state': card.get('state', ''),
                            'type': card.get('type', ''),
                            'currency': card.get('currency', ''),
                            'public_token': card.get('publicToken', '')
                        })
                    
                    logger.info(f"Получено {len(cards)} карт из Revolut")
                    return cards
                else:
                    raise DataError(f"Ошибка получения карт: {response.status}")
                    
        except Exception as e:
            logger.error(f"Ошибка получения карт Revolut: {e}")
            raise DataError(f"Не удалось получить карты: {e}")
    
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
