"""
Модели для работы со счетами
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class AccountBase(BaseModel):
    """Базовая модель счета"""
    bank_id: int = Field(..., description="ID банка")
    account_name: str = Field(..., description="Название счета")
    account_number: Optional[str] = Field(None, description="Номер счета")
    balance: float = Field(0.0, description="Текущий баланс")
    currency: str = Field(..., description="Валюта счета")


class AccountCreate(AccountBase):
    """Модель для создания счета"""
    pass


class AccountUpdate(BaseModel):
    """Модель для обновления счета"""
    account_name: Optional[str] = None
    account_number: Optional[str] = None
    balance: Optional[float] = None
    currency: Optional[str] = None
    is_active: Optional[bool] = None


class Account(AccountBase):
    """Полная модель счета"""
    id: int = Field(..., description="ID счета")
    is_active: bool = Field(True, description="Активен ли счет")
    created_at: datetime = Field(..., description="Дата создания")
    
    class Config:
        from_attributes = True


class AccountWithBank(Account):
    """Счет с информацией о банке"""
    bank_name: str = Field(..., description="Название банка")
    bank_country: str = Field(..., description="Страна банка")


class AccountWithTransactions(AccountWithBank):
    """Счет с информацией о транзакциях"""
    transactions_count: int = Field(0, description="Количество транзакций")
    last_transaction_date: Optional[datetime] = Field(None, description="Дата последней транзакции")


