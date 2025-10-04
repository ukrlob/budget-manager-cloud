"""
Модели для работы с транзакциями
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime, date


class TransactionBase(BaseModel):
    """Базовая модель транзакции"""
    account_id: int = Field(..., description="ID счета")
    amount: float = Field(..., description="Сумма транзакции")
    description: Optional[str] = Field(None, description="Описание транзакции")
    category: Optional[str] = Field(None, description="Категория транзакции")
    transaction_date: date = Field(..., description="Дата транзакции")


class TransactionCreate(TransactionBase):
    """Модель для создания транзакции"""
    pass


class TransactionUpdate(BaseModel):
    """Модель для обновления транзакции"""
    amount: Optional[float] = None
    description: Optional[str] = None
    category: Optional[str] = None
    transaction_date: Optional[date] = None


class Transaction(TransactionBase):
    """Полная модель транзакции"""
    id: int = Field(..., description="ID транзакции")
    created_at: datetime = Field(..., description="Дата создания записи")
    
    class Config:
        from_attributes = True


class TransactionWithAccount(Transaction):
    """Транзакция с информацией о счете"""
    account_name: str = Field(..., description="Название счета")
    bank_name: str = Field(..., description="Название банка")
    currency: str = Field(..., description="Валюта счета")


class TransactionWithCategory(TransactionWithAccount):
    """Транзакция с детальной информацией о категории"""
    category_confidence: Optional[float] = Field(None, description="Уверенность в категоризации")
    is_ai_categorized: bool = Field(False, description="Категоризирована ли AI")


class TransactionSummary(BaseModel):
    """Сводка по транзакциям"""
    total_count: int = Field(..., description="Общее количество транзакций")
    total_amount: float = Field(..., description="Общая сумма")
    income_amount: float = Field(..., description="Сумма доходов")
    expense_amount: float = Field(..., description="Сумма расходов")
    average_amount: float = Field(..., description="Средняя сумма транзакции")
    most_common_category: Optional[str] = Field(None, description="Самая частая категория")


class CategoryStats(BaseModel):
    """Статистика по категориям"""
    category: str = Field(..., description="Название категории")
    count: int = Field(..., description="Количество транзакций")
    total_amount: float = Field(..., description="Общая сумма")
    average_amount: float = Field(..., description="Средняя сумма")
    percentage: float = Field(..., description="Процент от общих расходов")


