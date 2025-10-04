"""
AI система для автоматической категоризации транзакций
Использует машинное обучение и правила для определения категорий
"""

from typing import List, Dict, Any, Optional, Tuple
import re
import logging
from datetime import datetime

logger = logging.getLogger(__name__)


class TransactionCategorizer:
    """
    Система автоматической категоризации транзакций
    
    Использует:
    - Правила на основе ключевых слов
    - Машинное обучение (в будущем)
    - Обучение на пользовательских данных
    """
    
    def __init__(self):
        """Инициализация категоризатора"""
        self.categories = {
            "Продукты": {
                "keywords": ["grocery", "supermarket", "food", "restaurant", "cafe", "tim hortons", "mcdonald", "starbucks"],
                "patterns": [r".*grocery.*", r".*supermarket.*", r".*food.*", r".*restaurant.*"]
            },
            "Транспорт": {
                "keywords": ["uber", "lyft", "taxi", "gas", "fuel", "parking", "metro", "bus", "train"],
                "patterns": [r".*uber.*", r".*lyft.*", r".*gas.*", r".*fuel.*"]
            },
            "Развлечения": {
                "keywords": ["netflix", "spotify", "movie", "cinema", "theater", "game", "entertainment"],
                "patterns": [r".*netflix.*", r".*spotify.*", r".*movie.*", r".*cinema.*"]
            },
            "Здоровье": {
                "keywords": ["pharmacy", "doctor", "hospital", "medical", "health", "drugstore"],
                "patterns": [r".*pharmacy.*", r".*medical.*", r".*health.*"]
            },
            "Образование": {
                "keywords": ["university", "college", "school", "course", "education", "book", "library"],
                "patterns": [r".*university.*", r".*college.*", r".*school.*"]
            },
            "Покупки": {
                "keywords": ["amazon", "shop", "store", "mall", "retail", "purchase", "buy"],
                "patterns": [r".*amazon.*", r".*shop.*", r".*store.*"]
            },
            "Доходы": {
                "keywords": ["salary", "wage", "income", "deposit", "refund", "bonus"],
                "patterns": [r".*salary.*", r".*wage.*", r".*deposit.*"]
            },
            "Инвестиции": {
                "keywords": ["investment", "stock", "bond", "dividend", "trading", "broker"],
                "patterns": [r".*investment.*", r".*stock.*", r".*dividend.*"]
            },
            "Коммунальные услуги": {
                "keywords": ["electric", "water", "gas", "utility", "internet", "phone", "cable"],
                "patterns": [r".*electric.*", r".*water.*", r".*utility.*"]
            },
            "Другое": {
                "keywords": [],
                "patterns": []
            }
        }
        
        self.user_preferences = {}  # Пользовательские предпочтения
        self.learning_data = []     # Данные для обучения
    
    async def categorize_transaction(self, transaction: Dict[str, Any]) -> str:
        """
        Категоризация одной транзакции
        
        Args:
            transaction: Данные транзакции
            
        Returns:
            str: Определенная категория
        """
        try:
            description = transaction.get("description", "").lower()
            amount = transaction.get("amount", 0)
            
            # Если транзакция положительная, скорее всего это доход
            if amount > 0:
                return "Доходы"
            
            # Поиск по ключевым словам
            category = await self._find_category_by_keywords(description)
            if category:
                return category
            
            # Поиск по паттернам
            category = await self._find_category_by_patterns(description)
            if category:
                return category
            
            # Если ничего не найдено, возвращаем "Другое"
            return "Другое"
            
        except Exception as e:
            logger.error(f"Ошибка категоризации транзакции: {e}")
            return "Другое"
    
    async def _find_category_by_keywords(self, description: str) -> Optional[str]:
        """Поиск категории по ключевым словам"""
        for category, data in self.categories.items():
            keywords = data.get("keywords", [])
            for keyword in keywords:
                if keyword.lower() in description:
                    return category
        return None
    
    async def _find_category_by_patterns(self, description: str) -> Optional[str]:
        """Поиск категории по регулярным выражениям"""
        for category, data in self.categories.items():
            patterns = data.get("patterns", [])
            for pattern in patterns:
                if re.search(pattern, description, re.IGNORECASE):
                    return category
        return None
    
    async def categorize_batch(self, transactions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Категоризация списка транзакций
        
        Args:
            transactions: Список транзакций
            
        Returns:
            List[Dict]: Транзакции с добавленными категориями
        """
        try:
            categorized_transactions = []
            
            for transaction in transactions:
                # Если категория уже есть, оставляем как есть
                if transaction.get("category"):
                    categorized_transactions.append(transaction)
                    continue
                
                # Определяем категорию
                category = await self.categorize_transaction(transaction)
                transaction["category"] = category
                transaction["category_confidence"] = await self._calculate_confidence(transaction, category)
                
                categorized_transactions.append(transaction)
            
            logger.info(f"Категоризировано {len(transactions)} транзакций")
            return categorized_transactions
            
        except Exception as e:
            logger.error(f"Ошибка пакетной категоризации: {e}")
            return transactions
    
    async def _calculate_confidence(self, transaction: Dict[str, Any], category: str) -> float:
        """
        Расчет уверенности в категоризации
        
        Args:
            transaction: Транзакция
            category: Определенная категория
            
        Returns:
            float: Уверенность от 0 до 1
        """
        description = transaction.get("description", "").lower()
        amount = transaction.get("amount", 0)
        
        confidence = 0.5  # Базовая уверенность
        
        # Бонус за точное совпадение ключевых слов
        if category in self.categories:
            keywords = self.categories[category].get("keywords", [])
            for keyword in keywords:
                if keyword.lower() in description:
                    confidence += 0.2
                    break
        
        # Бонус за паттерны
        if category in self.categories:
            patterns = self.categories[category].get("patterns", [])
            for pattern in patterns:
                if re.search(pattern, description, re.IGNORECASE):
                    confidence += 0.3
                    break
        
        # Бонус за логику (доходы для положительных сумм)
        if category == "Доходы" and amount > 0:
            confidence += 0.4
        elif category != "Доходы" and amount < 0:
            confidence += 0.1
        
        return min(1.0, confidence)
    
    async def learn_from_user_feedback(self, transaction_id: str, correct_category: str) -> None:
        """
        Обучение на основе пользовательской обратной связи
        
        Args:
            transaction_id: ID транзакции
            correct_category: Правильная категория
        """
        try:
            # Сохраняем данные для обучения
            learning_entry = {
                "transaction_id": transaction_id,
                "correct_category": correct_category,
                "timestamp": datetime.now().isoformat()
            }
            
            self.learning_data.append(learning_entry)
            
            # Здесь можно добавить логику машинного обучения
            # Пока что просто сохраняем данные
            
            logger.info(f"Сохранена обратная связь для транзакции {transaction_id}: {correct_category}")
            
        except Exception as e:
            logger.error(f"Ошибка обучения: {e}")
    
    async def get_category_statistics(self) -> Dict[str, Any]:
        """
        Получение статистики по категориям
        
        Returns:
            Dict: Статистика категоризации
        """
        try:
            total_transactions = len(self.learning_data)
            category_counts = {}
            
            for entry in self.learning_data:
                category = entry["correct_category"]
                category_counts[category] = category_counts.get(category, 0) + 1
            
            return {
                "total_learned": total_transactions,
                "category_distribution": category_counts,
                "available_categories": list(self.categories.keys())
            }
            
        except Exception as e:
            logger.error(f"Ошибка получения статистики: {e}")
            return {}
    
    def add_custom_category(self, category_name: str, keywords: List[str], patterns: List[str]) -> None:
        """
        Добавление пользовательской категории
        
        Args:
            category_name: Название категории
            keywords: Ключевые слова
            patterns: Регулярные выражения
        """
        try:
            self.categories[category_name] = {
                "keywords": keywords,
                "patterns": patterns
            }
            
            logger.info(f"Добавлена пользовательская категория: {category_name}")
            
        except Exception as e:
            logger.error(f"Ошибка добавления категории: {e}")
    
    def get_available_categories(self) -> List[str]:
        """Получение списка доступных категорий"""
        return list(self.categories.keys())


