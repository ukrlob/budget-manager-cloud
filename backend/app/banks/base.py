"""
Базовый класс для всех банковских интеграций
Обеспечивает единый интерфейс для работы с разными банками
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime, date
import logging

logger = logging.getLogger(__name__)


class BankConnector(ABC):
    """
    Абстрактный базовый класс для всех банковских интеграций
    
    Каждый банк должен наследовать этот класс и реализовать:
    - connect() - подключение к банку
    - get_accounts() - получение списка счетов
    - get_transactions() - получение транзакций
    - get_balance() - получение баланса
    """
    
    def __init__(self, bank_name: str, credentials: Dict[str, Any]):
        """
        Инициализация банковского коннектора
        
        Args:
            bank_name: Название банка
            credentials: Учетные данные для подключения
        """
        self.bank_name = bank_name
        self.credentials = credentials
        self.is_connected = False
        self.connection = None
        
    @abstractmethod
    async def connect(self) -> bool:
        """
        Подключение к банку
        
        Returns:
            bool: True если подключение успешно
        """
        pass
    
    @abstractmethod
    async def get_accounts(self) -> List[Dict[str, Any]]:
        """
        Получение списка счетов
        
        Returns:
            List[Dict]: Список счетов с информацией
        """
        pass
    
    @abstractmethod
    async def get_transactions(self, account_id: str, 
                             start_date: Optional[date] = None,
                             end_date: Optional[date] = None) -> List[Dict[str, Any]]:
        """
        Получение транзакций по счету
        
        Args:
            account_id: ID счета
            start_date: Начальная дата (опционально)
            end_date: Конечная дата (опционально)
            
        Returns:
            List[Dict]: Список транзакций
        """
        pass
    
    @abstractmethod
    async def get_balance(self, account_id: str) -> float:
        """
        Получение баланса счета
        
        Args:
            account_id: ID счета
            
        Returns:
            float: Текущий баланс
        """
        pass
    
    async def disconnect(self) -> None:
        """
        Отключение от банка
        """
        if self.connection:
            try:
                await self.connection.close()
            except Exception as e:
                logger.error(f"Ошибка при отключении от {self.bank_name}: {e}")
            finally:
                self.connection = None
                self.is_connected = False
    
    def __str__(self) -> str:
        return f"{self.bank_name}Connector(connected={self.is_connected})"
    
    def __repr__(self) -> str:
        return self.__str__()


class BankError(Exception):
    """Исключение для ошибок банковских операций"""
    pass


class ConnectionError(BankError):
    """Ошибка подключения к банку"""
    pass


class AuthenticationError(BankError):
    """Ошибка аутентификации"""
    pass


class DataError(BankError):
    """Ошибка получения данных"""
    pass


