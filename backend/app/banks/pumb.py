"""
Интеграция с PUMB API
Украинский банк с ограниченным API
"""

import aiohttp
import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, date
from .base import BankConnector, BankError, ConnectionError, AuthenticationError, DataError

logger = logging.getLogger(__name__)


class PUMBConnector(BankConnector):
    """
    Коннектор для PUMB API
    """
    
    def __init__(self, credentials: Dict[str, Any]):
        super().__init__("PUMB", credentials)
        self.api_base_url = "https://api.pumb.ua"
        self.client_id = credentials.get('client_id')
        self.client_secret = credentials.get('client_secret')
        self.access_token = None
        self.session = None
        
    async def connect(self) -> bool:
        """
        Подключение к PUMB API
        """
        try:
            logger.info(f"Подключение к {self.bank_name} API...")
            
            if not self.client_id or not self.client_secret:
                raise AuthenticationError("PUMB client_id и client_secret не найдены")
            
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
                'client_secret': self.client_secret
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
                        'Content-Type': 'application/json'
                    })
                    
                    logger.info("PUMB access token получен")
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
                raise ConnectionError("Не подключен к PUMB")
            
            async with self.session.get(f"{self.api_base_url}/api/accounts") as response:
                if response.status == 200:
                    data = await response.json()
                    accounts = []
                    
                    for account in data.get('accounts', []):
                        accounts.append({
                            'id': account['id'],
                            'name': f"PUMB {account.get('type', 'Account')}",
                            'type': account.get('type', 'current'),
                            'balance': float(account.get('balance', 0)),
                            'currency': account.get('currency', 'UAH'),
                            'bank_name': 'PUMB',
                            'account_number': account.get('account_number', ''),
                            'status': account.get('status', 'active')
                        })
                    
                    logger.info(f"Получено {len(accounts)} счетов из PUMB")
                    return accounts
                else:
                    raise DataError(f"Ошибка получения счетов: {response.status}")
                    
        except Exception as e:
            logger.error(f"Ошибка получения счетов PUMB: {e}")
            raise DataError(f"Не удалось получить счета: {e}")
    
    async def get_transactions(self, account_id: str, from_date: Optional[datetime] = None, to_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """
        Получение транзакций по счету
        """
        try:
            if not self.is_connected:
                raise ConnectionError("Не подключен к PUMB")
            
            # Формируем параметры запроса
            params = {'account_id': account_id}
            if from_date:
                params['from_date'] = from_date.isoformat()
            if to_date:
                params['to_date'] = to_date.isoformat()
            
            async with self.session.get(f"{self.api_base_url}/api/transactions", params=params) as response:
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
                            'status': tx.get('status', 'completed')
                        })
                    
                    logger.info(f"Получено {len(transactions)} транзакций из PUMB")
                    return transactions
                else:
                    raise DataError(f"Ошибка получения транзакций: {response.status}")
                    
        except Exception as e:
            logger.error(f"Ошибка получения транзакций PUMB: {e}")
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
            logger.error(f"Ошибка получения баланса PUMB: {e}")
            raise DataError(f"Не удалось получить баланс: {e}")
    
    def _categorize_transaction(self, transaction: Dict) -> str:
        """
        Категоризация транзакции на основе данных PUMB
        """
        description = transaction.get('description', '').lower()
        category = transaction.get('category', '').lower()
        
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
                'transfer': 'Переводы'
            }
            return category_map.get(category, 'Другое')
        
        # Fallback на описание
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
