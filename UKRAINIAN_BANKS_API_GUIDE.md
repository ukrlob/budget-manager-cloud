# 🏦 Руководство по получению API ключей украинских банков

## 🎯 **Приоритет интеграции:**

### **1. 🥇 Monobank** - Начнем с этого!

#### **Как получить API токен:**
1. **Скачайте приложение Monobank** на телефон
2. **Зарегистрируйтесь** и пройдите верификацию
3. **Перейдите в настройки** → "Для розробників"
4. **Создайте токен** для вашего приложения
5. **Скопируйте токен** и сохраните в `.env`

#### **Преимущества Monobank:**
- ✅ **Бесплатный API** - без ограничений
- ✅ **Отличная документация** - подробные примеры
- ✅ **Webhooks** - мгновенные уведомления
- ✅ **MCC категоризация** - автоматическая категоризация
- ✅ **Простая интеграция** - один токен

#### **Пример использования:**
```python
monobank = MonobankConnector({
    'token': 'your_monobank_token_here'
})
```

---

### **2. 🥈 Privat24** - Второй приоритет

#### **Как получить API доступ:**
1. **Зарегистрируйтесь** в Privat24 Business
2. **Подайте заявку** на API доступ
3. **Получите merchant_id и merchant_password**
4. **Настройте webhook** для уведомлений

#### **Преимущества Privat24:**
- ✅ **Много пользователей** - самый популярный банк
- ✅ **Курсы валют** - встроенные курсы
- ✅ **Бизнес API** - для корпоративных клиентов
- ✅ **Множество карт** - поддержка разных типов

#### **Пример использования:**
```python
privat24 = Privat24Connector({
    'merchant_id': 'your_merchant_id',
    'merchant_password': 'your_merchant_password',
    'card_number': 'your_card_number'
})
```

---

### **3. 🥉 Raiffeisen** - Третий приоритет

#### **Как получить API доступ:**
1. **Зарегистрируйтесь** в Raiffeisen Business
2. **Подайте заявку** на Developer API
3. **Получите client_id и client_secret**
4. **Настройте OAuth2** аутентификацию

#### **Преимущества Raiffeisen:**
- ✅ **Современный API** - RESTful архитектура
- ✅ **IBAN поддержка** - международные переводы
- ✅ **Карты** - управление картами
- ✅ **Курсы валют** - встроенные курсы

#### **Пример использования:**
```python
raiffeisen = RaiffeisenConnector({
    'client_id': 'your_client_id',
    'client_secret': 'your_client_secret'
})
```

---

### **4. 4️⃣ PUMB** - Дополнительный банк

#### **Как получить API доступ:**
1. **Зарегистрируйтесь** в PUMB Business
2. **Подайте заявку** на API доступ
3. **Получите client_id и client_secret**
4. **Настройте OAuth2** аутентификацию

#### **Особенности PUMB:**
- ⚠️ **Ограниченный API** - базовые функции
- ⚠️ **Базовая документация** - минимум примеров
- ✅ **Бесплатно** - без дополнительных затрат

---

## 🔧 **Техническая настройка**

### **1. Создайте файл `.env`:**
```env
# Monobank
MONOBANK_TOKEN=your_monobank_token_here

# Privat24
PRIVAT24_MERCHANT_ID=your_merchant_id
PRIVAT24_MERCHANT_PASSWORD=your_merchant_password
PRIVAT24_CARD_NUMBER=your_card_number

# Raiffeisen
RAIFFEISEN_CLIENT_ID=your_client_id
RAIFFEISEN_CLIENT_SECRET=your_client_secret

# PUMB
PUMB_CLIENT_ID=your_client_id
PUMB_CLIENT_SECRET=your_client_secret
```

### **2. Обновите `backend/app/banks/__init__.py`:**
```python
from .monobank import MonobankConnector
from .privat24 import Privat24Connector
from .pumb import PUMBConnector
from .raiffeisen import RaiffeisenConnector

__all__ = [
    'MonobankConnector',
    'Privat24Connector', 
    'PUMBConnector',
    'RaiffeisenConnector'
]
```

