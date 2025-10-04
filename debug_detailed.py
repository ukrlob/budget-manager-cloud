#!/usr/bin/env python3
"""
Детальная отладка токенов
"""

import os
import asyncio
from dotenv import load_dotenv
from backend.app.banks.plaid_integration import PlaidBankConnector

load_dotenv()

async def debug_detailed():
    """Детальная отладка токенов"""
    
    tokens = {
        "BMO_TOKEN": os.getenv("BMO_ACCESS_TOKEN"),
        "CIBC_TOKEN": os.getenv("CIBC_ACCESS_TOKEN")
    }
    
    plaid_credentials = {
        "client_id": os.getenv("PLAID_CLIENT_ID"),
        "secret": os.getenv("PLAID_SECRET"),
        "environment": os.getenv("PLAID_ENVIRONMENT", "production")
    }
    
    for token_name, access_token in tokens.items():
        print(f"\n=== {token_name} ===")
        print(f"Access Token: {access_token[:20]}...")
        
        try:
            credentials = {
                **plaid_credentials,
                "access_token": access_token,
                "item_id": None
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
                    print(f"  Валюта: {account.get('currency', 'N/A')}")
            else:
                print("Ошибка подключения")
                
        except Exception as e:
            print(f"Ошибка: {e}")

if __name__ == "__main__":
    asyncio.run(debug_detailed())











