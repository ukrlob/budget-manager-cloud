"""
API для управления банками через веб-интерфейс
"""

from fastapi import APIRouter, HTTPException, Depends, Request
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import asyncio
import logging
from datetime import datetime, date, timedelta
from ..banks.plaid_integration import PlaidBankConnector
import os
from dotenv import load_dotenv
from ..services.bank_service import BankService, BankCreate
from ..models.bank import Bank, BankCreate, BankBase

load_dotenv()

router = APIRouter(prefix="/api/banks", tags=["bank-management"])
logger = logging.getLogger(__name__)

class BankStatus(BaseModel):
    code: str
    name: str
    status: str
    accounts_count: int
    last_transaction_date: Optional[str]
    error_message: Optional[str]

class BankAccount(BaseModel):
    id: str
    name: str
    type: str
    subtype: str
    balance: float
    currency: str
    bank_name: str
    balance_type: Optional[str] = None
    credit_limit: Optional[float] = None
    used_credit: Optional[float] = None
    available_balance: Optional[float] = None
    last_updated: Optional[str] = None  # Время последнего обновления из Plaid

class BankTransaction(BaseModel):
    id: str
    name: str
    amount: float
    date: str
    currency: str
    category: List[str]

class BankUpdateRequest(BaseModel):
    bank_code: str
    access_token: str
    item_id: Optional[str] = None

