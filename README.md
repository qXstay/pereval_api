# 🌄 FSTR Pereval API

REST API для Федеральной службы туризма России (ФСТР) по управлению данными о горных перевалах.  
Проект позволяет туристам добавлять информацию о перевалах, редактировать их (в статусе "new") и просматривать данные.

## 📌 Основные методы API

| Метод       | Путь                     | Описание                                      |
|-------------|--------------------------|-----------------------------------------------|
| `POST`      | `/submitData`            | Добавление нового перевала                    |
| `GET`       | `/submitData/{id}`       | Получение данных перевала по ID               |
| `PATCH`     | `/submitData/{id}`       | Редактирование перевала (только статус "new") |
| `GET`       | `/submitDataByEmail`     | Поиск перевалов по email пользователя         |

## Статусы модерации
- `new` - новая запись (можно редактировать)
- `pending` - модератор взял в работу
- `accepted` - модерация прошла успешно
- `rejected` - информация не принята

## 🔍 Ограничения редактирования
- Редактирование возможно **только** если запись имеет статус `new`
- **Нельзя изменять** данные пользователя:
  - ФИО (`fam`, `name`, `otc`)
  - Email
  - Телефон (`phone`)

## 🚀 Быстрый старт

### Требования
- Python 3.9+
- PostgreSQL 14+

### Установка
```bash
# Клонируем репозиторий
git clone https://github.com/qXstay/pereval_api.git
cd pereval_api

# Устанавливаем зависимости
pip install -r requirements.txt
```

### Настройка базы данных
```bash
# Создаем базу данных
psql -U postgres -c "CREATE DATABASE pereval;"

# Создаем пользователя
psql -U postgres -c "CREATE USER pereval_user WITH PASSWORD 'pereval_password';"

# Применяем схему БД
psql -U postgres -d pereval -f init_db.sql
```

### Настройка окружения
Создайте файл `.env` в корне проекта:
```env
FSTR_DB_HOST=localhost
FSTR_DB_PORT=5432
FSTR_DB_NAME=pereval
FSTR_DB_LOGIN=pereval_user
FSTR_DB_PASS=pereval_password
```

### Запуск сервера
```bash
uvicorn main:app --reload
```

Сервер будет доступен по адресу: [http://localhost:8000](http://localhost:8000)

## 📄 Документация API

Проверки можно произвести по адресу: http://localhost:8000/docs
### 1. Добавление нового перевала
**Endpoint:** `POST /submitData`  
**Тело запроса (пример):**
```json
{
  "beauty_title": "пер.",
  "title": "Пхия",
  "other_titles": "Триев",
  "connect": "",
  "add_time": "2021-09-22 13:18:13",
  "user": {
    "email": "user@example.com",
    "fam": "Пупкин",
    "name": "Василий",
    "otc": "Иванович",
    "phone": "+7 555 55 55"
  },
  "coords": {
    "latitude": "45.3842",
    "longitude": "7.1525",
    "height": "1200"
  },
  "level": {
    "winter": "",
    "summer": "1А",
    "autumn": "1А",
    "spring": ""
  },
  "images": [
    {
      "data": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==",
      "title": "Седловина"
    }
  ]
}
```

**Успешный ответ:**
```json
{
  "status": 200,
  "message": "Отправлено успешно",
  "id": 42
}
```

### 2. Получение данных о перевале
**Endpoint:** `GET /submitData/{id}`  
**Пример:**
```bash
curl -X GET "http://localhost:8000/submitData/42"
```

**Успешный ответ:**
```json
{
  "id": 42,
  "beauty_title": "пер.",
  "title": "Пхия",
  "status": "new",
  "user": {
    "email": "user@example.com",
    "fam": "Пупкин",
    "name": "Василий",
    "otc": "Иванович",
    "phone": "+7 555 55 55"
  },
  "coords": {
    "latitude": 45.3842,
    "longitude": 7.1525,
    "height": 1200
  },
  "level": {
    "winter": "",
    "summer": "1А",
    "autumn": "1А",
    "spring": ""
  },
  "images": [
    {
      "id": 1,
      "title": "Седловина",
      "data": "base64-encoded-image"
    }
  ]
}
```

### 3. Редактирование перевала
**Endpoint:** `PATCH /submitData/{id}`  
**Тело запроса (только изменяемые поля):**
```json
{
  "title": "Новое название",
  "level": {
    "summer": "2Б"
  }
}
```

**Успешный ответ:**
```json
{
  "status": 1,
  "message": "Запись успешно обновлена",
  "id": 42
}
```

**Ошибка (статус не 'new'):**
```json
{
  "status": 0,
  "message": "Редактирование запрещено: запись не в статусе 'new'",
  "id": 42
}
```

### 4. Поиск перевалов по email
**Endpoint:** `GET /submitDataByEmail?user_email=user@example.com`  
**Пример:**
```bash
curl -X GET "http://localhost:8000/submitDataByEmail?user_email=user@example.com"
```

**Успешный ответ:**
```json
[
  {
    "id": 42,
    "beauty_title": "пер.",
    "title": "Пхия",
    "other_titles": "Триев",
    "connect": "",
    "add_time": "2021-09-22T13:18:13",
    "status": "new",
    "level": {
      "winter": "",
      "summer": "1А",
      "autumn": "1А",
      "spring": ""
    }
  }
]
```

## 🧪 Тестирование
```bash
# Запуск интеграционных тестов
python manual_test.py

# Запуск теста подключения к БД
python test_db.py

# Пример вывода тестов:
# === 1. Очистка базы данных ===
# База данных очищена
# === 2. POST /submitData ===
# 200 {'status': 200, 'message': 'Отправлено успешно', 'id': 1}
# Exists in DB: yes
```

## 🔍 Swagger документация
Интерактивная документация доступна по адресу:  
[http://localhost:8000/docs](http://localhost:8000/docs) (при локальном запуске)

## ⚠️ Ошибки и их решение
```json
{
  "status": 400,
  "message": "Bad Request: недостаточно данных",
  "id": null
}
```
**Решение:** Проверьте, что все обязательные поля заполнены:

| Поле         | Обязательное |
|--------------|--------------|
| beauty_title | ✓            |
| title        | ✓            |
| user.email   | ✓            |
| user.fam     | ✓            |
| user.name    | ✓            |
| user.phone   | ✓            |
| coords       | ✓            |
| level.summer | ✓            |
| level.autumn | ✓            |
| images       | ✓ (min 1)    |


## 🧪 Автоматические тесты
Проект включает набор автоматических тестов, проверяющих:
- Полный цикл работы с перевалом (создание, чтение, обновление)
- Обработку ошибок валидации
- Ограничения редактирования данных пользователя

Для запуска тестов:
```bash
pytest test_main.py -v