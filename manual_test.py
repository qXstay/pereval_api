import requests
import json
import psycopg2
from dotenv import load_dotenv
import os

# Загружаем .env
load_dotenv()

BASE_URL = "http://localhost:8000"

def clear_database():
    try:
        conn = psycopg2.connect(
            host=os.getenv('FSTR_DB_HOST'),
            port=os.getenv('FSTR_DB_PORT'),
            dbname=os.getenv('FSTR_DB_NAME'),
            user=os.getenv('FSTR_DB_LOGIN'),
            password=os.getenv('FSTR_DB_PASS')
        )
        with conn.cursor() as cursor:
            cursor.execute("DELETE FROM pereval_image_links;")
            cursor.execute("DELETE FROM pereval_images;")
            cursor.execute("DELETE FROM pereval_added;")
            cursor.execute("DELETE FROM coords;")
            cursor.execute("DELETE FROM users;")
        conn.commit()
        conn.close()
        print("База данных очищена")
    except Exception as e:
        print(f"Ошибка при очистке базы данных: {e}")

# Очистка базы перед тестом
print("\n=== 1. Очистка базы данных ===")
clear_database()

# Загружаем тестовый запрос
with open("request.json", "r", encoding="utf-8-sig") as f:
    data = json.load(f)

# 2. Тест POST
print("\n=== 2. POST /submitData ===")
response = requests.post(f"{BASE_URL}/submitData", json=data)
print(response.status_code, response.json())
pereval_id = response.json().get("id")

# Проверка наличия в БД
if pereval_id:
    conn = psycopg2.connect(
        host=os.getenv('FSTR_DB_HOST'),
        port=os.getenv('FSTR_DB_PORT'),
        dbname=os.getenv('FSTR_DB_NAME'),
        user=os.getenv('FSTR_DB_LOGIN'),
        password=os.getenv('FSTR_DB_PASS')
    )
    cur = conn.cursor()
    cur.execute("SELECT id FROM pereval_added WHERE id = %s", (pereval_id,))
    result = cur.fetchone()
    print(f"Exists in DB: {'yes' if result else 'no'}")
    cur.close()
    conn.close()
else:
    print("❌ Ошибка: ID не получен, POST не прошёл")
    exit()

# 3. GET по ID
print(f"\n=== 3. GET /submitData/{pereval_id} ===")
response = requests.get(f"{BASE_URL}/submitData/{pereval_id}")
print(response.status_code, response.json())

# 4. PATCH обновление
print(f"\n=== 4. PATCH /submitData/{pereval_id} ===")
update_data = {
    "title": "Обновленное название",
    "level": {"summer": "2Б"}
}
response = requests.patch(f"{BASE_URL}/submitData/{pereval_id}", json=update_data)
print(response.status_code, response.json())

# Проверка изменений
print(f"\n=== 5. GET /submitData/{pereval_id} после PATCH ===")
response = requests.get(f"{BASE_URL}/submitData/{pereval_id}")
print(response.status_code, response.json())

# 6. GET по email
email = data["user"]["email"]
print(f"\n=== 6. GET /submitDataByEmail?user_email={email} ===")
response = requests.get(f"{BASE_URL}/submitDataByEmail", params={"user_email": email})
print(response.status_code, response.json())