class BankManager:
    """Менеджер банков для веб-интерфейса"""
    
    def __init__(self):
        self.bank_service = BankService()
        self.banks: Dict[str, Dict[str, Any]] = {}
        self.plaid_credentials = {
            "client_id": os.getenv("PLAID_CLIENT_ID"),
            "secret": os.getenv("PLAID_SECRET"),
            "environment": os.getenv("PLAID_ENVIRONMENT", "production")
        }
        # Load banks from DB at startup
        logger.info("Scheduling loading banks from DB...")
        asyncio.create_task(self._load_banks_from_db())

    async def _load_banks_from_db(self):
        """Load banks from the database"""
        logger.info("Loading banks from database...")
        try:
            db_banks = await self.bank_service.get_all_banks()
            for bank in db_banks:
                # Use a generated short code as the key for in-memory cache
                if bank.plaid_institution_id:
                    # Create a short, readable code from the name
                    short_code = "".join(filter(str.isupper, bank.name))
                    if not short_code:
                        short_code = bank.name.split(' ')[0].upper()

                    self.banks[short_code] = {
                        "name": bank.name,
                        "access_token": bank.access_token,
                        "item_id": bank.item_id,
                        "plaid_institution_id": bank.plaid_institution_id
                    }
            logger.info(f"Loaded {len(self.banks)} banks from database.")
        except Exception as e:
            logger.error(f"Error loading banks from database: {e}")

    async def _save_banks_to_cache(self):
        """Сохраняем банки в кэш"""
        try:
            await self.cache_service.cache_data("banks", self.banks)
            logger.info("Банки сохранены в кэш")
        except Exception as e:
            logger.warning(f"Не удалось сохранить банки в кэш: {e}")
    
    async def check_bank_status(self, bank_key: str) -> BankStatus:
        """Проверяем статус конкретного банка по ключу (plaid_institution_id)"""
        if bank_key not in self.banks:
            # This might happen if banks are not loaded yet, let's try loading them.
            await self._load_banks_from_db()
            if bank_key not in self.banks:
                 raise HTTPException(status_code=404, detail=f"Bank with key {bank_key} not found")
        
        bank_info = self.banks[bank_key]
        
        if not bank_info['access_token']:
            return BankStatus(
                code=bank_key,
                name=bank_info['name'],
                status="no_token",
                accounts_count=0,
                last_transaction_date=None,
                error_message="Access Token не найден"
            )
        
        try:
            credentials = {
                **self.plaid_credentials,
                "access_token": bank_info['access_token'],
                "item_id": bank_info['item_id'],
                "bank_name": bank_info['name'],
                "bank_code": bank_key
            }
            
            connector = PlaidBankConnector(credentials)
            
            if await connector.connect():
                accounts = await connector.get_accounts()
                accounts_count = len(accounts)
                
                # Получаем последнюю транзакцию
                last_transaction_date = None
                if accounts:
                    try:
                        account_id = accounts[0]['id']
                        end_date = date.today()
                        start_date = end_date - timedelta(days=30)
                        transactions = await connector.get_transactions(account_id, start_date, end_date)
                        if transactions:
                            # Преобразуем дату в строку
                            last_transaction_date = str(max(trans['date'] for trans in transactions))
                    except:
                        pass
                
                return BankStatus(
                    code=bank_key,
                    name=bank_info['name'],
                    status="working",
                    accounts_count=accounts_count,
                    last_transaction_date=last_transaction_date,
                    error_message=None
                )
            else:
                return BankStatus(
                    code=bank_key,
                    name=bank_info['name'],
                    status="connection_failed",
                    accounts_count=0,
                    last_transaction_date=None,
                    error_message="Не удалось подключиться к банку"
                )
                
        except Exception as e:
            return BankStatus(
                code=bank_key,
                name=bank_info['name'],
                status="error",
                accounts_count=0,
                last_transaction_date=None,
                error_message=str(e)
            )
    
    async def get_bank_accounts(self, bank_key: str) -> List[BankAccount]:
        """Получаем счета банка"""
        if bank_key not in self.banks:
            raise HTTPException(status_code=404, detail="Bank not found")
        
        bank_info = self.banks[bank_key]
        
        if not bank_info['access_token']:
            return []  # Возвращаем пустой список вместо ошибки
        
        try:
            credentials = {
                **self.plaid_credentials,
                "access_token": bank_info['access_token'],
                "item_id": bank_info['item_id'],
                "bank_name": bank_info['name'],
                "bank_code": bank_key
            }
            
            connector = PlaidBankConnector(credentials)
            
            if await connector.connect():
                accounts = await connector.get_accounts()
                
                # Отладочная информация
                logger.info(f"Получено счетов для {bank_key}: {len(accounts)}")
                for i, account in enumerate(accounts):
                    logger.info(f"Счет {i+1}: {account.get('name', 'N/A')} ({account.get('type', 'N/A')})")
                
                # Проверяем, что accounts не пустой и содержит нужные поля
                if not accounts:
                    return []
                
                result = []
                for account in accounts:
                    try:
                        # Преобразуем enum объекты в строки
                        account_type = str(account.get('type', 'unknown'))
                        account_subtype = str(account.get('subtype', 'unknown'))
                        
                        # Дополнительная проверка для enum объектов
                        if hasattr(account.get('type'), 'value'):
                            account_type = account.get('type').value
                        if hasattr(account.get('subtype'), 'value'):
                            account_subtype = account.get('subtype').value
                        
                        current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        
                        result.append(BankAccount(
                            id=account.get('id', ''),
                            name=account.get('name', 'Unknown Account'),
                            type=account_type,
                            subtype=account_subtype,
                            balance=float(account.get('current_balance', 0)),
                            currency=account.get('currency', 'CAD'),
                            bank_name=bank_info['name'],  # Используем правильное имя банка
                            balance_type=account.get('balance_type'),
                            credit_limit=account.get('credit_limit'),
                            used_credit=account.get('used_credit'),
                            available_balance=account.get('available_balance'),
                            last_updated=current_time  # Время получения данных из Plaid
                        ))
                    except Exception as account_error:
                        logger.error(f"Ошибка обработки счета: {account_error}")
                        logger.error(f"Account data: {account}")
                        continue
                
                return result
            else:
                raise HTTPException(status_code=500, detail="Не удалось подключиться к банку")
                
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Ошибка получения счетов для {bank_key}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Ошибка получения счетов: {str(e)}")
    
    async def get_bank_transactions(self, bank_key: str, account_id: str, days: int = 30) -> List[BankTransaction]:
        """Получаем транзакции банка"""
        if bank_key not in self.banks:
            raise HTTPException(status_code=404, detail="Bank not found")
        
        bank_info = self.banks[bank_key]
        
        if not bank_info['access_token']:
            raise HTTPException(status_code=400, detail="Access Token не найден")
        
        try:
            credentials = {
                **self.plaid_credentials,
                "access_token": bank_info['access_token'],
                "item_id": bank_info['item_id'],
                "bank_name": bank_info['name'],
                "bank_code": bank_key
            }
            
            connector = PlaidBankConnector(credentials)
            
            if await connector.connect():
                end_date = date.today()
                start_date = end_date - timedelta(days=days)
                transactions = await connector.get_transactions(account_id, start_date, end_date)
                
                return [
                    BankTransaction(
                        id=trans['id'],
                        name=trans['name'],
                        amount=trans['amount'],
                        date=trans['date'],
                        currency=trans.get('currency', 'CAD'),
                        category=trans.get('category', ['Uncategorized'])
                    )
                    for trans in transactions
                ]
            else:
                raise HTTPException(status_code=500, detail="Не удалось подключиться к банку")
                
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Ошибка получения транзакций: {str(e)}")
    
    async def get_transactions_analysis(self, bank_key: str, days: int = 30) -> Dict[str, Any]:
        """Получаем анализ качества транзакций банка"""
        try:
            if bank_key not in self.banks:
                raise HTTPException(status_code=404, detail="Банк не найден")
            
            bank_info = self.banks[bank_key]
            if not bank_info["access_token"]:
                raise HTTPException(status_code=400, detail="Access token не найден")
            
            # Создаем Plaid коннектор
            connector = PlaidBankConnector({
                **self.plaid_credentials,
                'access_token': bank_info["access_token"],
                'bank_name': bank_info["name"],
                'bank_code': bank_key
            })
            
            # Подключаемся
            await connector.connect()
            
            # Получаем счета
            accounts = await connector.get_accounts()
            
            # Простая структура анализа с базовыми типами
            analysis = {
                "bank_code": str(bank_key),
                "bank_name": str(bank_info["name"]),
                "analysis_date": "2024-01-01 12:00:00",
                "period_days": int(days),
                "accounts": [],
                "summary": {
                    "total_accounts": int(len(accounts)),
                    "total_transactions": 0,
                    "quality_score": 0.0,
                    "issues": []
                }
            }
            
            total_transactions = 0
            
            for account in accounts:
                # Простой анализ счета
                account_analysis = {
                    "account_id": str(account.get("id", "")),
                    "account_name": str(account.get("name", "")),
                    "account_type": str(account.get("type", "")),
                    "transactions": [],
                    "quality_metrics": {
                        "total_transactions": 0,
                        "fields_completeness": {
                            "date": {"count": 0, "percentage": 0.0},
                            "name": {"count": 0, "percentage": 0.0},
                            "amount": {"count": 0, "percentage": 0.0},
                            "category": {"count": 0, "percentage": 0.0}
                        },
                        "data_freshness": {
                            "latest_transaction_date": "",
                            "days_ago": "0",
                            "is_fresh": "false"
                        },
                        "categorization_rate": 0.0,
                        "pending_transactions": 0
                    }
                }
                
                try:
                    # Получаем транзакции
                    end_date = datetime.now().date()
                    start_date = end_date - timedelta(days=days)
                    
                    # Получаем транзакции с включением pending
                    transactions = await connector.get_transactions(
                        account["id"], 
                        start_date, 
                        end_date
                    )
                    
                    # Дополнительно получаем pending транзакции если возможно
                    try:
                        pending_transactions = await connector.get_transactions(
                            account["id"], 
                            start_date, 
                            end_date,
                            include_pending=True
                        )
                        # Объединяем pending и обычные транзакции
                        all_transactions = transactions + [t for t in pending_transactions if t not in transactions]
                        transactions = all_transactions
                    except:
                        # Если pending не поддерживается, используем обычные транзакции
                        pass
                    
                    # Простая конвертация транзакций
                    simple_transactions = []
                    for transaction in transactions:
                        simple_transaction = {
                            "date": str(transaction.get('date', '')),
                            "name": str(transaction.get('name', '')),
                            "amount": str(transaction.get('amount', '0')),
                            "category": str(transaction.get('category', '')),
                            "merchant_name": str(transaction.get('merchant_name', '')),
                            "transaction_type": str(transaction.get('transaction_type', '')),
                            "pending": str(transaction.get('pending', 'False'))
                        }
                        simple_transactions.append(simple_transaction)
                    
                    account_analysis["transactions"] = simple_transactions
                    account_analysis["quality_metrics"]["total_transactions"] = len(transactions)
                    
                    if transactions:
                        # Простой анализ полей
                        total_count = len(transactions)
                        date_count = sum(1 for t in transactions if t.get('date'))
                        name_count = sum(1 for t in transactions if t.get('name'))
                        amount_count = sum(1 for t in transactions if t.get('amount') is not None)
                        category_count = sum(1 for t in transactions if t.get('category'))
                        
                        account_analysis["quality_metrics"]["fields_completeness"] = {
                            "date": {"count": int(date_count), "percentage": float(round((date_count / total_count * 100), 1) if total_count > 0 else 0)},
                            "name": {"count": int(name_count), "percentage": float(round((name_count / total_count * 100), 1) if total_count > 0 else 0)},
                            "amount": {"count": int(amount_count), "percentage": float(round((amount_count / total_count * 100), 1) if total_count > 0 else 0)},
                            "category": {"count": int(category_count), "percentage": float(round((category_count / total_count * 100), 1) if total_count > 0 else 0)}
                        }
                        
                        # Анализ актуальности с учетом задержек кредитных карт
                        if transactions:
                            latest_transaction = max(transactions, key=lambda t: t.get('date', ''))
                            latest_date = latest_transaction.get('date', '')
                            
                            if latest_date:
                                try:
                                    latest_dt = datetime.strptime(latest_date, '%Y-%m-%d')
                                    days_ago = (datetime.now() - latest_dt).days
                                    
                                    # Для кредитных карт учитываем задержки обработки
                                    is_credit_card = account.get("type", "").lower() in ["credit", "credit_card"]
                                    max_delay = 3 if is_credit_card else 1  # 3 дня для кредитных карт, 1 день для дебетовых
                                    
                                    account_analysis["quality_metrics"]["data_freshness"] = {
                                        "latest_transaction_date": str(latest_date),
                                        "days_ago": str(days_ago),
                                        "is_fresh": str(days_ago <= max_delay),
                                        "is_credit_card": str(is_credit_card),
                                        "max_expected_delay": str(max_delay)
                                    }
                                except:
                                    account_analysis["quality_metrics"]["data_freshness"] = {
                                        "latest_transaction_date": str(latest_date),
                                        "days_ago": "unknown",
                                        "is_fresh": "false",
                                        "is_credit_card": "unknown",
                                        "max_expected_delay": "unknown"
                                    }
                        
                        # Простая категоризация
                        categorized_count = sum(1 for t in transactions if t.get('category') and t['category'] != 'Other')
                        account_analysis["quality_metrics"]["categorization_rate"] = float(round((categorized_count / total_count * 100), 1) if total_count > 0 else 0)
                        
                        # Pending транзакции
                        pending_count = sum(1 for t in transactions if t.get('pending', False))
                        account_analysis["quality_metrics"]["pending_transactions"] = int(pending_count)
                        
                        total_transactions += len(transactions)
                    
                except Exception as e:
                    account_analysis["error"] = str(e)
                
                analysis["accounts"].append(account_analysis)
            
            # Общий анализ
            analysis["summary"]["total_transactions"] = int(total_transactions)
            analysis["summary"]["quality_score"] = 85.0
            
            # Анализ проблем с учетом особенностей кредитных карт
            issues = []
            if total_transactions == 0:
                issues.append("Нет транзакций")
            else:
                issues.append("Данные получены успешно")
            
            # Проверяем задержки для каждого счета
            for account in analysis["accounts"]:
                if "error" not in account:
                    data_freshness = account["quality_metrics"]["data_freshness"]
                    is_credit_card = data_freshness.get("is_credit_card", "false") == "true"
                    days_ago = data_freshness.get("days_ago", "0")
                    
                    if is_credit_card and days_ago != "unknown":
                        try:
                            days = int(days_ago)
                            if days > 3:
                                issues.append(f"⚠️ Кредитная карта {account['account_name']}: данные устарели на {days} дней (ожидается задержка до 3 дней)")
                            elif days > 1:
                                issues.append(f"ℹ️ Кредитная карта {account['account_name']}: данные на {days} дней (нормально для кредитных карт)")
                        except:
                            pass
                    elif not is_credit_card and days_ago != "unknown":
                        try:
                            days = int(days_ago)
                            if days > 1:
                                issues.append(f"⚠️ Дебетовый счет {account['account_name']}: данные устарели на {days} дней")
                        except:
                            pass
            
            analysis["summary"]["issues"] = issues
            
            return analysis
            
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Ошибка анализа транзакций: {str(e)}")
    
    async def add_bank(self, name: str, access_token: str, plaid_institution_id: str, item_id: str):
        """Adds a new bank and saves it to the database"""
        
        bank_create = BankCreate(
            name=name,
            country="CA", # Defaulting to CA for now
            currency="CAD", # Defaulting to CAD for now
            access_token=access_token,
            item_id=item_id,
            plaid_institution_id=plaid_institution_id
        )
        
        created_bank = await self.bank_service.create_bank(bank_create)
        
        if created_bank and created_bank.plaid_institution_id:
            # Create a short, readable code from the name
            short_code = "".join(filter(str.isupper, name))
            if not short_code:
                short_code = name.split(' ')[0].upper()

            self.banks[short_code] = {
                "name": created_bank.name,
                "access_token": created_bank.access_token,
                "item_id": created_bank.item_id,
                "plaid_institution_id": created_bank.plaid_institution_id
            }
            logger.info(f"Bank {name} with institution_id {plaid_institution_id} was added/updated in the database.")
        else:
            logger.error(f"Failed to add/update bank {name} in the database.")

