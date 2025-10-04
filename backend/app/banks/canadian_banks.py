"""
Интеграция с канадскими банками через Plaid
RBC, BMO, TD Bank, Scotiabank, CIBC
"""

import aiohttp
import asyncio
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, date
from .base import BankConnector, BankError, ConnectionError, AuthenticationError, DataError

logger = logging.getLogger(__name__)


class CanadianBankConnector(BankConnector):
    """
    Коннектор для канадских банков через Plaid
    """
    
    def __init__(self, credentials: Dict[str, Any]):
        super().__init__("Canadian Banks", credentials)
        self.plaid_client_id = credentials.get('plaid_client_id')
        self.plaid_secret = credentials.get('plaid_secret')
        self.plaid_environment = credentials.get('plaid_environment', 'sandbox')
        self.access_token = credentials.get('access_token')
        self.item_id = credentials.get('item_id')
        self.session = None
        
    async def connect(self) -> bool:
        """
        Подключение к канадским банкам через Plaid
        """
        try:
            logger.info(f"Подключение к {self.bank_name} через Plaid...")
            
            if not all([self.plaid_client_id, self.plaid_secret]):
                raise AuthenticationError("Plaid client_id и secret не найдены")
            
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
            logger.info(f"Успешно подключен к {self.bank_name} через Plaid")
            return True
            
        except Exception as e:
            logger.error(f"Ошибка подключения к {self.bank_name}: {e}")
            if self.session:
                await self.session.close()
                self.session = None
            raise ConnectionError(f"Не удалось подключиться к {self.bank_name}: {e}")
    
    async def _test_connection(self):
        """
        Тестирование подключения к Plaid API
        """
        try:
            # Тестируем подключение к Plaid
            url = f"https://{self.plaid_environment}.plaid.com/institutions/get"
            data = {
                'client_id': self.plaid_client_id,
                'secret': self.plaid_secret,
                'country_codes': ['CA'],
                'count': 5
            }
            
            async with self.session.post(url, json=data) as response:
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"Plaid подключен. Найдено {len(data.get('institutions', []))} канадских банков")
                else:
                    raise ConnectionError(f"Ошибка Plaid API: {response.status}")
        except aiohttp.ClientError as e:
            raise ConnectionError(f"Ошибка сети: {e}")
    
    async def get_supported_banks(self) -> List[Dict[str, Any]]:
        """
        Получение списка поддерживаемых канадских банков
        """
        try:
            if not self.is_connected:
                raise ConnectionError("Не подключен к Plaid")
            
            url = f"https://{self.plaid_environment}.plaid.com/institutions/get"
            data = {
                'client_id': self.plaid_client_id,
                'secret': self.plaid_secret,
                'country_codes': ['CA'],
                'count': 100
            }
            
            async with self.session.post(url, json=data) as response:
                if response.status == 200:
                    data = await response.json()
                    banks = []
                    
                    for bank in data.get('institutions', []):
                        banks.append({
                            'institution_id': bank['institution_id'],
                            'name': bank['name'],
                            'country': 'CA',
                            'currency': 'CAD',
                            'logo': bank.get('logo', ''),
                            'primary_color': bank.get('primary_color', ''),
                            'url': bank.get('url', ''),
                            'products': bank.get('products', [])
                        })
                    
                    logger.info(f"Получено {len(banks)} канадских банков из Plaid")
                    return banks
                else:
                    raise DataError(f"Ошибка получения банков: {response.status}")
                    
        except Exception as e:
            logger.error(f"Ошибка получения банков: {e}")
            raise DataError(f"Не удалось получить банки: {e}")
    
    async def get_accounts(self) -> List[Dict[str, Any]]:
        """
        Получение списка счетов
        """
        try:
            if not self.is_connected:
                raise ConnectionError("Не подключен к Plaid")
            
            if not self.access_token:
                raise AuthenticationError("Access token не найден")
            
            url = f"https://{self.plaid_environment}.plaid.com/accounts/get"
            data = {
                'client_id': self.plaid_client_id,
                'secret': self.plaid_secret,
                'access_token': self.access_token
            }
            
            async with self.session.post(url, json=data) as response:
                if response.status == 200:
                    data = await response.json()
                    accounts = []
                    
                    for account in data.get('accounts', []):
                        accounts.append({
                            'id': account['account_id'],
                            'name': account['name'],
                            'type': account['type'],
                            'subtype': account['subtype'],
                            'balance': account['balances']['current'],
                            'available_balance': account['balances']['available'],
                            'currency': account['balances']['iso_currency_code'],
                            'mask': account['mask'],
                            'bank_name': self._get_bank_name(account),
                            'country': 'CA'
                        })
                    
                    logger.info(f"Получено {len(accounts)} счетов из канадских банков")
                    return accounts
                else:
                    raise DataError(f"Ошибка получения счетов: {response.status}")
                    
        except Exception as e:
            logger.error(f"Ошибка получения счетов: {e}")
            raise DataError(f"Не удалось получить счета: {e}")
    
    async def get_transactions(self, account_id: str, from_date: Optional[datetime] = None, to_date: Optional[datetime] = None) -> List[Dict[str, Any]]:
        """
        Получение транзакций по счету
        """
        try:
            if not self.is_connected:
                raise ConnectionError("Не подключен к Plaid")
            
            if not self.access_token:
                raise AuthenticationError("Access token не найден")
            
            # Формируем даты
            if not from_date:
                from_date = datetime.now().replace(day=1)
            if not to_date:
                to_date = datetime.now()
            
            url = f"https://{self.plaid_environment}.plaid.com/transactions/get"
            data = {
                'client_id': self.plaid_client_id,
                'secret': self.plaid_secret,
                'access_token': self.access_token,
                'start_date': from_date.strftime('%Y-%m-%d'),
                'end_date': to_date.strftime('%Y-%m-%d'),
                'account_ids': [account_id]
            }
            
            async with self.session.post(url, json=data) as response:
                if response.status == 200:
                    data = await response.json()
                    transactions = []
                    
                    for tx in data.get('transactions', []):
                        transactions.append({
                            'id': tx['transaction_id'],
                            'amount': tx['amount'],
                            'description': tx['name'],
                            'date': datetime.strptime(tx['date'], '%Y-%m-%d').date(),
                            'category': self._categorize_transaction(tx),
                            'account_id': account_id,
                            'currency': tx['iso_currency_code'],
                            'merchant_name': tx.get('merchant_name', ''),
                            'location': tx.get('location', {}),
                            'payment_meta': tx.get('payment_meta', {})
                        })
                    
                    logger.info(f"Получено {len(transactions)} транзакций из канадских банков")
                    return transactions
                else:
                    raise DataError(f"Ошибка получения транзакций: {response.status}")
                    
        except Exception as e:
            logger.error(f"Ошибка получения транзакций: {e}")
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
                        'available_balance': account['available_balance'],
                        'currency': account['currency'],
                        'last_updated': datetime.now().isoformat()
                    }
            
            raise DataError(f"Счет {account_id} не найден")
            
        except Exception as e:
            logger.error(f"Ошибка получения баланса: {e}")
            raise DataError(f"Не удалось получить баланс: {e}")
    
    def _get_bank_name(self, account: Dict) -> str:
        """
        Получение названия банка на основе account
        """
        # В Plaid название банка обычно в institution_id
        institution_id = account.get('institution_id', '')
        
        bank_names = {
            'ins_1': 'RBC Royal Bank',
            'ins_2': 'Bank of Montreal',
            'ins_3': 'TD Bank',
            'ins_4': 'Scotiabank',
            'ins_5': 'CIBC',
            'rbc': 'RBC Royal Bank',
            'bmo': 'Bank of Montreal',
            'td': 'TD Bank',
            'scotia': 'Scotiabank',
            'cibc': 'CIBC'
        }
        
        for key, name in bank_names.items():
            if key in institution_id.lower():
                return name
        
        return 'Canadian Bank'
    
    def _categorize_transaction(self, transaction: Dict) -> str:
        """
        Категоризация транзакции на основе данных Plaid
        """
        # Plaid предоставляет категоризацию
        category = transaction.get('category', [])
        if category:
            primary_category = category[0] if category else 'Other'
            
            category_map = {
                'Food and Drink': 'Продукты',
                'Shops': 'Покупки',
                'Transportation': 'Транспорт',
                'Healthcare': 'Здоровье',
                'Entertainment': 'Развлечения',
                'Bills and Utilities': 'Коммунальные услуги',
                'Financial': 'Финансы',
                'Government and Non-Profit': 'Государство',
                'Travel': 'Путешествия',
                'Education': 'Образование',
                'Personal Care': 'Личная гигиена',
                'Business Services': 'Бизнес услуги',
                'Recreation and Sports': 'Спорт и отдых',
                'Home': 'Дом',
                'Other': 'Другое'
            }
            
            return category_map.get(primary_category, 'Другое')
        
        return 'Другое'
    
    async def create_link_token(self, user_id: str) -> Dict[str, Any]:
        """
        Создание Link token для Plaid Link
        """
        try:
            url = f"https://{self.plaid_environment}.plaid.com/link/token/create"
            data = {
                'client_id': self.plaid_client_id,
                'secret': self.plaid_secret,
                'client_name': 'Budget Manager Cloud',
                'country_codes': ['CA'],
                'language': 'en',
                'user': {
                    'client_user_id': user_id
                },
                'products': ['transactions', 'auth']
            }
            
            async with self.session.post(url, json=data) as response:
                if response.status == 200:
                    data = await response.json()
                    return {
                        'link_token': data['link_token'],
                        'expiration': data['expiration']
                    }
                else:
                    raise DataError(f"Ошибка создания Link token: {response.status}")
                    
        except Exception as e:
            logger.error(f"Ошибка создания Link token: {e}")
            raise DataError(f"Не удалось создать Link token: {e}")
    
    async def exchange_public_token(self, public_token: str) -> Dict[str, str]:
        """
        Обмен публичного токена на access_token
        """
        try:
            url = f"https://{self.plaid_environment}.plaid.com/item/public_token/exchange"
            data = {
                'client_id': self.plaid_client_id,
                'secret': self.plaid_secret,
                'public_token': public_token
            }
            
            async with self.session.post(url, json=data) as response:
                if response.status == 200:
                    data = await response.json()
                    self.access_token = data['access_token']
                    self.item_id = data['item_id']
                    
                    return {
                        'access_token': self.access_token,
                        'item_id': self.item_id
                    }
                else:
                    raise DataError(f"Ошибка обмена токена: {response.status}")
                    
        except Exception as e:
            logger.error(f"Ошибка обмена токена: {e}")
            raise DataError(f"Не удалось обменять токен: {e}")
    
    async def disconnect(self):
        """
        Отключение от Plaid
        """
        if self.session:
            await self.session.close()
            self.session = None
        self.is_connected = False
        logger.info(f"Отключен от {self.bank_name}")
