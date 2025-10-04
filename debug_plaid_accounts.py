#!/usr/bin/env python3
"""
Отладочный скрипт для проверки данных Plaid
"""

import os
import asyncio
from dotenv import load_dotenv
from backend.app.banks.plaid_integration import PlaidBankConnector

load_dotenv()

async def debug_bank_accounts():
    """Отладка счетов банков"""
    
    banks = {
        "BMO": {
            "name": "Bank of Montreal",
            "access_token": os.getenv("BMO_ACCESS_TOKEN"),
            "item_id": os.getenv("BMO_ITEM_ID"),
        },
        "CIBC": {
            "name": "Canadian Imperial Bank of Commerce", 
            "access_token": os.getenv("CIBC_ACCESS_TOKEN"),
            "item_id": os.getenv("CIBC_ITEM_ID"),
        }
    }
    
    plaid_credentials = {
        "client_id": os.getenv("PLAID_CLIENT_ID"),
        "secret": os.getenv("PLAID_SECRET"),
        "environment": os.getenv("PLAID_ENVIRONMENT", "production")
    }
    
    for bank_code, bank_info in banks.items():
        print(f"\n=== {bank_code} ({bank_info['name']}) ===")
        print(f"Access Token: {bank_info['access_token'][:20]}...")
        print(f"Item ID: {bank_info['item_id']}")
        
        try:
            credentials = {
                **plaid_credentials,
                "access_token": bank_info['access_token'],
                "item_id": bank_info['item_id']
            }
            
            connector = PlaidBankConnector(credentials)
            
            if await connector.connect():
                accounts = await connector.get_accounts()
                print(f"Получено счетов: {len(accounts)}")
                
                for i, account in enumerate(accounts):
                    print(f"\nСчет {i+1}:")
                    print(f"  ID: {account.get('id', 'N/A')}")
                    print(f"  Название: {account.get('name', 'N/A')}")
                    print(f"  Тип: {account.get('type', 'N/A')}")
                    print(f"  Подтип: {account.get('subtype', 'N/A')}")
                    print(f"  Банк: {account.get('bank_name', 'N/A')}")
                    print(f"  Текущий баланс: {account.get('current_balance', 'N/A')}")
                    print(f"  Кредитный лимит: {account.get('credit_limit', 'N/A')}")
                    print(f"  Использованный кредит: {account.get('used_credit', 'N/A')}")
                    print(f"  Доступный баланс: {account.get('available_balance', 'N/A')}")
                    print(f"  Валюта: {account.get('currency', 'N/A')}")
                    print(f"  Тип баланса: {account.get('balance_type', 'N/A')}")
            else:
                print("Ошибка подключения")
                
        except Exception as e:
            print(f"Ошибка: {e}")

if __name__ == "__main__":
    asyncio.run(debug_bank_accounts())











