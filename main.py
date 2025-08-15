from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime
import database
import logging
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

app = FastAPI(title="FSTR Pereval API")

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Модели данных
class User(BaseModel):
    email: str
    fam: str
    name: str
    otc: Optional[str] = None
    phone: str

class Coords(BaseModel):
    latitude: str
    longitude: str
    height: str

class Level(BaseModel):
    winter: Optional[str] = None
    summer: Optional[str] = None
    autumn: Optional[str] = None
    spring: Optional[str] = None

class Image(BaseModel):
    data: str  # base64 encoded image
    title: str

class PerevalInput(BaseModel):
    beauty_title: str
    title: str
    other_titles: str = ""
    connect: str = ""
    add_time: str = Field(default_factory=lambda: datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    user: User
    coords: Coords
    level: Level
    images: List[Image] = Field(..., min_items=1)


class PerevalUpdate(BaseModel):
    """Модель для обновления данных перевала"""
    beauty_title: Optional[str] = None
    title: Optional[str] = None
    other_titles: Optional[str] = None
    connect: Optional[str] = None
    coords: Optional[Coords] = None
    level: Optional[Level] = None
    images: Optional[List[Image]] = None

@app.post("/submitData", summary="Submit new pereval data")
async def submit_data(pereval: PerevalInput):
    try:
        db = database.Database()
        pereval_id = db.submit_data(pereval.dict())
        return {
            "status": 200,
            "message": "Отправлено успешно",
            "id": pereval_id
        }
    except ValueError as e:
        return {
            "status": 400,
            "message": str(e),
            "id": None
        }
    except Exception as e:
        logger.error(f"API error: {e}")
        return {
            "status": 500,
            "message": f"Внутренняя ошибка сервера",
            "id": None
        }

@app.get("/")
async def read_root():
    return {"message": "FSTR Pereval API is running"}

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    return JSONResponse(
        status_code=400,
        content={"status": 400, "message": "Bad Request: недостаточно данных", "id": None},
    )


@app.get("/submitData/{pereval_id}", summary="Get pereval by ID")
async def get_pereval(pereval_id: int):
    try:
        db = database.Database()
        pereval = db.get_pereval_by_id(pereval_id)
        if not pereval:
            return JSONResponse(
                status_code=404,
                content={"status": 404, "message": "Запись не найдена", "id": pereval_id}
            )
        return pereval
    except Exception as e:
        logger.error(f"API error: {e}")
        return JSONResponse(
            status_code=500,
            content={"status": 500, "message": "Внутренняя ошибка сервера", "id": pereval_id}
        )


@app.patch("/submitData/{pereval_id}", summary="Update pereval data")
async def update_pereval(pereval_id: int, update_data: PerevalUpdate):
    try:
        # Преобразуем данные для обновления
        update_dict = update_data.dict(exclude_unset=True)

        # Проверяем, что есть данные для обновления
        if not update_dict:
            return JSONResponse(
                status_code=400,
                content={"status": 0, "message": "Нет данных для обновления", "id": pereval_id}
            )

        db = database.Database()
        success = db.update_pereval(pereval_id, update_dict)

        if success:
            return {"status": 1, "message": "Запись успешно обновлена", "id": pereval_id}
        else:
            return {"status": 0, "message": "Не удалось обновить запись", "id": pereval_id}

    except ValueError as e:
        return {"status": 0, "message": str(e), "id": pereval_id}
    except Exception as e:
        logger.error(f"API error: {e}")
        return {"status": 0, "message": "Внутренняя ошибка сервера", "id": pereval_id}


@app.get("/submitDataByEmail", summary="Get perevals by user email")
async def get_pereval_by_email(user_email: str):
    try:
        db = database.Database()
        perevals = db.get_pereval_by_email(user_email)
        return perevals
    except Exception as e:
        logger.error(f"API error: {e}")
        return JSONResponse(
            status_code=500,
            content={"status": 500, "message": "Внутренняя ошибка сервера"}
        )