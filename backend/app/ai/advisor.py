"""
AI Финансовый консультант
Анализирует полную картину финансов и дает рекомендации
"""

from typing import List, Dict, Any, Optional
from datetime import datetime, date, timedelta
import logging
import json
import google.generativeai as genai

logger = logging.getLogger(__name__)


class FinancialAdvisor:
    """
    AI консультант для анализа финансов и выдачи рекомендаций
    
    Функции:
    - Анализ расходов и доходов
    - Рекомендации по оптимизации бюджета
    - Предупреждения о рисках
    - Советы по инвестициям
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Инициализация финансового консультанта
        
        Args:
            api_key: API ключ для Gemini AI (опционально)
        """
        self.api_key = api_key or "AIzaSyBvQZvQZvQZvQZvQZvQZvQZvQZvQZvQZvQ"  # Заглушка
        self.analysis_history = []
        
        # Настройка Gemini AI
        if self.api_key:
            try:
                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel('gemini-pro')
                self.ai_enabled = True
                logger.info("Gemini AI инициализирован")
            except Exception as e:
                logger.warning(f"Не удалось инициализировать Gemini AI: {e}")
                self.ai_enabled = False
        else:
            self.ai_enabled = False
        
    async def analyze_financial_health(self, financial_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Комплексный анализ финансового здоровья
        
        Args:
            financial_data: Данные о финансах пользователя
            
        Returns:
            Dict: Анализ и рекомендации
        """
        try:
            logger.info("Начинаем анализ финансового здоровья...")
            
            # Анализ доходов и расходов
            income_analysis = await self._analyze_income(financial_data)
            expense_analysis = await self._analyze_expenses(financial_data)
            investment_analysis = await self._analyze_investments(financial_data)
            
            # Общая оценка
            overall_score = self._calculate_financial_score(
                income_analysis, expense_analysis, investment_analysis
            )
            
            # Генерация рекомендаций
            recommendations = await self._generate_recommendations(
                income_analysis, expense_analysis, investment_analysis
            )
            
            analysis_result = {
                "timestamp": datetime.now().isoformat(),
                "overall_score": overall_score,
                "income_analysis": income_analysis,
                "expense_analysis": expense_analysis,
                "investment_analysis": investment_analysis,
                "recommendations": recommendations,
                "risk_alerts": await self._check_risk_alerts(financial_data)
            }
            
            self.analysis_history.append(analysis_result)
            logger.info(f"Анализ завершен. Общий балл: {overall_score}/100")
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"Ошибка анализа финансов: {e}")
            raise
    
    async def _analyze_income(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Анализ доходов"""
        transactions = data.get("transactions", [])
        accounts = data.get("accounts", [])
        
        # Фильтруем доходы
        income_transactions = [
            t for t in transactions 
            if t.get("amount", 0) > 0 and t.get("category") == "Доходы"
        ]
        
        total_income = sum(t["amount"] for t in income_transactions)
        monthly_income = total_income / 12 if total_income > 0 else 0
        
        return {
            "total_income": total_income,
            "monthly_income": monthly_income,
            "income_stability": "stable",  # Можно добавить анализ стабильности
            "income_sources": len(set(t.get("description", "") for t in income_transactions))
        }
    
    async def _analyze_expenses(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Анализ расходов"""
        transactions = data.get("transactions", [])
        
        # Фильтруем расходы
        expense_transactions = [
            t for t in transactions 
            if t.get("amount", 0) < 0
        ]
        
        total_expenses = abs(sum(t["amount"] for t in expense_transactions))
        monthly_expenses = total_expenses / 12 if total_expenses > 0 else 0
        
        # Анализ по категориям
        category_expenses = {}
        for t in expense_transactions:
            category = t.get("category", "Другое")
            amount = abs(t["amount"])
            category_expenses[category] = category_expenses.get(category, 0) + amount
        
        return {
            "total_expenses": total_expenses,
            "monthly_expenses": monthly_expenses,
            "category_breakdown": category_expenses,
            "top_expense_category": max(category_expenses.items(), key=lambda x: x[1])[0] if category_expenses else None
        }
    
    async def _analyze_investments(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Анализ инвестиций"""
        # Здесь будет анализ инвестиционного портфеля
        # Пока что базовая структура
        return {
            "total_investments": 0,
            "portfolio_diversity": "low",
            "risk_level": "conservative",
            "expected_returns": 0
        }
    
    def _calculate_financial_score(self, income: Dict, expenses: Dict, investments: Dict) -> int:
        """Расчет общего финансового балла (0-100)"""
        score = 50  # Базовый балл
        
        # Анализ соотношения доходов и расходов
        if income.get("monthly_income", 0) > 0:
            expense_ratio = expenses.get("monthly_expenses", 0) / income.get("monthly_income", 1)
            if expense_ratio < 0.5:
                score += 20
            elif expense_ratio < 0.7:
                score += 10
            elif expense_ratio > 0.9:
                score -= 20
        
        # Бонус за диверсификацию доходов
        if income.get("income_sources", 0) > 1:
            score += 10
        
        return min(100, max(0, score))
    
    async def _generate_recommendations(self, income: Dict, expenses: Dict, investments: Dict) -> List[str]:
        """Генерация рекомендаций"""
        recommendations = []
        
        # Анализ расходов
        expense_ratio = expenses.get("monthly_expenses", 0) / max(income.get("monthly_income", 1), 1)
        
        if expense_ratio > 0.8:
            recommendations.append("⚠️ Высокий уровень расходов. Рекомендуется пересмотреть бюджет.")
        
        if expenses.get("top_expense_category"):
            recommendations.append(f"💡 Основная статья расходов: {expenses['top_expense_category']}. Рассмотрите оптимизацию.")
        
        # Рекомендации по сбережениям
        if expense_ratio < 0.7:
            recommendations.append("✅ Хорошее соотношение доходов и расходов. Можно увеличить сбережения.")
        
        return recommendations
    
    async def _check_risk_alerts(self, data: Dict[str, Any]) -> List[str]:
        """Проверка рисков"""
        alerts = []
        
        # Проверка на овердрафт
        accounts = data.get("accounts", [])
        for account in accounts:
            if account.get("balance", 0) < 0:
                alerts.append(f"🚨 Отрицательный баланс на счете {account.get('name', 'Unknown')}")
        
        return alerts
    
    async def get_investment_advice(self, portfolio_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Получение инвестиционных рекомендаций
        
        Args:
            portfolio_data: Данные о портфеле
            
        Returns:
            Dict: Инвестиционные рекомендации
        """
        if self.ai_enabled:
            try:
                # Формируем запрос для Gemini AI
                prompt = f"""
                Проанализируйте следующий инвестиционный портфель и дайте рекомендации:
                
                Данные портфеля: {json.dumps(portfolio_data, indent=2)}
                
                Пожалуйста, предоставьте:
                1. Оценку риска портфеля (консервативный/умеренный/агрессивный)
                2. Рекомендации по диверсификации
                3. Предложения по распределению активов
                4. Общие советы по управлению портфелем
                
                Ответьте на русском языке в структурированном формате.
                """
                
                response = self.model.generate_content(prompt)
                
                return {
                    "recommendations": response.text.split('\n'),
                    "risk_assessment": "moderate",
                    "suggested_allocations": {
                        "stocks": 60,
                        "bonds": 30,
                        "cash": 10
                    },
                    "ai_generated": True
                }
                
            except Exception as e:
                logger.error(f"Ошибка получения AI рекомендаций: {e}")
                # Fallback к базовым рекомендациям
                return {
                    "recommendations": [
                        "Рассмотрите диверсификацию портфеля",
                        "Обратите внимание на соотношение риск/доходность"
                    ],
                    "risk_assessment": "moderate",
                    "suggested_allocations": {
                        "stocks": 60,
                        "bonds": 30,
                        "cash": 10
                    },
                    "ai_generated": False
                }
        else:
            # Базовые рекомендации без AI
            return {
                "recommendations": [
                    "Рассмотрите диверсификацию портфеля",
                    "Обратите внимание на соотношение риск/доходность"
                ],
                "risk_assessment": "moderate",
                "suggested_allocations": {
                    "stocks": 60,
                    "bonds": 30,
                    "cash": 10
                },
                "ai_generated": False
            }
    
    def get_analysis_history(self) -> List[Dict[str, Any]]:
        """Получение истории анализов"""
        return self.analysis_history


