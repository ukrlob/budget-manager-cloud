#!/usr/bin/env python3
"""
Скрипт для очистки кэша Plaid
"""

import os
import sys
sys.path.append('.')

# Очищаем переменные окружения
os.environ.pop('PLAID_CLIENT_ID', None)
os.environ.pop('PLAID_SECRET', None)
os.environ.pop('PLAID_ENVIRONMENT', None)

print("Кэш очищен")











