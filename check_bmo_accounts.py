"""
Проверка всех счетов BMO через Plaid
"""

import asyncio
import logging
from datetime import datetime, date, timedelta
from dotenv import load_dotenv
from backend.app.banks.plaid_integration import PlaidBankConnector

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def check_bmo_accounts():
    """Проверяем все счета BMO"""
    print("🏦 Проверка всех счетов BMO...")
    
    plaid_credentials = {
        "client_id": "685c0e30304b670024efcd0d",
        "secret": "c85668bbb1564530b9b71ffc568424",
        "environment": "production",
        "access_token": "access-production-ed446475-839e-4f0d-8984-20f4f8a7dd53",
        "item_id": None
    }
    
    try:
        connector = PlaidBankConnector(plaid_credentials)
        
        if await connector.connect():
            print("✅ BMO: Подключение успешно")
            
            # Получаем все счета
            accounts = await connector.get_accounts()
            print(f"📊 BMO: Получено {len(accounts)} счетов")
            
            for i, account in enumerate(accounts, 1):
                print(f"\n💳 Счет {i}:")
                print(f"  ID: {account['id']}")
                print(f"  Название: {account['name']}")
                print(f"  Тип: {account['type']}")
                print(f"  Подтип: {account['subtype']}")
                print(f"  Баланс: {account['current_balance']} {account['currency']}")
                print(f"  Банк: {account.get('bank_name', 'Unknown')}")
            
            # Проверяем транзакции для каждого счета
            print(f"\n💸 Проверяем транзакции для всех счетов...")
            end_date = date.today()
            start_date = end_date - timedelta(days=30)
            
            for account in accounts:
                print(f"\n📈 Транзакции для счета: {account['name']}")
                transactions = await connector.get_transactions(account['id'], start_date, end_date)
                print(f"  Получено {len(transactions)} транзакций за 30 дней")
                
                if transactions:
                    print("  Последние 5 транзакций:")
                    for i, trans in enumerate(transactions[:5]):
                        print(f"    {i+1}. {trans['date']} - {trans['name']} - {trans['amount']} {trans.get('currency', 'CAD')}")
                else:
                    print("  Нет транзакций за этот период")
            
            return True
        else:
            print("❌ BMO: Не удалось подключиться")
            return False
            
    except Exception as e:
        print(f"❌ BMO: Ошибка - {e}")
        return False

if __name__ == "__main__":
    asyncio.run(check_bmo_accounts())

