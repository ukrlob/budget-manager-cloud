"""
Модели для работы с банками
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class BankBase(BaseModel):
    """Базовая модель банка"""
    name: str = Field(..., description="Название банка")
    country: str = Field(..., description="Страна банка")
    currency: str = Field(..., description="Основная валюта банка")


class BankCreate(BankBase):
    """Модель для создания банка"""
    pass


class BankUpdate(BaseModel):
    """Модель для обновления банка"""
    name: Optional[str] = None
    country: Optional[str] = None
    currency: Optional[str] = None


class Bank(BankBase):
    """Полная модель банка"""
    id: int = Field(..., description="ID банка")
    created_at: datetime = Field(..., description="Дата создания")
    
    class Config:
        from_attributes = True


class BankWithAccounts(Bank):
    """Банк с информацией о счетах"""
    accounts_count: int = Field(0, description="Количество счетов")
    total_balance: float = Field(0.0, description="Общий баланс по всем счетам")


