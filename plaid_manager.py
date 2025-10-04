"""
Plaid Bank Manager - Управление банками через Plaid
Просмотр счетов, обновление токенов, добавление новых банков
"""

import asyncio
import logging
import os
from datetime import datetime, date, timedelta
from dotenv import load_dotenv
from backend.app.banks.plaid_integration import PlaidBankConnector

# Загружаем переменные окружения
load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class PlaidBankManager:
    """Менеджер для управления банками через Plaid"""
    
    def __init__(self):
        self.banks = {
            "RBC": {
                "name": "Royal Bank of Canada",
                "access_token": os.getenv("RBC_ACCESS_TOKEN"),
                "item_id": os.getenv("RBC_ITEM_ID"),
                "status": "unknown"
            },
            "BMO": {
                "name": "Bank of Montreal", 
                "access_token": os.getenv("BMO_ACCESS_TOKEN"),
                "item_id": os.getenv("BMO_ITEM_ID"),
                "status": "unknown"
            },
            "WALMART": {
                "name": "Walmart Rewards",
                "access_token": os.getenv("WALMART_ACCESS_TOKEN"),
                "item_id": os.getenv("WALMART_ITEM_ID"),
                "status": "unknown"
            },
            "CIBC": {
                "name": "Canadian Imperial Bank of Commerce",
                "access_token": os.getenv("CIBC_ACCESS_TOKEN"),
                "item_id": os.getenv("CIBC_ITEM_ID"),
                "status": "unknown"
            }
        }
        
        self.plaid_credentials = {
            "client_id": os.getenv("PLAID_CLIENT_ID"),
            "secret": os.getenv("PLAID_SECRET"),
            "environment": os.getenv("PLAID_ENVIRONMENT", "production")
        }
    
    async def check_all_banks(self):
        """Проверяем статус всех банков"""
        print("🏦 Проверка статуса всех банков...")
        print("=" * 60)
        
        for bank_code, bank_info in self.banks.items():
            print(f"\n📊 {bank_info['name']} ({bank_code})")
            print("-" * 40)
            
            if not bank_info['access_token']:
                print("❌ Access Token не найден")
                bank_info['status'] = "no_token"
                continue
            
            try:
                # Создаем коннектор для банка
                credentials = {
                    **self.plaid_credentials,
                    "access_token": bank_info['access_token'],
                    "item_id": bank_info['item_id']
                }
                
                connector = PlaidBankConnector(credentials)
                
                # Проверяем подключение
                if await connector.connect():
                    print("✅ Подключение успешно")
                    
                    # Получаем счета
                    accounts = await connector.get_accounts()
                    print(f"💳 Счетов: {len(accounts)}")
                    
                    if accounts:
                        for account in accounts:
                            balance = account.get('current_balance', 0)
                            currency = account.get('currency', 'CAD')
                            print(f"  • {account['name']} ({account['type']}) - {balance} {currency}")
                        
                        # Тестируем транзакции
                        account_id = accounts[0]['id']
                        end_date = date.today()
                        start_date = end_date - timedelta(days=7)
                        
                        transactions = await connector.get_transactions(account_id, start_date, end_date)
                        print(f"💸 Транзакций за неделю: {len(transactions)}")
                        
                        if transactions:
                            print("  Последние транзакции:")
                            for i, trans in enumerate(transactions[:3]):
                                print(f"    {i+1}. {trans['date']} - {trans['name']} - {trans['amount']} {trans.get('currency', 'CAD')}")
                    
                    bank_info['status'] = "working"
                    
                else:
                    print("❌ Не удалось подключиться")
                    bank_info['status'] = "connection_failed"
                    
            except Exception as e:
                print(f"❌ Ошибка: {e}")
                bank_info['status'] = "error"
    
    def show_bank_status(self):
        """Показываем статус всех банков"""
        print("\n📋 СТАТУС БАНКОВ")
        print("=" * 60)
        
        for bank_code, bank_info in self.banks.items():
            status_icons = {
                "working": "✅",
                "no_token": "❌",
                "connection_failed": "⚠️",
                "error": "❌",
                "unknown": "❓"
            }
            
            icon = status_icons.get(bank_info['status'], "❓")
            print(f"{icon} {bank_code}: {bank_info['name']} - {bank_info['status']}")
    
    def show_accounts_summary(self):
        """Показываем сводку по всем счетам"""
        print("\n💰 СВОДКА ПО СЧЕТАМ")
        print("=" * 60)
        
        total_accounts = 0
        total_balance = 0
        
        for bank_code, bank_info in self.banks.items():
            if bank_info['status'] == "working":
                print(f"\n🏦 {bank_info['name']} ({bank_code})")
                # Здесь можно добавить детальную информацию о счетах
                total_accounts += 1
        
        print(f"\n📊 Всего работающих банков: {total_accounts}")
    
    def show_update_instructions(self):
        """Показываем инструкции по обновлению банков"""
        print("\n🔄 ИНСТРУКЦИИ ПО ОБНОВЛЕНИЮ БАНКОВ")
        print("=" * 60)
        
        for bank_code, bank_info in self.banks.items():
            if bank_info['status'] != "working":
                print(f"\n📝 {bank_code} ({bank_info['name']}):")
                
                if bank_info['status'] == "no_token":
                    print("  • Добавьте Access Token в .env файл:")
                    print(f"    {bank_code}_ACCESS_TOKEN=your_token_here")
                
                elif bank_info['status'] == "connection_failed":
                    print("  • Проверьте правильность Access Token")
                    print("  • Возможно, токен истек - получите новый через Plaid Link")
                
                elif bank_info['status'] == "error":
                    print("  • Проверьте логи для детальной информации об ошибке")
                    print("  • Возможно, требуется повторная авторизация")
    
    def add_new_bank(self, bank_code, bank_name, access_token, item_id=None):
        """Добавляем новый банк"""
        print(f"\n➕ Добавление банка: {bank_name} ({bank_code})")
        
        # Добавляем в .env файл
        env_file = ".env"
        
        # Читаем существующий файл
        try:
            with open(env_file, 'r', encoding='utf-8') as f:
                content = f.read()
        except FileNotFoundError:
            content = ""
        
        # Добавляем новые переменные
        new_vars = f"\n# {bank_name}\n{bank_code}_ACCESS_TOKEN={access_token}\n"
        if item_id:
            new_vars += f"{bank_code}_ITEM_ID={item_id}\n"
        
        content += new_vars
        
        # Записываем обратно
        with open(env_file, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ Банк {bank_name} добавлен в .env файл")
        print("🔄 Перезапустите приложение для применения изменений")

async def main():
    """Главная функция"""
    print("🏦 PLAID BANK MANAGER")
    print("=" * 60)
    
    manager = PlaidBankManager()
    
    # Проверяем все банки
    await manager.check_all_banks()
    
    # Показываем статус
    manager.show_bank_status()
    
    # Показываем сводку
    manager.show_accounts_summary()
    
    # Показываем инструкции по обновлению
    manager.show_update_instructions()
    
    print("\n" + "=" * 60)
    print("✅ Проверка завершена!")
    
    # Интерактивное меню
    while True:
        print("\n🔧 ДОСТУПНЫЕ ДЕЙСТВИЯ:")
        print("1. Проверить все банки заново")
        print("2. Показать детальную информацию о счетах")
        print("3. Добавить новый банк")
        print("4. Показать инструкции по обновлению")
        print("5. Выход")
        
        choice = input("\nВыберите действие (1-5): ").strip()
        
        if choice == "1":
            await manager.check_all_banks()
            manager.show_bank_status()
        
        elif choice == "2":
            manager.show_accounts_summary()
        
        elif choice == "3":
            bank_code = input("Код банка (например, CIBC): ").strip().upper()
            bank_name = input("Название банка: ").strip()
            access_token = input("Access Token: ").strip()
            item_id = input("Item ID (опционально): ").strip() or None
            
            manager.add_new_bank(bank_code, bank_name, access_token, item_id)
        
        elif choice == "4":
            manager.show_update_instructions()
        
        elif choice == "5":
            print("👋 До свидания!")
            break
        
        else:
            print("❌ Неверный выбор. Попробуйте снова.")

if __name__ == "__main__":
    asyncio.run(main())

