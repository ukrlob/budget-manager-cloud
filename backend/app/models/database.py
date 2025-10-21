"""
Модель для работы с базой данных
Централизованное управление подключениями и операциями
"""

import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import asynccontextmanager
from typing import Optional, Dict, Any
import logging
import os
from dotenv import load_dotenv

# --- Environment and DB Initialization ---
# Load .env file at the top-level of the module.
# This is the single source of truth for configuration.
dotenv_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', '.env')
if os.path.exists(dotenv_path):
    load_dotenv(dotenv_path=dotenv_path)
    logging.info(f".env file found at {dotenv_path} and loaded.")
else:
    # CRITICAL: If .env file is missing, we must not proceed with a fallback.
    # This prevents silent failures with wrong credentials.
    logging.error(f"FATAL: .env file not found at path: {dotenv_path}. Application cannot start.")
    raise FileNotFoundError(f".env file not found at path: {dotenv_path}")

DB_URL_FROM_ENV = os.getenv("DATABASE_URL")
if not DB_URL_FROM_ENV:
    logging.error("FATAL: DATABASE_URL not found in the loaded .env file. Application cannot start.")
    raise ValueError("DATABASE_URL not found in the loaded .env file.")
# --- End of Initialization ---

logger = logging.getLogger(__name__)


class Database:
    """
    Класс для управления подключениями к базе данных
    
    Обеспечивает:
    - Пул подключений
    - Автоматическое управление транзакциями
    - Обработку ошибок
    - Логирование операций
    """
    
    def __init__(self, connection_string: str):
        """
        Инициализация подключения к базе данных
        
        Args:
            connection_string: Строка подключения (обязательно)
        """
        if not connection_string:
            raise ValueError("Connection string cannot be None or empty.")
        self.connection_string = connection_string
        logging.info(f"Database class initialized to use the provided connection string.")
        self._connection_pool = []
        self._max_connections = 10
        
    def _get_connection_string(self) -> str:
        # This method is no longer needed as connection string is passed directly.
        # Kept for compatibility in case it's called somewhere else, but it should not be.
        return self.connection_string
    
    @asynccontextmanager
    async def get_connection(self):
        """
        Контекстный менеджер для получения подключения
        
        Usage:
            async with db.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM users")
                result = cursor.fetchall()
        """
        connection = None
        try:
            # Получаем подключение из пула или создаем новое
            if self._connection_pool:
                connection = self._connection_pool.pop()
            else:
                if isinstance(self.connection_string, dict):
                    connection = psycopg2.connect(
                        cursor_factory=RealDictCursor,
                        **self.connection_string
                    )
                else:
                    connection = psycopg2.connect(
                        self.connection_string,
                        cursor_factory=RealDictCursor
                    )
            
            logger.debug("Получено подключение к базе данных")
            yield connection
            
        except Exception as e:
            logger.error(f"Ошибка работы с базой данных: {e}")
            if connection:
                connection.rollback()
            raise
        finally:
            # Возвращаем подключение в пул или закрываем
            if connection:
                try:
                    if not connection.closed:
                        if len(self._connection_pool) < self._max_connections:
                            self._connection_pool.append(connection)
                        else:
                            connection.close()
                except Exception as e:
                    logger.error(f"Ошибка при возврате подключения в пул: {e}")
                    try:
                        connection.close()
                    except:
                        pass
    
    async def execute_query(self, query: str, params: Optional[Dict] = None) -> list:
        """
        Выполнение SELECT запроса, а также INSERT/UPDATE с возвратом данных (RETURNING)
        
        Args:
            query: SQL запрос
            params: Параметры запроса в виде словаря
            
        Returns:
            list: Результаты запроса
        """
        async with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                logger.debug(f"Executing query: {query} with params: {params}")
                cursor.execute(query, params)
                
                # Если это изменяющий запрос, коммитим его
                if query.strip().upper().startswith(('INSERT', 'UPDATE', 'DELETE')):
                    conn.commit()
                    logger.info(f"Query committed successfully. Row count: {cursor.rowcount}")

                # Если есть что возвращать (RETURNING), то возвращаем
                if cursor.description:
                    results = cursor.fetchall()
                    return [dict(row) for row in results]
                return []
            except Exception as e:
                logger.error(f"Error executing query: {query} - {e}")
                conn.rollback()
                raise
            finally:
                cursor.close()
    
    async def execute_insert(self, query: str, params: Optional[tuple] = None) -> int:
        """
        Выполнение INSERT запроса
        
        Args:
            query: SQL запрос
            params: Параметры запроса
            
        Returns:
            int: ID вставленной записи
        """
        async with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(query, params)
                conn.commit()
                return cursor.fetchone()[0] if cursor.description else 0
            except Exception as e:
                conn.rollback()
                raise
            finally:
                cursor.close()
    
    async def execute_update(self, query: str, params: Optional[tuple] = None) -> int:
        """
        Выполнение UPDATE запроса
        
        Args:
            query: SQL запрос
            params: Параметры запроса
            
        Returns:
            int: Количество обновленных записей
        """
        async with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(query, params)
                conn.commit()
                return cursor.rowcount
            except Exception as e:
                conn.rollback()
                raise
            finally:
                cursor.close()
    
    async def execute_delete(self, query: str, params: Optional[tuple] = None) -> int:
        """
        Выполнение DELETE запроса
        
        Args:
            query: SQL запрос
            params: Параметры запроса
            
        Returns:
            int: Количество удаленных записей
        """
        async with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(query, params)
                conn.commit()
                return cursor.rowcount
            except Exception as e:
                conn.rollback()
                raise
            finally:
                cursor.close()
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Проверка состояния базы данных
        
        Returns:
            Dict: Статус базы данных
        """
        try:
            async with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                cursor.fetchone()
                cursor.close()
                
                return {
                    "status": "healthy",
                    "database": "connected",
                    "pool_size": len(self._connection_pool)
                }
        except Exception as e:
            return {
                "status": "unhealthy",
                "database": "disconnected",
                "error": str(e)
            }
    
    async def close_all_connections(self):
        """Закрытие всех подключений"""
        for connection in self._connection_pool:
            try:
                if not connection.closed:
                    connection.close()
            except Exception as e:
                logger.error(f"Ошибка при закрытии подключения: {e}")
        
        self._connection_pool.clear()
        logger.info("Все подключения к базе данных закрыты")


# Глобальный экземпляр базы данных.
# This is now created with the guaranteed-to-be-loaded DB_URL_FROM_ENV.
db = Database(connection_string=DB_URL_FROM_ENV)


