"""
Сервис для работы с AI функциями
"""

from typing import List, Dict, Any, Optional
import logging

from ..ai.advisor import FinancialAdvisor
from ..ai.categorizer import TransactionCategorizer
from ..ai.analyzer import FinancialAnalyzer
from .transaction_service import TransactionService
from .account_service import AccountService

logger = logging.getLogger(__name__)


class AIService:
    """Сервис для работы с AI функциями"""
    
    def __init__(self):
        self.advisor = FinancialAdvisor()
        self.categorizer = TransactionCategorizer()
        self.analyzer = FinancialAnalyzer()
        self.transaction_service = TransactionService()
        self.account_service = AccountService()
    
    async def categorize_all_transactions(self) -> Dict[str, Any]:
        """AI категоризация всех транзакций"""
        try:
            logger.info("Начинаем AI категоризацию транзакций...")
            
            # Получаем все транзакции
            transactions = await self.transaction_service.get_all_transactions()
            
            if not transactions:
                return {"message": "Нет транзакций для категоризации", "categorized": 0}
            
            # Конвертируем в формат для категоризатора
            transaction_data = []
            for t in transactions:
                transaction_data.append({
                    "id": t.id,
                    "description": t.description or "",
                    "amount": t.amount,
                    "category": t.category
                })
            
            # Категоризируем
            categorized = await self.categorizer.categorize_batch(transaction_data)
            
            # Подсчитываем статистику
            categorized_count = sum(1 for t in categorized if t.get("category") and t["category"] != "Другое")
            total_count = len(categorized)
            
            logger.info(f"Категоризировано {categorized_count} из {total_count} транзакций")
            
            return {
                "message": "Категоризация завершена",
                "total_transactions": total_count,
                "categorized": categorized_count,
                "categorization_rate": categorized_count / total_count if total_count > 0 else 0
            }
            
        except Exception as e:
            logger.error(f"Ошибка AI категоризации: {e}")
            raise
    
    async def analyze_financial_health(self) -> Dict[str, Any]:
        """Анализ финансового здоровья"""
        try:
            logger.info("Начинаем анализ финансового здоровья...")
            
            # Собираем данные
            accounts = await self.account_service.get_all_accounts()
            transactions = await self.transaction_service.get_all_transactions()
            
            # Подготавливаем данные для анализа
            financial_data = {
                "accounts": [account.dict() for account in accounts],
                "transactions": [transaction.dict() for transaction in transactions],
                "total_income": sum(t.amount for t in transactions if t.amount > 0),
                "total_expenses": abs(sum(t.amount for t in transactions if t.amount < 0)),
                "total_investments": 0,  # Пока что заглушка
                "categories": list(set(t.category for t in transactions if t.category))
            }
            
            # Анализируем
            analysis = await self.advisor.analyze_financial_health(financial_data)
            
            logger.info("Анализ финансового здоровья завершен")
            return analysis
            
        except Exception as e:
            logger.error(f"Ошибка анализа финансового здоровья: {e}")
            raise
    
    async def get_financial_advice(self) -> Dict[str, Any]:
        """Получение рекомендаций от AI консультанта"""
        try:
            logger.info("Получение рекомендаций от AI консультанта...")
            
            # Собираем данные для анализа
            accounts = await self.account_service.get_all_accounts()
            transactions = await self.transaction_service.get_all_transactions()
            
            financial_data = {
                "accounts": [account.dict() for account in accounts],
                "transactions": [transaction.dict() for transaction in transactions]
            }
            
            # Получаем рекомендации
            advice = await self.advisor.analyze_financial_health(financial_data)
            
            return {
                "advice": advice.get("recommendations", []),
                "score": advice.get("overall_score", 0),
                "alerts": advice.get("risk_alerts", []),
                "timestamp": advice.get("timestamp")
            }
            
        except Exception as e:
            logger.error(f"Ошибка получения рекомендаций: {e}")
            raise
    
    async def learn_from_feedback(self, feedback_data: Dict[str, Any]) -> Dict[str, Any]:
        """Обучение AI на основе обратной связи"""
        try:
            transaction_id = feedback_data.get("transaction_id")
            correct_category = feedback_data.get("correct_category")
            
            if not transaction_id or not correct_category:
                raise ValueError("Необходимы transaction_id и correct_category")
            
            # Обучаем категоризатор
            await self.categorizer.learn_from_user_feedback(transaction_id, correct_category)
            
            return {
                "message": "Обратная связь сохранена",
                "transaction_id": transaction_id,
                "correct_category": correct_category
            }
            
        except Exception as e:
            logger.error(f"Ошибка обучения AI: {e}")
            raise
    
    async def get_spending_analysis(self, period_days: int = 30) -> Dict[str, Any]:
        """Анализ расходов за период"""
        try:
            transactions = await self.transaction_service.get_all_transactions()
            
            # Конвертируем в формат для анализатора
            transaction_data = []
            for t in transactions:
                transaction_data.append({
                    "amount": t.amount,
                    "description": t.description or "",
                    "category": t.category,
                    "transaction_date": t.transaction_date.isoformat() if t.transaction_date else None
                })
            
            # Анализируем расходы
            analysis = await self.analyzer.analyze_spending_trends(transaction_data, period_days)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Ошибка анализа расходов: {e}")
            raise
    
    async def get_income_analysis(self, period_days: int = 30) -> Dict[str, Any]:
        """Анализ доходов за период"""
        try:
            transactions = await self.transaction_service.get_all_transactions()
            
            # Конвертируем в формат для анализатора
            transaction_data = []
            for t in transactions:
                transaction_data.append({
                    "amount": t.amount,
                    "description": t.description or "",
                    "category": t.category,
                    "transaction_date": t.transaction_date.isoformat() if t.transaction_date else None
                })
            
            # Анализируем доходы
            analysis = await self.analyzer.analyze_income_trends(transaction_data, period_days)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Ошибка анализа доходов: {e}")
            raise