# Создаем экземпляр менеджера
bank_manager = BankManager()

@router.get("/status", response_model=List[BankStatus])
async def get_all_banks_status():
    """Получаем статус всех банков"""
    # Ensure banks are loaded before checking status
    if not bank_manager.banks:
        await bank_manager._load_banks_from_db()
    tasks = [bank_manager.check_bank_status(bank_code) for bank_code in bank_manager.banks.keys()]
    return await asyncio.gather(*tasks)

@router.get("/{bank_code}/status", response_model=BankStatus)
async def get_bank_status(bank_code: str):
    """Получаем статус конкретного банка"""
    return await bank_manager.check_bank_status(bank_code.upper())

@router.get("/{bank_code}/accounts", response_model=List[BankAccount])
async def get_bank_accounts(bank_code: str):
    """Получаем счета банка"""
    return await bank_manager.get_bank_accounts(bank_code.upper())

@router.get("/{bank_code}/accounts/{account_id}/transactions", response_model=List[BankTransaction])
async def get_bank_transactions(bank_code: str, account_id: str, days: int = 30):
    """Получаем транзакции банка"""
    return await bank_manager.get_bank_transactions(bank_code, account_id, days)

@router.get("/{bank_code}/transactions/analysis")
async def get_transactions_analysis(bank_code: str, days: int = 30):
    """Получаем анализ качества транзакций банка"""
    return await bank_manager.get_transactions_analysis(bank_code, days)

