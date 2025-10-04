"""
Финансовый анализатор
Анализирует финансовые данные и генерирует инсайты
"""

from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, date, timedelta
import statistics
import logging

logger = logging.getLogger(__name__)


class FinancialAnalyzer:
    """
    Анализатор финансовых данных
    
    Функции:
    - Анализ трендов доходов и расходов
    - Выявление аномалий
    - Прогнозирование
    - Генерация инсайтов
    """
    
    def __init__(self):
        """Инициализация анализатора"""
        self.analysis_cache = {}
        self.cache_ttl = 3600  # 1 час
    
    async def analyze_spending_trends(self, transactions: List[Dict[str, Any]], 
                                    period_days: int = 30) -> Dict[str, Any]:
        """
        Анализ трендов расходов
        
        Args:
            transactions: Список транзакций
            period_days: Период анализа в днях
            
        Returns:
            Dict: Анализ трендов
        """
        try:
            logger.info(f"Анализ трендов расходов за {period_days} дней...")
            
            # Фильтруем расходы за период
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=period_days)
            
            period_transactions = [
                t for t in transactions
                if t.get("amount", 0) < 0 and 
                self._parse_date(t.get("transaction_date", "")) >= start_date
            ]
            
            if not period_transactions:
                return {"error": "Нет данных за указанный период"}
            
            # Анализ по категориям
            category_analysis = await self._analyze_by_categories(period_transactions)
            
            # Анализ по времени
            time_analysis = await self._analyze_by_time(period_transactions)
            
            # Выявление аномалий
            anomalies = await self._detect_anomalies(period_transactions)
            
            # Расчет статистик
            stats = await self._calculate_spending_stats(period_transactions)
            
            result = {
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "days": period_days
                },
                "total_transactions": len(period_transactions),
                "total_spent": abs(sum(t["amount"] for t in period_transactions)),
                "category_analysis": category_analysis,
                "time_analysis": time_analysis,
                "anomalies": anomalies,
                "statistics": stats,
                "insights": await self._generate_spending_insights(category_analysis, stats)
            }
            
            logger.info("Анализ трендов завершен")
            return result
            
        except Exception as e:
            logger.error(f"Ошибка анализа трендов: {e}")
            return {"error": str(e)}
    
    async def _analyze_by_categories(self, transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Анализ расходов по категориям"""
        category_totals = {}
        category_counts = {}
        
        for transaction in transactions:
            category = transaction.get("category", "Другое")
            amount = abs(transaction["amount"])
            
            category_totals[category] = category_totals.get(category, 0) + amount
            category_counts[category] = category_counts.get(category, 0) + 1
        
        # Сортируем по сумме
        sorted_categories = sorted(category_totals.items(), key=lambda x: x[1], reverse=True)
        
        total_spent = sum(category_totals.values())
        
        return {
            "by_amount": sorted_categories,
            "by_count": sorted(category_counts.items(), key=lambda x: x[1], reverse=True),
            "total_spent": total_spent,
            "category_percentages": {
                category: (amount / total_spent * 100) if total_spent > 0 else 0
                for category, amount in category_totals.items()
            }
        }
    
    async def _analyze_by_time(self, transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Анализ расходов по времени"""
        daily_totals = {}
        weekly_totals = {}
        
        for transaction in transactions:
            trans_date = self._parse_date(transaction.get("transaction_date", ""))
            if not trans_date:
                continue
                
            amount = abs(transaction["amount"])
            
            # По дням
            day_key = trans_date.isoformat()
            daily_totals[day_key] = daily_totals.get(day_key, 0) + amount
            
            # По неделям
            week_start = trans_date - timedelta(days=trans_date.weekday())
            week_key = week_start.isoformat()
            weekly_totals[week_key] = weekly_totals.get(week_key, 0) + amount
        
        return {
            "daily": daily_totals,
            "weekly": weekly_totals,
            "average_daily": statistics.mean(daily_totals.values()) if daily_totals else 0,
            "average_weekly": statistics.mean(weekly_totals.values()) if weekly_totals else 0
        }
    
    async def _detect_anomalies(self, transactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Выявление аномальных транзакций"""
        anomalies = []
        
        if not transactions:
            return anomalies
        
        amounts = [abs(t["amount"]) for t in transactions]
        mean_amount = statistics.mean(amounts)
        std_amount = statistics.stdev(amounts) if len(amounts) > 1 else 0
        
        # Аномалии по сумме (больше 2 стандартных отклонений)
        threshold = mean_amount + 2 * std_amount
        
        for transaction in transactions:
            amount = abs(transaction["amount"])
            if amount > threshold:
                anomalies.append({
                    "type": "high_amount",
                    "transaction": transaction,
                    "amount": amount,
                    "threshold": threshold,
                    "severity": "high" if amount > mean_amount + 3 * std_amount else "medium"
                })
        
        return anomalies
    
    async def _calculate_spending_stats(self, transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Расчет статистик расходов"""
        amounts = [abs(t["amount"]) for t in transactions]
        
        if not amounts:
            return {}
        
        return {
            "mean": statistics.mean(amounts),
            "median": statistics.median(amounts),
            "std_dev": statistics.stdev(amounts) if len(amounts) > 1 else 0,
            "min": min(amounts),
            "max": max(amounts),
            "total": sum(amounts)
        }
    
    async def _generate_spending_insights(self, category_analysis: Dict, stats: Dict) -> List[str]:
        """Генерация инсайтов по расходам"""
        insights = []
        
        # Анализ топ категории
        if category_analysis.get("by_amount"):
            top_category, top_amount = category_analysis["by_amount"][0]
            top_percentage = category_analysis["category_percentages"].get(top_category, 0)
            
            if top_percentage > 40:
                insights.append(f"💡 Основная статья расходов: {top_category} ({top_percentage:.1f}%)")
        
        # Анализ диверсификации
        category_count = len(category_analysis.get("by_amount", []))
        if category_count < 3:
            insights.append("⚠️ Низкая диверсификация расходов. Рассмотрите больше категорий.")
        
        # Анализ среднего чека
        mean_amount = stats.get("mean", 0)
        if mean_amount > 100:
            insights.append(f"📊 Высокий средний чек: ${mean_amount:.2f}")
        elif mean_amount < 20:
            insights.append(f"📊 Низкий средний чек: ${mean_amount:.2f}")
        
        return insights
    
    async def analyze_income_trends(self, transactions: List[Dict[str, Any]], 
                                  period_days: int = 30) -> Dict[str, Any]:
        """
        Анализ трендов доходов
        
        Args:
            transactions: Список транзакций
            period_days: Период анализа в днях
            
        Returns:
            Dict: Анализ доходов
        """
        try:
            logger.info(f"Анализ трендов доходов за {period_days} дней...")
            
            # Фильтруем доходы за период
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=period_days)
            
            income_transactions = [
                t for t in transactions
                if t.get("amount", 0) > 0 and 
                self._parse_date(t.get("transaction_date", "")) >= start_date
            ]
            
            if not income_transactions:
                return {"error": "Нет данных о доходах за указанный период"}
            
            # Анализ источников дохода
            source_analysis = {}
            for transaction in income_transactions:
                source = transaction.get("description", "Unknown")
                amount = transaction["amount"]
                source_analysis[source] = source_analysis.get(source, 0) + amount
            
            # Статистики
            amounts = [t["amount"] for t in income_transactions]
            stats = {
                "total_income": sum(amounts),
                "mean_income": statistics.mean(amounts),
                "income_count": len(amounts),
                "sources": len(source_analysis)
            }
            
            result = {
                "period": {
                    "start_date": start_date.isoformat(),
                    "end_date": end_date.isoformat(),
                    "days": period_days
                },
                "statistics": stats,
                "sources": source_analysis,
                "insights": await self._generate_income_insights(stats, source_analysis)
            }
            
            logger.info("Анализ доходов завершен")
            return result
            
        except Exception as e:
            logger.error(f"Ошибка анализа доходов: {e}")
            return {"error": str(e)}
    
    async def _generate_income_insights(self, stats: Dict, sources: Dict) -> List[str]:
        """Генерация инсайтов по доходам"""
        insights = []
        
        # Анализ диверсификации источников
        source_count = stats.get("sources", 0)
        if source_count == 1:
            insights.append("⚠️ Единственный источник дохода. Рассмотрите диверсификацию.")
        elif source_count > 3:
            insights.append("✅ Хорошая диверсификация источников дохода")
        
        # Анализ стабильности
        total_income = stats.get("total_income", 0)
        if total_income > 0:
            insights.append(f"💰 Общий доход за период: ${total_income:.2f}")
        
        return insights
    
    def _parse_date(self, date_str: str) -> Optional[date]:
        """Парсинг даты из строки"""
        try:
            if isinstance(date_str, str):
                return datetime.fromisoformat(date_str).date()
            elif isinstance(date_str, date):
                return date_str
            return None
        except:
            return None
    
    async def get_financial_health_score(self, financial_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Расчет общего балла финансового здоровья
        
        Args:
            financial_data: Финансовые данные
            
        Returns:
            Dict: Балл и рекомендации
        """
        try:
            score = 0
            max_score = 100
            factors = []
            
            # Анализ соотношения доходов и расходов
            income = financial_data.get("total_income", 0)
            expenses = financial_data.get("total_expenses", 0)
            
            if income > 0:
                expense_ratio = expenses / income
                if expense_ratio < 0.5:
                    score += 30
                    factors.append("Отличное соотношение доходов и расходов")
                elif expense_ratio < 0.7:
                    score += 20
                    factors.append("Хорошее соотношение доходов и расходов")
                elif expense_ratio < 0.9:
                    score += 10
                    factors.append("Приемлемое соотношение доходов и расходов")
                else:
                    factors.append("Высокий уровень расходов")
            
            # Анализ сбережений
            savings = income - expenses
            if savings > 0:
                savings_ratio = savings / income
                if savings_ratio > 0.2:
                    score += 25
                    factors.append("Отличный уровень сбережений")
                elif savings_ratio > 0.1:
                    score += 15
                    factors.append("Хороший уровень сбережений")
                else:
                    factors.append("Низкий уровень сбережений")
            
            # Анализ диверсификации
            category_count = len(financial_data.get("categories", []))
            if category_count > 5:
                score += 15
                factors.append("Хорошая диверсификация расходов")
            elif category_count > 3:
                score += 10
                factors.append("Умеренная диверсификация расходов")
            
            # Анализ стабильности
            if financial_data.get("income_stability") == "stable":
                score += 20
                factors.append("Стабильные доходы")
            
            # Анализ инвестиций
            investments = financial_data.get("total_investments", 0)
            if investments > 0:
                score += 10
                factors.append("Наличие инвестиций")
            
            return {
                "score": min(score, max_score),
                "max_score": max_score,
                "grade": self._get_grade(score),
                "factors": factors,
                "recommendations": await self._get_recommendations(score, factors)
            }
            
        except Exception as e:
            logger.error(f"Ошибка расчета балла: {e}")
            return {"error": str(e)}
    
    def _get_grade(self, score: int) -> str:
        """Получение буквенной оценки"""
        if score >= 90:
            return "A+"
        elif score >= 80:
            return "A"
        elif score >= 70:
            return "B+"
        elif score >= 60:
            return "B"
        elif score >= 50:
            return "C"
        else:
            return "D"
    
    async def _get_recommendations(self, score: int, factors: List[str]) -> List[str]:
        """Генерация рекомендаций на основе балла"""
        recommendations = []
        
        if score < 50:
            recommendations.append("🚨 Критический уровень. Необходимо срочно пересмотреть финансовую стратегию")
        elif score < 70:
            recommendations.append("⚠️ Требуются улучшения в управлении финансами")
        elif score < 85:
            recommendations.append("✅ Хорошее финансовое состояние с возможностями для улучшения")
        else:
            recommendations.append("🎉 Отличное финансовое состояние!")
        
        return recommendations


