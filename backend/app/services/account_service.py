"""
Сервис для работы со счетами
"""

from typing import List, Optional, Dict, Any
from datetime import datetime
import logging

from ..models.database import db
from ..models.account import Account, AccountCreate, AccountUpdate, AccountWithBank

logger = logging.getLogger(__name__)


class AccountService:
    """Сервис для работы со счетами"""
    
    def __init__(self):
        self.db = db
    
    async def create_account(self, account_data: AccountCreate) -> Account:
        """Создание нового счета"""
        try:
            query = """
                INSERT INTO accounts (bank_id, account_name, account_number, balance, currency) 
                VALUES (%s, %s, %s, %s, %s) 
                RETURNING id, bank_id, account_name, account_number, balance, currency, is_active, created_at
            """
            
            result = await self.db.execute_query(
                query,
                (account_data.bank_id, account_data.account_name, 
                 account_data.account_number, account_data.balance, account_data.currency)
            )
            
            if not result:
                raise Exception("Не удалось создать счет")
            
            return Account(**result[0])
            
        except Exception as e:
            logger.error(f"Ошибка создания счета: {e}")
            raise
    
    async def get_all_accounts(self) -> List[AccountWithBank]:
        """Получение всех счетов с информацией о банках"""
        try:
            query = """
                SELECT a.*, b.name as bank_name, b.country as bank_country
                FROM accounts a 
                JOIN banks b ON a.bank_id = b.id 
                ORDER BY a.account_name
            """
            
            result = await self.db.execute_query(query)
            return [AccountWithBank(**row) for row in result]
            
        except Exception as e:
            logger.error(f"Ошибка получения счетов: {e}")
            raise
    
    async def get_balance_report(self) -> Dict[str, Any]:
        """Отчет по балансам"""
        try:
            query = """
                SELECT 
                    b.name as bank_name,
                    a.currency,
                    SUM(a.balance) as total_balance,
                    COUNT(a.id) as account_count
                FROM accounts a 
                JOIN banks b ON a.bank_id = b.id 
                WHERE a.is_active = true
                GROUP BY b.name, a.currency
                ORDER BY total_balance DESC
            """
            
            result = await self.db.execute_query(query)
            return {"balance_report": result}
            
        except Exception as e:
            logger.error(f"Ошибка получения отчета по балансам: {e}")
            raise


