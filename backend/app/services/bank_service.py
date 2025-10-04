"""
Сервис для работы с банками (исправленная версия)
Содержит бизнес-логику для управления банковскими данными
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from ..models.database import db
from ..models.bank import Bank, BankCreate, BankUpdate, BankWithAccounts

logger = logging.getLogger(__name__)


class BankService:
    """
    Сервис для работы с банками
    
    Функции:
    - CRUD операции с банками
    - Получение статистики по банкам
    - Интеграция с внешними банковскими API
    """
    
    def __init__(self):
        """Инициализация сервиса"""
        self.db = db
    
    async def create_bank(self, bank_data: BankCreate) -> Bank:
        """
        Создание нового банка
        
        Args:
            bank_data: Данные для создания банка
            
        Returns:
            Bank: Созданный банк
        """
        try:
            logger.info(f"Создание банка: {bank_data.name}")
            
            query = """
                INSERT INTO banks (name, country, currency) 
                VALUES (%s, %s, %s) 
                RETURNING id, name, country, currency, created_at
            """
            
            # Используем execute_query для INSERT с RETURNING
            result = await self.db.execute_query(
                query, 
                (bank_data.name, bank_data.country, bank_data.currency)
            )
            
            if not result:
                raise Exception("Не удалось создать банк")
            
            bank = Bank(**result[0])
            logger.info(f"Банк создан с ID: {bank.id}")
            
            return bank
            
        except Exception as e:
            logger.error(f"Ошибка создания банка: {e}")
            raise
    
    async def get_bank(self, bank_id: int) -> Optional[Bank]:
        """
        Получение банка по ID
        
        Args:
            bank_id: ID банка
            
        Returns:
            Bank: Данные банка или None
        """
        try:
            query = "SELECT * FROM banks WHERE id = %s"
            result = await self.db.execute_query(query, (bank_id,))
            
            if result:
                return Bank(**result[0])
            return None
            
        except Exception as e:
            logger.error(f"Ошибка получения банка {bank_id}: {e}")
            raise
    
    async def get_all_banks(self) -> List[Bank]:
        """
        Получение всех банков
        
        Returns:
            List[Bank]: Список всех банков
        """
        try:
            query = "SELECT * FROM banks ORDER BY name"
            result = await self.db.execute_query(query)
            
            return [Bank(**row) for row in result]
            
        except Exception as e:
            logger.error(f"Ошибка получения списка банков: {e}")
            raise
    
    async def get_banks_with_accounts(self) -> List[BankWithAccounts]:
        """
        Получение банков с информацией о счетах
        
        Returns:
            List[BankWithAccounts]: Банки с данными о счетах
        """
        try:
            query = """
                SELECT 
                    b.*,
                    COUNT(a.id) as accounts_count,
                    COALESCE(SUM(a.balance), 0) as total_balance
                FROM banks b
                LEFT JOIN accounts a ON b.id = a.bank_id AND a.is_active = true
                GROUP BY b.id, b.name, b.country, b.currency, b.created_at
                ORDER BY b.name
            """
            
            result = await self.db.execute_query(query)
            
            banks = []
            for row in result:
                bank_data = {
                    'id': row['id'],
                    'name': row['name'],
                    'country': row['country'],
                    'currency': row['currency'],
                    'created_at': row['created_at'],
                    'accounts_count': row['accounts_count'],
                    'total_balance': float(row['total_balance'])
                }
                banks.append(BankWithAccounts(**bank_data))
            
            return banks
            
        except Exception as e:
            logger.error(f"Ошибка получения банков с счетами: {e}")
            raise
    
    async def get_bank_statistics(self) -> Dict[str, Any]:
        """
        Получение статистики по банкам
        
        Returns:
            Dict: Статистика банков
        """
        try:
            # Общее количество банков
            total_banks_query = "SELECT COUNT(*) as total FROM banks"
            total_result = await self.db.execute_query(total_banks_query)
            total_banks = total_result[0]['total'] if total_result else 0
            
            # Банки по странам
            countries_query = """
                SELECT country, COUNT(*) as count 
                FROM banks 
                GROUP BY country 
                ORDER BY count DESC
            """
            countries_result = await self.db.execute_query(countries_query)
            
            # Банки по валютам
            currencies_query = """
                SELECT currency, COUNT(*) as count 
                FROM banks 
                GROUP BY currency 
                ORDER BY count DESC
            """
            currencies_result = await self.db.execute_query(currencies_query)
            
            return {
                "total_banks": total_banks,
                "by_country": {row['country']: row['count'] for row in countries_result},
                "by_currency": {row['currency']: row['count'] for row in currencies_result}
            }
            
        except Exception as e:
            logger.error(f"Ошибка получения статистики банков: {e}")
            raise
    
    async def sync_bank_data(self, bank_id: int) -> Dict[str, Any]:
        """
        Синхронизация данных с банком
        
        Args:
            bank_id: ID банка
            
        Returns:
            Dict: Результат синхронизации
        """
        try:
            logger.info(f"Синхронизация данных банка {bank_id}")
            
            # Здесь будет логика синхронизации с внешними API
            # Пока что заглушка
            
            bank = await self.get_bank(bank_id)
            if not bank:
                raise Exception("Банк не найден")
            
            # Имитация синхронизации
            import asyncio
            await asyncio.sleep(1)
            
            return {
                "bank_id": bank_id,
                "bank_name": bank.name,
                "status": "success",
                "synced_at": datetime.now().isoformat(),
                "accounts_updated": 0,
                "transactions_updated": 0
            }
            
        except Exception as e:
            logger.error(f"Ошибка синхронизации банка {bank_id}: {e}")
            raise