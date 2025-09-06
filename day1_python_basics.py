#!/usr/bin/env python3
"""
День 1: Основы Python
Образовательный проект Budget Manager Cloud
"""

print("Welcome to Python!")
print("=" * 30)
print("1. VARIABLES AND DATA TYPES:")

# Переменные и типы данных
name = "Yurii"
age = 25
height = 175.5
is_student = True

print(f"Name: {name}, Type: {type(name)}")
print(f"Age: {age}, Type: {type(age)}")
print(f"Height: {height}, Type: {type(height)}")
print(f"Is Student: {is_student}, Type: {type(is_student)}")

print("\n2. LISTS AND DICTIONARIES:")
# Списки
expenses = [100, 50, 75, 200, 30]
categories = ["food", "transport", "entertainment", "shopping", "utilities"]

print(f"Expenses: {expenses}")
print(f"Categories: {categories}")

# Словари
budget = {
    "food": 500,
    "transport": 200,
    "entertainment": 300,
    "shopping": 400,
    "utilities": 150
}

print(f"Budget: {budget}")

print("\n3. FUNCTIONS:")
def calculate_total_expenses(expenses_list):
    """Вычисляет общую сумму расходов"""
    return sum(expenses_list)

def find_category_by_expense(expense, expenses_list, categories_list):
    """Находит категорию по сумме расхода"""
    if expense in expenses_list:
        index = expenses_list.index(expense)
        return categories_list[index]
    return "Unknown"

total = calculate_total_expenses(expenses)
print(f"Total expenses: {total}")

category = find_category_by_expense(100, expenses, categories)
print(f"Category for 100: {category}")

print("\n4. LOOPS AND CONDITIONS:")
print("Expenses by category:")
for i, expense in enumerate(expenses):
    category = categories[i]
    print(f"  {category}: ${expense}")

print("\nHigh expenses (>100):")
for expense in expenses:
    if expense > 100:
        print(f"  High expense: ${expense}")

print("\n5. FILE OPERATIONS:")
# Создаем файл с данными о расходах
with open("expenses.txt", "w") as file:
    file.write("Expenses for this month:\n")
    for i, expense in enumerate(expenses):
        file.write(f"{categories[i]}: ${expense}\n")
    file.write(f"Total: ${total}\n")

print("Data saved to expenses.txt")

# Читаем файл обратно
print("\nReading from file:")
with open("expenses.txt", "r") as file:
    content = file.read()
    print(content)

print("\n6. ERROR HANDLING:")
def safe_divide(a, b):
    """Безопасное деление с обработкой ошибок"""
    try:
        result = a / b
        return result
    except ZeroDivisionError:
        print("Error: Division by zero!")
        return None
    except TypeError:
        print("Error: Invalid input types!")
        return None

print(f"10 / 2 = {safe_divide(10, 2)}")
print(f"10 / 0 = {safe_divide(10, 0)}")

print("\n" + "=" * 50)
print("Day 1 completed! Ready for Day 2.")
print("Next: Git and GitHub setup")