### **3. Создайте банк-менеджер:**
```python
class UkrainianBankManager:
    def __init__(self):
        self.banks = {
            'monobank': MonobankConnector({'token': os.getenv('MONOBANK_TOKEN')}),
            'privat24': Privat24Connector({
                'merchant_id': os.getenv('PRIVAT24_MERCHANT_ID'),
                'merchant_password': os.getenv('PRIVAT24_MERCHANT_PASSWORD'),
                'card_number': os.getenv('PRIVAT24_CARD_NUMBER')
            }),
            'raiffeisen': RaiffeisenConnector({
                'client_id': os.getenv('RAIFFEISEN_CLIENT_ID'),
                'client_secret': os.getenv('RAIFFEISEN_CLIENT_SECRET')
            }),
            'pumb': PUMBConnector({
                'client_id': os.getenv('PUMB_CLIENT_ID'),
                'client_secret': os.getenv('PUMB_CLIENT_SECRET')
            })
        }
    
    async def get_all_accounts(self):
        all_accounts = []
        for bank_name, bank in self.banks.items():
            try:
                accounts = await bank.get_accounts()
                all_accounts.extend(accounts)
            except Exception as e:
                logger.error(f"Ошибка {bank_name}: {e}")
        return all_accounts
```

---

## 📊 **План внедрения**

### **Неделя 1: Monobank**
- [ ] Получить API токен
- [ ] Протестировать интеграцию
- [ ] Настроить webhooks
- [ ] Добавить в основное приложение

### **Неделя 2: Privat24**
- [ ] Зарегистрироваться в Business
- [ ] Получить merchant credentials
- [ ] Протестировать интеграцию
- [ ] Добавить курсы валют

### **Неделя 3: Raiffeisen**
- [ ] Зарегистрироваться в Business
- [ ] Получить OAuth2 ключи
- [ ] Протестировать интеграцию
- [ ] Добавить управление картами

### **Неделя 4: PUMB (опционально)**
- [ ] Зарегистрироваться в Business
- [ ] Получить API доступ
- [ ] Протестировать интеграцию
- [ ] Добавить как дополнительный банк

---

## 🚀 **Ожидаемые результаты**

### **После Monobank:**
- ✅ **Покрытие:** 30%+ украинских пользователей
- ✅ **Функции:** Полная интеграция с webhooks
- ✅ **Стоимость:** $0/месяц
- ✅ **Время:** 1-2 дня

### **После Privat24:**
- ✅ **Покрытие:** 60%+ украинских пользователей
- ✅ **Функции:** Курсы валют, бизнес API
- ✅ **Стоимость:** $0/месяц
- ✅ **Время:** 3-5 дней

### **После Raiffeisen:**
- ✅ **Покрытие:** 80%+ украинских пользователей
- ✅ **Функции:** IBAN, карты, современный API
- ✅ **Стоимость:** $0/месяц
- ✅ **Время:** 5-7 дней

### **После PUMB:**
- ✅ **Покрытие:** 90%+ украинских пользователей
- ✅ **Функции:** Дополнительное покрытие
- ✅ **Стоимость:** $0/месяц
- ✅ **Время:** 2-3 дня

---

## 🎯 **Рекомендации**

### **Начните с Monobank потому что:**
1. **Самый простой** - один токен, отличная документация
2. **Самый функциональный** - webhooks, MCC категоризация
3. **Самый быстрый** - интеграция за 1-2 дня
4. **Самый надежный** - стабильный API

### **Добавьте Privat24 потому что:**
1. **Много пользователей** - самый популярный банк
2. **Курсы валют** - встроенная функциональность
3. **Бизнес API** - для корпоративных клиентов

### **Raiffeisen для современных функций:**
1. **IBAN поддержка** - международные переводы
2. **Управление картами** - современные функции
3. **RESTful API** - современная архитектура

---

## 🔥 **Готовы начать?**

**Следующий шаг:** Получите API токен от Monobank и начните интеграцию!

1. **Скачайте Monobank** на телефон
2. **Создайте токен** в настройках
3. **Добавьте в `.env`** файл
4. **Протестируйте** интеграцию

**Время до первого работающего банка: 1-2 дня!** 🚀
