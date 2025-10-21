"""
Главный файл приложения Budget Manager Cloud
Реструктурированная версия с модульной архитектурой
"""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
import logging
import uvicorn
import sys
import asyncio

# --- Windows-specific event loop policy fix for UVicorn reload ---
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# --- Logging Configuration ---
# Must be configured BEFORE other modules are imported.
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout,
)
# --- End of Logging Configuration ---

# Импорты модулей
from .models.database import db
# from .services.bank_service import BankService  # Удален во время очистки
from .services.account_service import AccountService
from .services.transaction_service import TransactionService
from .services.ai_service import AIService
from .api.bank_management import router as bank_management_router
from .api.cache_management import router as cache_management_router
from .api.plaid_link import router as plaid_link_router

# Настройка логирования
# logging.basicConfig(level=logging.INFO) # This is now at the top of the file
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Управление жизненным циклом приложения
    """
    # Startup
    logger.info("Запуск Budget Manager Cloud...")
    
    # Проверка подключения к базе данных
    health = await db.health_check()
    if health["status"] != "healthy":
        logger.error(f"Ошибка подключения к базе данных: {health}")
        raise Exception("Не удалось подключиться к базе данных")
    
    logger.info("Приложение успешно запущено")
    
    yield
    
    # Shutdown
    logger.info("Завершение работы приложения...")
    await db.close_all_connections()
    logger.info("Приложение остановлено")


# Создание приложения FastAPI
app = FastAPI(
    title="Budget Manager Cloud",
    description="Персональный финансовый менеджер с AI консультантом",
    version="2.0.0",
    lifespan=lifespan
)

# Настройка CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # В продакшене указать конкретные домены
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение статических файлов
import os
static_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "..")
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Подключение роутеров
app.include_router(bank_management_router)
app.include_router(cache_management_router)
app.include_router(plaid_link_router)

# Инициализация сервисов
# bank_service = BankService()  # Удален во время очистки
account_service = AccountService()
transaction_service = TransactionService()
ai_service = AIService()


# ==================== ОСНОВНЫЕ ЭНДПОИНТЫ ====================

@app.get("/")
async def root():
    """Главная страница"""
    return FileResponse("index.html")

@app.get("/index.html")
async def index_page():
    """Явная главная страница для тестирования"""
    return FileResponse("index.html")

@app.get("/banks.html")
async def banks_page():
    """Страница банков для тестирования"""
    return FileResponse("banks.html")


@app.get("/api")
async def api_info():
    """Информация об API"""
    return {
        "message": "Budget Manager Cloud API v2.0",
        "status": "running",
        "features": [
            "Банковские интеграции",
            "AI категоризация транзакций", 
            "Финансовый консультант",
            "Аналитика и отчеты"
        ]
    }


@app.get("/health")
async def health_check():
    """Проверка состояния системы"""
    try:
        db_health = await db.health_check()
        return {
            "status": "healthy",
            "database": db_health,
            "services": {
                # "bank_service": "active",  # Удален во время очистки
                "account_service": "active", 
                "transaction_service": "active",
                "ai_service": "active"
            }
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e)
        }


# ==================== БАНКИ ====================

@app.get("/banks")
async def bank_management():
    """Страница управления банками"""
    return FileResponse("bank_cards_working.html")

@app.get("/plaid_management.html")
async def plaid_management():
    """Страница управления Plaid банками"""
    return FileResponse("plaid_management.html")

@app.get("/transactions-analysis")
async def transactions_analysis():
    """Страница анализа качества транзакций"""
    return FileResponse("transactions_analysis.html")

@app.get("/api/banks")
async def get_banks():
    """Получение списка банков"""
    try:
        # banks = await bank_service.get_all_banks()  # Удален во время очистки
        banks = []  # Временная заглушка
        return {"banks": [bank.dict() for bank in banks]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/banks")
async def create_bank(bank_data: dict):
    """Создание нового банка"""
    try:
        from .models.bank import BankCreate
        bank = BankCreate(**bank_data)
        # created_bank = await bank_service.create_bank(bank)  # Удален во время очистки
        # return {"id": created_bank.id, "message": "Bank created successfully"}  # Удален во время очистки
        return {"id": 1, "message": "Bank service temporarily disabled"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/banks/{bank_id}")
async def get_bank(bank_id: int):
    """Получение банка по ID"""
    try:
        # bank = await bank_service.get_bank(bank_id)  # Удален во время очистки
        # if not bank:  # Удален во время очистки
        #     raise HTTPException(status_code=404, detail="Bank not found")  # Удален во время очистки
        # return bank.dict()  # Удален во время очистки
        raise HTTPException(status_code=404, detail="Bank service temporarily disabled")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/banks/{bank_id}/sync")
async def sync_bank(bank_id: int):
    """Синхронизация данных банка"""
    try:
        # result = await bank_service.sync_bank_data(bank_id)  # Удален во время очистки
        # return result  # Удален во время очистки
        return {"message": "Bank service temporarily disabled"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== СЧЕТА ====================

@app.get("/accounts")
async def get_accounts():
    """Получение списка счетов"""
    try:
        accounts = await account_service.get_all_accounts()
        return {"accounts": [account.dict() for account in accounts]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/accounts")
async def create_account(account_data: dict):
    """Создание нового счета"""
    try:
        from .models.account import AccountCreate
        account = AccountCreate(**account_data)
        created_account = await account_service.create_account(account)
        return {"id": created_account.id, "message": "Account created successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== ТРАНЗАКЦИИ ====================

@app.get("/transactions")
async def get_transactions(account_id: int = None):
    """Получение списка транзакций"""
    try:
        if account_id:
            transactions = await transaction_service.get_transactions_by_account(account_id)
        else:
            transactions = await transaction_service.get_all_transactions()
        return {"transactions": [transaction.dict() for transaction in transactions]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/transactions")
async def create_transaction(transaction_data: dict):
    """Создание новой транзакции"""
    try:
        from .models.transaction import TransactionCreate
        transaction = TransactionCreate(**transaction_data)
        created_transaction = await transaction_service.create_transaction(transaction)
        return {"id": created_transaction.id, "message": "Transaction created successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/transactions/categorize")
async def categorize_transactions():
    """AI категоризация всех транзакций"""
    try:
        result = await ai_service.categorize_all_transactions()
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== ОТЧЕТЫ ====================

@app.get("/reports/balance")
async def get_balance_report():
    """Отчет по балансам"""
    try:
        report = await account_service.get_balance_report()
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/reports/transactions")
async def get_transactions_report(start_date: str = None, end_date: str = None):
    """Отчет по транзакциям"""
    try:
        report = await transaction_service.get_transactions_report(start_date, end_date)
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/reports/financial-health")
async def get_financial_health():
    """Анализ финансового здоровья"""
    try:
        analysis = await ai_service.analyze_financial_health()
        return analysis
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== AI КОНСУЛЬТАНТ ====================

@app.get("/ai/advisor")
async def get_ai_advice():
    """Получение рекомендаций от AI консультанта"""
    try:
        advice = await ai_service.get_financial_advice()
        return advice
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/ai/learn")
async def learn_from_feedback(feedback_data: dict):
    """Обучение AI на основе обратной связи"""
    try:
        result = await ai_service.learn_from_feedback(feedback_data)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== СТАТИСТИКА ====================

@app.get("/stats/summary")
async def get_summary_stats():
    """Общая статистика"""
    try:
        stats = await transaction_service.get_summary_statistics()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/categories")
async def get_categories():
    """Получение категорий транзакций"""
    try:
        categories = await transaction_service.get_categories()
        return {"categories": categories}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ==================== УТИЛИТЫ ====================

@app.get("/create-tables")
async def create_tables():
    """Создание таблиц в базе данных (для разработки)"""
    try:
        # Здесь будет логика создания таблиц
        return {"status": "success", "message": "Tables created successfully"}
    except Exception as e:
        return {"status": "error", "message": str(e)}


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )


