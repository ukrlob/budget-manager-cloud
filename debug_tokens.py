#!/usr/bin/env python3
"""
Отладочный скрипт для проверки токенов
"""

import os
import asyncio
from dotenv import load_dotenv
from backend.app.banks.plaid_integration import PlaidBankConnector

load_dotenv()

async def debug_tokens():
    """Отладка токенов"""
    
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
                "item_id": None  # Не используем item_id для отладки
            }
            
            connector = PlaidBankConnector(credentials)
            
            if await connector.connect():
                accounts = await connector.get_accounts()
                print(f"Получено счетов: {len(accounts)}")
                
                for i, account in enumerate(accounts):
                    print(f"  {i+1}. {account.get('name', 'N/A')} ({account.get('type', 'N/A')}) - {account.get('bank_name', 'N/A')}")
            else:
                print("Ошибка подключения")
                
        except Exception as e:
            print(f"Ошибка: {e}")

if __name__ == "__main__":
    asyncio.run(debug_tokens())










