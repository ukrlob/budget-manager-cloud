"""
Сервис для работы с транзакциями
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, date
import logging

from ..models.database import db
from ..models.transaction import Transaction, TransactionCreate, TransactionWithAccount

logger = logging.getLogger(__name__)


class TransactionService:
    """Сервис для работы с транзакциями"""
    
    def __init__(self):
        self.db = db
    
    async def create_transaction(self, transaction_data: TransactionCreate) -> Transaction:
        """Создание новой транзакции"""
        try:
            query = """
                INSERT INTO transactions (account_id, amount, description, category, transaction_date) 
                VALUES (%s, %s, %s, %s, %s) 
                RETURNING id, account_id, amount, description, category, transaction_date, created_at
            """
            
            result = await self.db.execute_query(
                query,
                (transaction_data.account_id, transaction_data.amount,
                 transaction_data.description, transaction_data.category, 
                 transaction_data.transaction_date)
            )
            
            if not result:
                raise Exception("Не удалось создать транзакцию")
            
            return Transaction(**result[0])
            
        except Exception as e:
            logger.error(f"Ошибка создания транзакции: {e}")
            raise
    
    async def get_all_transactions(self) -> List[TransactionWithAccount]:
        """Получение всех транзакций с информацией о счетах"""
        try:
            query = """
                SELECT t.*, a.account_name, b.name as bank_name, a.currency
                FROM transactions t 
                JOIN accounts a ON t.account_id = a.id 
                JOIN banks b ON a.bank_id = b.id 
                ORDER BY t.transaction_date DESC
            """
            
            result = await self.db.execute_query(query)
            return [TransactionWithAccount(**row) for row in result]
            
        except Exception as e:
            logger.error(f"Ошибка получения транзакций: {e}")
            raise
    
    async def get_transactions_by_account(self, account_id: int) -> List[TransactionWithAccount]:
        """Получение транзакций по счету"""
        try:
            query = """
                SELECT t.*, a.account_name, b.name as bank_name, a.currency
                FROM transactions t 
                JOIN accounts a ON t.account_id = a.id 
                JOIN banks b ON a.bank_id = b.id 
                WHERE t.account_id = %s
                ORDER BY t.transaction_date DESC
            """
            
            result = await self.db.execute_query(query, (account_id,))
            return [TransactionWithAccount(**row) for row in result]
            
        except Exception as e:
            logger.error(f"Ошибка получения транзакций по счету: {e}")
            raise
    
    async def get_summary_statistics(self) -> Dict[str, Any]:
        """Общая статистика транзакций"""
        try:
            # Общее количество транзакций
            total_query = "SELECT COUNT(*) as total_transactions FROM transactions"
            total_result = await self.db.execute_query(total_query)
            total_transactions = total_result[0]['total_transactions'] if total_result else 0
            
            # Баланс по валютам
            balance_query = """
                SELECT 
                    currency,
                    SUM(balance) as total_balance,
                    COUNT(*) as account_count
                FROM accounts 
                WHERE is_active = true
                GROUP BY currency
            """
            balance_result = await self.db.execute_query(balance_query)
            
            return {
                "total_transactions": total_transactions,
                "balance_by_currency": balance_result
            }
            
        except Exception as e:
            logger.error(f"Ошибка получения статистики: {e}")
            raise
    
    async def get_categories(self) -> List[Dict[str, Any]]:
        """Получение категорий транзакций"""
        try:
            query = """
                SELECT DISTINCT category, COUNT(*) as transaction_count
                FROM transactions 
                WHERE category IS NOT NULL
                GROUP BY category
                ORDER BY transaction_count DESC
            """
            
            result = await self.db.execute_query(query)
            return result
            
        except Exception as e:
            logger.error(f"Ошибка получения категорий: {e}")
            raise
    
    async def get_transactions_report(self, start_date: str = None, end_date: str = None) -> Dict[str, Any]:
        """Отчет по транзакциям за период"""
        try:
            if start_date and end_date:
                query = """
                    SELECT 
                        t.*, 
                        a.account_name, 
                        b.name as bank_name,
                        b.currency
                    FROM transactions t 
                    JOIN accounts a ON t.account_id = a.id 
                    JOIN banks b ON a.bank_id = b.id 
                    WHERE t.transaction_date BETWEEN %s AND %s
                    ORDER BY t.transaction_date DESC
                """
                result = await self.db.execute_query(query, (start_date, end_date))
            else:
                query = """
                    SELECT 
                        t.*, 
                        a.account_name, 
                        b.name as bank_name,
                        b.currency
                    FROM transactions t 
                    JOIN accounts a ON t.account_id = a.id 
                    JOIN banks b ON a.bank_id = b.id 
                    ORDER BY t.transaction_date DESC
                """
                result = await self.db.execute_query(query)
            
            return {"transactions_report": result}
            
        except Exception as e:
            logger.error(f"Ошибка получения отчета по транзакциям: {e}")
            raise


