"""
Гибридная стратегия банковских интеграций
Комбинирует Plaid, Selenium и API для максимального покрытия
"""

from typing import List, Dict, Any, Optional
import asyncio
import logging
from datetime import datetime
from .plaid_integration import PlaidBankConnector
from .rbc import RBCBank
from .bmo import BMOBank
from .interactive_brokers import InteractiveBrokers
from .base import BankConnector

logger = logging.getLogger(__name__)


class HybridBankStrategy:
    """
    Умная стратегия выбора метода интеграции с банками
    """
    
    def __init__(self):
        self.connectors = {}
        self.bank_mapping = {
            # Банки с поддержкой Plaid
            'rbc': {'method': 'plaid', 'institution_id': 'ins_1'},
            'bmo': {'method': 'plaid', 'institution_id': 'ins_2'},
            'td': {'method': 'plaid', 'institution_id': 'ins_3'},
            'scotiabank': {'method': 'plaid', 'institution_id': 'ins_4'},
            'cibc': {'method': 'plaid', 'institution_id': 'ins_5'},
            
            # Банки с Selenium
            'rbc_selenium': {'method': 'selenium', 'connector': RBCBank},
            'bmo_selenium': {'method': 'selenium', 'connector': BMOBank},
            'privatbank': {'method': 'selenium', 'connector': None},  # Нужно создать
            'revolut': {'method': 'selenium', 'connector': None},     # Нужно создать
            
            # Банки с API
            'interactive_brokers': {'method': 'api', 'connector': InteractiveBrokers},
            'questrade': {'method': 'api', 'connector': None},        # Нужно создать
            'wealthsimple': {'method': 'api', 'connector': None},     # Нужно создать
        }
        
        # Статистика использования методов
        self.usage_stats = {
            'plaid': {'requests': 0, 'success_rate': 0.0, 'avg_response_time': 0.0},
            'selenium': {'requests': 0, 'success_rate': 0.0, 'avg_response_time': 0.0},
            'api': {'requests': 0, 'success_rate': 0.0, 'avg_response_time': 0.0}
        }
    
    async def get_bank_connector(self, bank_name: str, credentials: Dict[str, Any]) -> BankConnector:
        """
        Получение оптимального коннектора для банка
        """
        try:
            # Определяем метод интеграции
            bank_config = self.bank_mapping.get(bank_name.lower())
            if not bank_config:
                raise ValueError(f"Банк {bank_name} не поддерживается")
            
            method = bank_config['method']
            
            # Создаем коннектор в зависимости от метода
            if method == 'plaid':
                return await self._create_plaid_connector(bank_config, credentials)
            elif method == 'selenium':
                return await self._create_selenium_connector(bank_config, credentials)
            elif method == 'api':
                return await self._create_api_connector(bank_config, credentials)
            else:
                raise ValueError(f"Неизвестный метод интеграции: {method}")
                
        except Exception as e:
            logger.error(f"Ошибка создания коннектора для {bank_name}: {e}")
            raise
    
    async def _create_plaid_connector(self, bank_config: Dict, credentials: Dict) -> PlaidBankConnector:
        """
        Создание Plaid коннектора
        """
        plaid_credentials = {
            'client_id': credentials.get('plaid_client_id'),
            'secret': credentials.get('plaid_secret'),
            'environment': credentials.get('plaid_environment', 'sandbox'),
            'access_token': credentials.get('access_token')
        }
        
        connector = PlaidBankConnector(plaid_credentials)
        await connector.connect()
        
        # Обновляем статистику
        self.usage_stats['plaid']['requests'] += 1
        
        return connector
    
    async def _create_selenium_connector(self, bank_config: Dict, credentials: Dict) -> BankConnector:
        """
        Создание Selenium коннектора
        """
        connector_class = bank_config['connector']
        if not connector_class:
            raise ValueError("Selenium коннектор не реализован для этого банка")
        
        connector = connector_class(credentials)
        await connector.connect()
        
        # Обновляем статистику
        self.usage_stats['selenium']['requests'] += 1
        
        return connector
    
    async def _create_api_connector(self, bank_config: Dict, credentials: Dict) -> BankConnector:
        """
        Создание API коннектора
        """
        connector_class = bank_config['connector']
        if not connector_class:
            raise ValueError("API коннектор не реализован для этого банка")
        
        connector = connector_class(credentials)
        await connector.connect()
        
        # Обновляем статистику
        self.usage_stats['api']['requests'] += 1
        
        return connector
    
    async def get_optimal_method(self, bank_name: str) -> str:
        """
        Определение оптимального метода для банка
        """
        bank_config = self.bank_mapping.get(bank_name.lower())
        if not bank_config:
            return 'selenium'  # Fallback к Selenium
        
        method = bank_config['method']
        
        # Проверяем доступность Plaid
        if method == 'plaid':
            plaid_status = await self._check_plaid_availability()
            if not plaid_status['available']:
                logger.warning(f"Plaid недоступен для {bank_name}, переключаемся на Selenium")
                return 'selenium'
        
        return method
    
    async def _check_plaid_availability(self) -> Dict[str, Any]:
        """
        Проверка доступности Plaid
        """
        try:
            # Проверяем лимиты запросов
            plaid_connector = PlaidBankConnector({
                'client_id': 'test',
                'secret': 'test',
                'environment': 'sandbox'
            })
            
            rate_limit_status = await plaid_connector.get_rate_limit_status()
            
            return {
                'available': rate_limit_status['requests_remaining'] > 0,
                'rate_limit_status': rate_limit_status,
                'recommendation': 'plaid' if rate_limit_status['requests_remaining'] > 10 else 'selenium'
            }
            
        except Exception as e:
            logger.error(f"Ошибка проверки Plaid: {e}")
            return {
                'available': False,
                'error': str(e),
                'recommendation': 'selenium'
            }
    
    async def get_bank_coverage(self) -> Dict[str, Any]:
        """
        Получение информации о покрытии банков
        """
        coverage = {
            'plaid': {
                'banks': ['RBC', 'BMO', 'TD', 'Scotiabank', 'CIBC'],
                'coverage_percentage': 40,
                'reliability': 'high',
                'cost': 'low'
            },
            'selenium': {
                'banks': ['RBC', 'BMO', 'PrivatBank', 'Revolut', 'Any Bank'],
                'coverage_percentage': 90,
                'reliability': 'medium',
                'cost': 'free'
            },
            'api': {
                'banks': ['Interactive Brokers', 'Questrade', 'Wealthsimple'],
                'coverage_percentage': 20,
                'reliability': 'high',
                'cost': 'varies'
            }
        }
        
        return coverage
    
    async def optimize_for_region(self, region: str) -> Dict[str, Any]:
        """
        Оптимизация стратегии для региона
        """
        regional_strategies = {
            'canada': {
                'primary': 'plaid',
                'fallback': 'selenium',
                'recommended_banks': ['RBC', 'BMO', 'TD', 'Scotiabank'],
                'plaid_coverage': 80
            },
            'usa': {
                'primary': 'plaid',
                'fallback': 'selenium',
                'recommended_banks': ['Chase', 'Bank of America', 'Wells Fargo'],
                'plaid_coverage': 95
            },
            'europe': {
                'primary': 'selenium',
                'fallback': 'api',
                'recommended_banks': ['Revolut', 'N26', 'Monzo'],
                'plaid_coverage': 10
            },
            'ukraine': {
                'primary': 'selenium',
                'fallback': 'api',
                'recommended_banks': ['PrivatBank', 'Monobank', 'Oschadbank'],
                'plaid_coverage': 0
            }
        }
        
        return regional_strategies.get(region, regional_strategies['canada'])
    
    async def get_cost_analysis(self) -> Dict[str, Any]:
        """
        Анализ стоимости интеграций
        """
        costs = {
            'plaid': {
                'free_requests': 100,
                'cost_per_request': 0.50,
                'monthly_cost_estimate': 0,  # Если не превышаем лимит
                'scalability': 'high'
            },
            'selenium': {
                'free_requests': 'unlimited',
                'cost_per_request': 0,
                'monthly_cost_estimate': 0,
                'scalability': 'medium'
            },
            'api': {
                'free_requests': 'varies',
                'cost_per_request': 'varies',
                'monthly_cost_estimate': 'varies',
                'scalability': 'high'
            }
        }
        
        return costs
    
    async def get_recommendations(self) -> List[str]:
        """
        Получение рекомендаций по оптимизации
        """
        recommendations = []
        
        # Анализ использования Plaid
        plaid_stats = self.usage_stats['plaid']
        if plaid_stats['requests'] > 80:
            recommendations.append("Приближаетесь к лимиту Plaid - рассмотрите переход на Selenium")
        
        # Анализ надежности Selenium
        selenium_stats = self.usage_stats['selenium']
        if selenium_stats['success_rate'] < 0.8:
            recommendations.append("Низкая надежность Selenium - проверьте стабильность подключений")
        
        # Общие рекомендации
        recommendations.extend([
            "Используйте Plaid для основных канадских банков",
            "Используйте Selenium для банков, не поддерживаемых Plaid",
            "Реализуйте кэширование для снижения количества запросов",
            "Настройте webhooks для обновлений в реальном времени"
        ])
        
        return recommendations
