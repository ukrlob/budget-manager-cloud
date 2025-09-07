from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from datetime import date
import psycopg2
from psycopg2.extras import RealDictCursor

app = FastAPI(title="Budget Manager Cloud", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic models
class BankCreate(BaseModel):
    name: str
    country: str
    currency: str

class AccountCreate(BaseModel):
    bank_id: int
    account_name: str
    account_number: Optional[str] = None
    balance: float = 0.0
    currency: str

class TransactionCreate(BaseModel):
    account_id: int
    amount: float
    description: Optional[str] = None
    category: Optional[str] = None
    transaction_date: date

# Database connection
def get_db_connection():
    return psycopg2.connect(
        host="34.46.9.135",
        database="budget_cloud",
        user="postgres",
        password="BudgetCloud2025!",
        port="5432"
    )

@app.get("/")
async def root():
    return {"message": "Budget Manager Cloud API is running!"}

@app.get("/health")
async def health():
    try:
        conn = get_db_connection()
        conn.close()
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        return {"status": "unhealthy", "database": "disconnected", "error": str(e)}

@app.get("/create-tables")
async def create_tables():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Создание таблиц
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS banks (
                id SERIAL PRIMARY KEY,
                name VARCHAR(100) NOT NULL,
                country VARCHAR(50) NOT NULL,
                currency VARCHAR(3) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS accounts (
                id SERIAL PRIMARY KEY,
                bank_id INTEGER REFERENCES banks(id),
                account_name VARCHAR(100) NOT NULL,
                account_number VARCHAR(50),
                balance DECIMAL(15,2) DEFAULT 0.00,
                currency VARCHAR(3) NOT NULL,
                is_active BOOLEAN DEFAULT TRUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS transactions (
                id SERIAL PRIMARY KEY,
                account_id INTEGER REFERENCES accounts(id),
                amount DECIMAL(15,2) NOT NULL,
                description TEXT,
                category VARCHAR(50),
                transaction_date DATE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        
        # Вставка тестовых данных
        cursor.execute("""
            INSERT INTO banks (name, country, currency) VALUES 
            ('RBC', 'Canada', 'CAD'),
            ('BMO', 'Canada', 'CAD'),
            ('PrivatBank', 'Ukraine', 'UAH'),
            ('Revolut', 'Europe', 'EUR')
            ON CONFLICT DO NOTHING;
        """)
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return {"status": "success", "message": "Tables created successfully"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# Banks endpoints
@app.get("/banks")
async def get_banks():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("SELECT * FROM banks ORDER BY name")
        banks = cursor.fetchall()
        cursor.close()
        conn.close()
        return {"banks": [dict(bank) for bank in banks]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/banks")
async def create_bank(bank: BankCreate):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO banks (name, country, currency) VALUES (%s, %s, %s) RETURNING id",
            (bank.name, bank.country, bank.currency)
        )
        bank_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        conn.close()
        return {"id": bank_id, "message": "Bank created successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Accounts endpoints
@app.get("/accounts")
async def get_accounts():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("""
            SELECT a.*, b.name as bank_name 
            FROM accounts a 
            JOIN banks b ON a.bank_id = b.id 
            ORDER BY a.account_name
        """)
        accounts = cursor.fetchall()
        cursor.close()
        conn.close()
        return {"accounts": [dict(account) for account in accounts]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/accounts")
async def create_account(account: AccountCreate):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO accounts (bank_id, account_name, account_number, balance, currency) VALUES (%s, %s, %s, %s, %s) RETURNING id",
            (account.bank_id, account.account_name, account.account_number, account.balance, account.currency)
        )
        account_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        conn.close()
        return {"id": account_id, "message": "Account created successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Transactions endpoints
@app.get("/transactions")
async def get_transactions(account_id: Optional[int] = None):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        if account_id:
            cursor.execute("""
                SELECT t.*, a.account_name, b.name as bank_name 
                FROM transactions t 
                JOIN accounts a ON t.account_id = a.id 
                JOIN banks b ON a.bank_id = b.id 
                WHERE t.account_id = %s 
                ORDER BY t.transaction_date DESC
            """, (account_id,))
        else:
            cursor.execute("""
                SELECT t.*, a.account_name, b.name as bank_name 
                FROM transactions t 
                JOIN accounts a ON t.account_id = a.id 
                JOIN banks b ON a.bank_id = b.id 
                ORDER BY t.transaction_date DESC
            """)
        
        transactions = cursor.fetchall()
        cursor.close()
        conn.close()
        return {"transactions": [dict(transaction) for transaction in transactions]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/transactions")
async def create_transaction(transaction: TransactionCreate):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO transactions (account_id, amount, description, category, transaction_date) VALUES (%s, %s, %s, %s, %s) RETURNING id",
            (transaction.account_id, transaction.amount, transaction.description, transaction.category, transaction.transaction_date)
        )
        transaction_id = cursor.fetchone()[0]
        conn.commit()
        cursor.close()
        conn.close()
        return {"id": transaction_id, "message": "Transaction created successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Reports endpoints
@app.get("/reports/balance")
async def get_balance_report():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("""
            SELECT 
                b.name as bank_name,
                a.currency,
                SUM(a.balance) as total_balance,
                COUNT(a.id) as account_count
            FROM accounts a 
            JOIN banks b ON a.bank_id = b.id 
            WHERE a.is_active = true
            GROUP BY b.name, a.currency
            ORDER BY total_balance DESC
        """)
        report = cursor.fetchall()
        cursor.close()
        conn.close()
        return {"balance_report": [dict(row) for row in report]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/reports/transactions")
async def get_transactions_report(start_date: Optional[date] = None, end_date: Optional[date] = None):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        if start_date and end_date:
            cursor.execute("""
                SELECT 
                    t.*, 
                    a.account_name, 
                    b.name as bank_name,
                    b.currency
                FROM transactions t 
                JOIN accounts a ON t.account_id = a.id 
                JOIN banks b ON a.bank_id = b.id 
                WHERE t.transaction_date BETWEEN %s AND %s
                ORDER BY t.transaction_date DESC
            """, (start_date, end_date))
        else:
            cursor.execute("""
                SELECT 
                    t.*, 
                    a.account_name, 
                    b.name as bank_name,
                    b.currency
                FROM transactions t 
                JOIN accounts a ON t.account_id = a.id 
                JOIN banks b ON a.bank_id = b.id 
                ORDER BY t.transaction_date DESC
            """)
        
        transactions = cursor.fetchall()
        cursor.close()
        conn.close()
        return {"transactions_report": [dict(transaction) for transaction in transactions]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Categories endpoints
@app.get("/categories")
async def get_categories():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        cursor.execute("""
            SELECT DISTINCT category, COUNT(*) as transaction_count
            FROM transactions 
            WHERE category IS NOT NULL
            GROUP BY category
            ORDER BY transaction_count DESC
        """)
        categories = cursor.fetchall()
        cursor.close()
        conn.close()
        return {"categories": [dict(category) for category in categories]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Statistics endpoints
@app.get("/stats/summary")
async def get_summary_stats():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Общее количество транзакций
        cursor.execute("SELECT COUNT(*) as total_transactions FROM transactions")
        total_transactions = cursor.fetchone()["total_transactions"]
        
        # Общий баланс по валютам
        cursor.execute("""
            SELECT 
                currency,
                SUM(balance) as total_balance,
                COUNT(*) as account_count
            FROM accounts 
            WHERE is_active = true
            GROUP BY currency
        """)
        balance_by_currency = cursor.fetchall()
        
        # Топ категорий
        cursor.execute("""
            SELECT category, COUNT(*) as count
            FROM transactions 
            WHERE category IS NOT NULL
            GROUP BY category
            ORDER BY count DESC
            LIMIT 5
        """)
        top_categories = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return {
            "total_transactions": total_transactions,
            "balance_by_currency": [dict(row) for row in balance_by_currency],
            "top_categories": [dict(row) for row in top_categories]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))