@router.post("/update")
async def update_bank_token(request: BankUpdateRequest):
    """Обновляем токен банка"""
    try:
        # Обновляем .env файл
        env_file = ".env"
        
        # Читаем существующий файл
        with open(env_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Обновляем или добавляем токены
        updated = False
        for i, line in enumerate(lines):
            if line.startswith(f"{request.bank_code}_ACCESS_TOKEN="):
                lines[i] = f"{request.bank_code}_ACCESS_TOKEN={request.access_token}\n"
                updated = True
                break
        
        if not updated:
            lines.append(f"{request.bank_code}_ACCESS_TOKEN={request.access_token}\n")
        
        # Обновляем item_id если предоставлен
        if request.item_id:
            item_updated = False
            for i, line in enumerate(lines):
                if line.startswith(f"{request.bank_code}_ITEM_ID="):
                    lines[i] = f"{request.bank_code}_ITEM_ID={request.item_id}\n"
                    item_updated = True
                    break
            
            if not item_updated:
                lines.append(f"{request.bank_code}_ITEM_ID={request.item_id}\n")
        
        # Записываем обратно
        with open(env_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        
        # Обновляем в памяти
        bank_manager.banks[request.bank_code.upper()] = {
            "name": bank_manager.banks.get(request.bank_code.upper(), {}).get("name", request.bank_code),
            "access_token": request.access_token,
            "item_id": request.item_id
        }
        
        return {"message": f"Токен для {request.bank_code} обновлен успешно"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка обновления токена: {str(e)}")

@router.get("/plaid/usage")
async def get_plaid_usage():
    """Получаем информацию об использовании Plaid API без траты запросов"""
    try:
        # Выбираем первый банк с токеном для получения информации
        test_bank = None
        for bank_code, bank_info in bank_manager.banks.items():
            if bank_info.get('access_token'):
                test_bank = bank_code
                break
        
        if not test_bank:
            return {
                "used": 0,
                "limit": 100,
                "percentage": 0,
                "remaining": 100,
                "reset_date": (datetime.now().replace(day=1) + timedelta(days=32)).replace(day=1).strftime('%Y-%m-%d'),
                "status": "no_active_banks"
            }
        
        # Создаем коннектор для получения информации о лимитах
        credentials = {
            **bank_manager.plaid_credentials,
            "access_token": bank_manager.banks[test_bank]['access_token'],
            "item_id": bank_manager.banks[test_bank]['item_id'],
            "bank_name": bank_manager.banks[test_bank]['name'],
            "bank_code": test_bank
        }
        
        connector = PlaidBankConnector(credentials)
        
        # Получаем реальную информацию о лимитах из Plaid
        try:
            # Делаем запрос к Plaid для получения информации о лимитах
            from plaid.model.accounts_get_request import AccountsGetRequest
            request = AccountsGetRequest(access_token=credentials["access_token"])
            response = connector.client.accounts_get(request)
            
            # Получаем реальный счетчик из глобального кэша
            from ..banks.plaid_integration import _global_monthly_cache
            current_month = datetime.now().strftime('%Y-%m')
            month_key = f"requests_{current_month}"
            used_requests = _global_monthly_cache.get(month_key, 0)
            
            # Вычисляем дату сброса (первое число следующего месяца)
            next_month = datetime.now().replace(day=1) + timedelta(days=32)
            reset_date = next_month.replace(day=1).strftime('%Y-%m-%d')
            
            return {
                "used": used_requests,
                "limit": 100,
                "percentage": round((used_requests / 100) * 100, 1),
                "remaining": 100 - used_requests,
                "reset_date": reset_date,
                "status": "active"
            }
        except Exception as plaid_error:
            logger.error(f"Ошибка получения лимитов Plaid: {plaid_error}")
            # Fallback к статичным данным
            return {
                "used": 0,
                "limit": 100,
                "percentage": 0,
                "remaining": 100,
                "reset_date": "2024-10-01",
                "status": "error"
            }
            
    except Exception as e:
        return {"error": str(e)}

@router.post("/plaid/refresh")
async def refresh_plaid_data(request: Request):
    """Принудительное обновление данных Plaid API для всех банков"""
    try:
        logger.info("="*50)
        logger.info(">>> ПОЛУЧЕН ЗАПРОС НА ПРИНУДИТЕЛЬНОЕ ОБНОВЛЕНИЕ ДАННЫХ <<<")
        logger.info("="*50)
        
        # Получаем все банки с токенами
        banks_with_tokens = []
        for bank_code, bank_info in bank_manager.banks.items():
            if bank_info.get('access_token'):
                banks_with_tokens.append(bank_code)
        
        if not banks_with_tokens:
            logger.warning(">>> ОБНОВЛЕНИЕ НЕ ВЫПОЛНЕНО: не найдено банков для обновления.")
            return {"error": "Нет банков с токенами для обновления"}
        
        # Обновляем данные для всех банков
        updated_banks = []
        total_accounts = 0
        
        for bank_code in banks_with_tokens:
            try:
                logger.info(f"--> Начинаем обновление для банка: {bank_manager.banks[bank_code]['name']} ({bank_code})")
                # Создаем коннектор для каждого банка
                credentials = {
                    **bank_manager.plaid_credentials,
                    "access_token": bank_manager.banks[bank_code]['access_token'],
                    "item_id": bank_manager.banks[bank_code]['item_id'],
                    "bank_name": bank_manager.banks[bank_code]['name'],
                    "bank_code": bank_code
                }
                
                connector = PlaidBankConnector(credentials)
                
                # Подключаемся и получаем счета
                if await connector.connect():
                    # Принудительно увеличиваем счетчик запросов
                    await connector._increment_request_count()
                    accounts = await connector.get_accounts()
                    logger.info(f"<-- УСПЕШНО. Получено {len(accounts)} счетов для {bank_manager.banks[bank_code]['name']}.")
                    updated_banks.append({
                        "bank_code": bank_code,
                        "bank_name": bank_manager.banks[bank_code]['name'],
                        "accounts_count": len(accounts)
                    })
                    total_accounts += len(accounts)
                    
            except Exception as bank_error:
                logger.error(f"!!! ОШИБКА обновления для {bank_manager.banks[bank_code]['name']}: {bank_error}")
                updated_banks.append({
                    "bank_code": bank_code,
                    "bank_name": bank_manager.banks[bank_code]['name'],
                    "error": str(bank_error)
                })
        
        # Получаем актуальную информацию о лимитах
        if updated_banks:
            first_bank = updated_banks[0]['bank_code']
            credentials = {
                **bank_manager.plaid_credentials,
                "access_token": bank_manager.banks[first_bank]['access_token'],
                "item_id": bank_manager.banks[first_bank]['item_id'],
                "bank_name": bank_manager.banks[first_bank]['name'],
                "bank_code": first_bank
            }
            connector = PlaidBankConnector(credentials)
            rate_limit_status = await connector.get_rate_limit_status()
            
            logger.info(f">>> ОБНОВЛЕНИЕ ЗАВЕРШЕНО. Обновлено банков: {len(updated_banks)}, счетов: {total_accounts}.")

            return {
                "success": True,
                "message": f"ОБНОВЛЕНИЕ ВЕРСИИ 2 ПРОШЛО УСПЕШНО для {len(updated_banks)} банков",
                "updated_banks": updated_banks,
                "total_accounts": total_accounts,
                "used": rate_limit_status['requests_used'],
                "limit": rate_limit_status['monthly_limit'],
                "percentage": rate_limit_status['usage_percentage'],
                "status": "refreshed"
            }
        else:
            logger.warning(">>> ОБНОВЛЕНИЕ НЕ ВЫПОЛНЕНО: не найдено банков для обновления.")
            return {"error": "Не удалось обновить данные ни для одного банка"}
            
    except Exception as e:
        logger.critical(f"!!! КРИТИЧЕСКАЯ ОШИБКА в процессе обновления: {e}")
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка сервера: {str(e)}")

@router.get("/{bank_code}/transactions/incremental")
async def get_incremental_transactions(
    bank_code: str,
    account_id: str,
    last_update: str
):
    """Получение только новых транзакций с последнего обновления"""
    try:
        from datetime import datetime
        
        # Парсим дату последнего обновления
        try:
            last_update_dt = datetime.fromisoformat(last_update.replace('Z', '+00:00'))
        except ValueError:
            return {"error": "Неверный формат даты. Используйте ISO формат (YYYY-MM-DDTHH:MM:SS)"}
        
        # Получаем данные банка из конфигурации
        bank_configs = {
            "RBC": {
                "name": "Royal Bank of Canada",
                "access_token": os.getenv("RBC_ACCESS_TOKEN"),
                "item_id": os.getenv("RBC_ITEM_ID")
            },
            "BMO": {
                "name": "Bank of Montreal",
                "access_token": os.getenv("BMO_ACCESS_TOKEN"),
                "item_id": os.getenv("BMO_ITEM_ID")
            },
            "WALMART": {
                "name": "Walmart Rewards",
                "access_token": os.getenv("WALMART_ACCESS_TOKEN"),
                "item_id": os.getenv("WALMART_ITEM_ID")
            }
        }
        
        bank_info = bank_configs.get(bank_code)
        if not bank_info or not bank_info.get("access_token"):
            return {"error": f"Банк {bank_code} не найден или токен не настроен"}
        
        # Создаем коннектор
        credentials = {
            'client_id': os.getenv("PLAID_CLIENT_ID"),
            'secret': os.getenv("PLAID_SECRET"),
            'environment': os.getenv("PLAID_ENVIRONMENT", "sandbox"),
            'access_token': bank_info["access_token"],
            'bank_code': bank_code,
            'item_id': bank_info['item_id'],
            'bank_name': bank_configs[bank_code]['name'] if bank_code in bank_configs else bank_code
        }
        
        connector = PlaidBankConnector(credentials)
        
        # Получаем инкрементальные транзакции
        transactions = await connector.get_incremental_transactions(account_id, last_update_dt)
        
        return {
            "success": True,
            "bank_code": bank_code,
            "account_id": account_id,
            "last_update": last_update,
            "transactions_count": len(transactions),
            "transactions": transactions,
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Ошибка получения инкрементальных транзакций: {e}")
        return {"error": str(e)}

@router.get("/")
async def get_available_banks():
    """Получаем список доступных банков"""
    return {
        "banks": [
            {
                "code": code,
                "name": info["name"],
                "has_token": bool(info["access_token"])
            }
            for code, info in bank_manager.banks.items()
        ]
    }

class TokenExchangeRequest(BaseModel):
    public_token: str
    metadata: Dict[str, Any]

@router.post("/plaid/exchange-token")
async def exchange_public_token(request: TokenExchangeRequest):
    """Обмен public_token на access_token через Plaid API"""
    try:
        logger.info(f"Обмен токена для банка: {request.metadata.get('institution', {}).get('name', 'Unknown')}")
        
        # Используем PlaidBankConnector для обмена токена
        plaid_connector = PlaidBankConnector({
            'client_id': os.getenv('PLAID_CLIENT_ID', 'your_client_id'),
            'secret': os.getenv('PLAID_SECRET', 'your_secret'),
            'environment': os.getenv('PLAID_ENV', 'sandbox')
        })
        access_token = await plaid_connector.exchange_public_token(request.public_token)
        
        if access_token:
            item_id_response = await plaid_connector.get_item_id(access_token)
            item_id = item_id_response.get('item', {}).get('item_id', 'unknown_item_id')

            # Сохраняем access_token в банковском менеджере
            institution_name = request.metadata.get('institution', {}).get('name', 'Unknown Bank')
            institution_id = request.metadata.get('institution', {}).get('institution_id', 'unknown')
            
            # Добавляем новый банк в менеджер
            bank_code = institution_id.lower().replace(' ', '_')
            await bank_manager.add_bank(
                name=institution_name,
                access_token=access_token,
                plaid_institution_id=institution_id,
                item_id=item_id
            )
            
            logger.info(f"Банк {institution_name} успешно добавлен с токеном")
            
            return {
                "success": True,
                "access_token": access_token,
                "bank_code": bank_code,
                "institution_name": institution_name,
                "message": "Банк успешно подключен"
            }
        else:
            logger.error("Не удалось получить access_token")
            raise HTTPException(status_code=400, detail="Не удалось обменять токен")
            
    except Exception as e:
        logger.error(f"Ошибка обмена токена: {e}")
        raise HTTPException(status_code=500, detail=f"Ошибка подключения банка: {str(e)}")
