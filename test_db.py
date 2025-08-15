import psycopg2
from dotenv import load_dotenv
import os

load_dotenv()

print("Проверка подключения к БД...")
print("Используемые параметры:")
print(f"Хост: {os.getenv('FSTR_DB_HOST')}")
print(f"Порт: {os.getenv('FSTR_DB_PORT')}")
print(f"БД: {os.getenv('FSTR_DB_NAME')}")
print(f"Пользователь: {os.getenv('FSTR_DB_LOGIN')}")

try:
    conn = psycopg2.connect(
        host=os.getenv('FSTR_DB_HOST'),
        port=os.getenv('FSTR_DB_PORT'),
        dbname=os.getenv('FSTR_DB_NAME'),
        user=os.getenv('FSTR_DB_LOGIN'),
        password=os.getenv('FSTR_DB_PASS')
    )
    print("\nУспешное подключение к БД!")

    # Проверка существования таблиц
    with conn.cursor() as cursor:
        cursor.execute("SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'pereval_added')")
        exists = cursor.fetchone()[0]
        print(f"Таблица 'pereval_added' существует: {'Да' if exists else 'Нет'}")

    conn.close()
except Exception as e:
    print(f"\nОшибка подключения: {e}")
    print("\nУбедитесь что:")
    print("1. PostgreSQL запущен")
    print("2. Параметры в .env верные")
    print("3. БД создана командой: psql -U postgres -c 'CREATE DATABASE pereval;'")
    print("4. Таблицы созданы: psql -U postgres -d pereval -f init_db.sql")