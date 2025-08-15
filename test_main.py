import pytest
from fastapi.testclient import TestClient
from main import app
import os
import psycopg2
from dotenv import load_dotenv

load_dotenv()


@pytest.fixture
def client():
    return TestClient(app)


# Фикстура для очистки БД перед тестом
@pytest.fixture(autouse=True)
def clear_database():
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


# Фикстура для тестовых данных
@pytest.fixture
def test_data():
    return {
        "beauty_title": "пер.",
        "title": "Тестовый перевал",
        "other_titles": "",
        "connect": "",
        "user": {
            "email": "test@example.com",
            "fam": "Иванов",
            "name": "Петр",
            "otc": "Сидорович",
            "phone": "+7 999 888 77 66"
        },
        "coords": {
            "latitude": "45.0000",
            "longitude": "90.0000",
            "height": "1500"
        },
        "level": {
            "winter": "",
            "summer": "1A",
            "autumn": "1A",
            "spring": ""
        },
        "images": [{
            "data": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==",
            "title": "Тестовое фото"
        }]
    }


def test_full_flow(client, test_data):
    # 1. Создание перевала
    response = client.post("/submitData", json=test_data)
    assert response.status_code == 200
    result = response.json()
    assert result["status"] == 200
    pereval_id = result["id"]
    assert pereval_id is not None

    # 2. Получение данных
    response = client.get(f"/submitData/{pereval_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["title"] == "Тестовый перевал"
    assert data["user"]["email"] == "test@example.com"

    # 3. Обновление данных
    update = {"title": "Обновленное название"}
    response = client.patch(f"/submitData/{pereval_id}", json=update)
    assert response.status_code == 200
    assert response.json()["status"] == 1

    # 4. Проверка обновления
    response = client.get(f"/submitData/{pereval_id}")
    assert response.json()["title"] == "Обновленное название"

    # 5. Поиск по email
    response = client.get("/submitDataByEmail", params={"user_email": "test@example.com"})
    assert response.status_code == 200
    perevals = response.json()
    assert any(item["id"] == pereval_id for item in perevals)


def test_validation(client, test_data):
    # Тест на неполные данные
    invalid_data = test_data.copy()
    del invalid_data["user"]

    response = client.post("/submitData", json=invalid_data)
    assert response.status_code == 400
    assert "недостаточно данных" in response.json()["message"]


def test_update_restrictions(client, test_data):
    # Создаем перевал
    response = client.post("/submitData", json=test_data)
    pereval_id = response.json()["id"]

    # Пробуем изменить email пользователя
    update = {
        "user": {
            "email": "new@example.com"
        }
    }
    response = client.patch(f"/submitData/{pereval_id}", json=update)
    # Проверяем, что email не изменился
    response = client.get(f"/submitData/{pereval_id}")
    assert response.json()["user"]["email"] == "test@example.com"