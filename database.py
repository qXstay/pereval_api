import os
import psycopg2
from dotenv import load_dotenv
import logging
import base64

load_dotenv()

logger = logging.getLogger(__name__)


class Database:
    def __init__(self):
        self.conn = psycopg2.connect(
            host=os.getenv('FSTR_DB_HOST', 'localhost'),
            port=os.getenv('FSTR_DB_PORT', '5432'),
            dbname=os.getenv('FSTR_DB_NAME', 'pereval'),
            user=os.getenv('FSTR_DB_LOGIN', 'pereval_user'),
            password=os.getenv('FSTR_DB_PASS', 'pereval_password')
        )
        self.conn.autocommit = False

    def submit_data(self, data: dict) -> int:
        """Добавляет запись о перевале в БД и возвращает ID перевала"""
        try:
            with self.conn.cursor() as cursor:
                # 1. Сохраняем пользователя или получаем существующего
                user = data['user']
                cursor.execute(
                    "SELECT id FROM users WHERE email = %s",
                    (user['email'],)
                )
                existing_user = cursor.fetchone()
                if existing_user:
                    user_id = existing_user[0]
                else:
                    cursor.execute(
                        """
                        INSERT INTO users (email, fam, name, otc, phone)
                        VALUES (%s, %s, %s, %s, %s)
                        RETURNING id;
                        """,
                        (user['email'], user['fam'], user['name'], user.get('otc'), user['phone'])
                    )
                    user_id = cursor.fetchone()[0]

                # 2. Сохраняем координаты (с проверкой на существование)
                coords = data['coords']
                latitude = float(coords['latitude'])
                longitude = float(coords['longitude'])
                height = int(coords['height'])
                cursor.execute(
                    "SELECT id FROM coords WHERE latitude = %s AND longitude = %s AND height = %s",
                    (latitude, longitude, height)
                )
                existing_coord = cursor.fetchone()
                if existing_coord:
                    coord_id = existing_coord[0]
                else:
                    cursor.execute(
                        """
                        INSERT INTO coords (latitude, longitude, height)
                        VALUES (%s, %s, %s)
                        RETURNING id;
                        """,
                        (latitude, longitude, height)
                    )
                    coord_id = cursor.fetchone()[0]

                # 3. Сохраняем перевал
                cursor.execute(
                    """
                    INSERT INTO pereval_added (
                        beauty_title, title, other_titles, connect, add_time,
                        user_id, coord_id, status,
                        level_winter, level_summer, level_autumn, level_spring
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    RETURNING id;
                    """,
                    (
                        data['beauty_title'], data['title'], data['other_titles'], data['connect'], data['add_time'],
                        user_id, coord_id, 'new',
                        data['level'].get('winter'), data['level']['summer'],
                        data['level']['autumn'], data['level'].get('spring')
                    )
                )
                pereval_id = cursor.fetchone()[0]

                # 4. Сохраняем изображения
                for image in data['images']:
                    img_binary = base64.b64decode(image['data'])
                    cursor.execute(
                        """
                        INSERT INTO pereval_images (img, title)
                        VALUES (%s, %s)
                        RETURNING id;
                        """,
                        (img_binary, image['title'])
                    )
                    image_id = cursor.fetchone()[0]
                    cursor.execute(
                        """
                        INSERT INTO pereval_image_links (pereval_id, image_id)
                        VALUES (%s, %s);
                        """,
                        (pereval_id, image_id)
                    )

                self.conn.commit()
                return pereval_id

        except Exception as e:
            logger.error(f"Database error: {e}")
            self.conn.rollback()
            raise
        finally:
            self.conn.close()

    def get_pereval_by_id(self, pereval_id: int) -> dict:
        try:
            with self.conn.cursor() as cursor:
                cursor.execute("SELECT * FROM pereval_added WHERE id = %s", (pereval_id,))
                pereval = cursor.fetchone()
                if not pereval:
                    return None

                cursor.execute("SELECT * FROM coords WHERE id = %s", (pereval[7],))
                coords_data = cursor.fetchone()

                cursor.execute("SELECT * FROM users WHERE id = %s", (pereval[6],))
                user_data = cursor.fetchone()

                cursor.execute("""
                    SELECT i.id, i.title, i.img
                    FROM pereval_image_links l
                    JOIN pereval_images i ON l.image_id = i.id
                    WHERE l.pereval_id = %s
                """, (pereval_id,))
                images = []
                for row in cursor.fetchall():
                    img_data = base64.b64encode(row[2]).decode('utf-8')
                    images.append({'id': row[0], 'title': row[1], 'data': img_data})

                return {
                    'id': pereval[0],
                    'beauty_title': pereval[1],
                    'title': pereval[2],
                    'other_titles': pereval[3],
                    'connect': pereval[4],
                    'add_time': pereval[5].strftime("%Y-%m-%d %H:%M:%S"),
                    'status': pereval[8],
                    'level': {
                        'winter': pereval[9],
                        'summer': pereval[10],
                        'autumn': pereval[11],
                        'spring': pereval[12]
                    },
                    'coords': {
                        'latitude': float(coords_data[1]),
                        'longitude': float(coords_data[2]),
                        'height': coords_data[3]
                    },
                    'user': {
                        'email': user_data[1],
                        'fam': user_data[2],
                        'name': user_data[3],
                        'otc': user_data[4],
                        'phone': user_data[5]
                    },
                    'images': images
                }
        finally:
            self.conn.close()

    def update_pereval(self, pereval_id: int, data: dict) -> bool:
        try:
            with self.conn.cursor() as cursor:
                cursor.execute("SELECT status FROM pereval_added WHERE id = %s", (pereval_id,))
                result = cursor.fetchone()
                if not result:
                    raise ValueError("Запись не найдена")
                if result[0] != 'new':
                    raise ValueError("Редактирование запрещено: запись не в статусе 'new'")

                if 'coords' in data:
                    coords = data['coords']
                    cursor.execute(
                        "UPDATE coords SET latitude = %s, longitude = %s, height = %s WHERE id = (SELECT coord_id FROM pereval_added WHERE id = %s)",
                        (float(coords['latitude']), float(coords['longitude']), int(coords['height']), pereval_id)
                    )

                cursor.execute(
                    """
                    UPDATE pereval_added
                    SET beauty_title = COALESCE(%s, beauty_title),
                        title = COALESCE(%s, title),
                        other_titles = COALESCE(%s, other_titles),
                        connect = COALESCE(%s, connect),
                        level_winter = COALESCE(%s, level_winter),
                        level_summer = COALESCE(%s, level_summer),
                        level_autumn = COALESCE(%s, level_autumn),
                        level_spring = COALESCE(%s, level_spring)
                    WHERE id = %s
                    """,
                    (
                        data.get('beauty_title'), data.get('title'), data.get('other_titles'), data.get('connect'),
                        data.get('level', {}).get('winter') if 'level' in data else None,
                        data.get('level', {}).get('summer') if 'level' in data else None,
                        data.get('level', {}).get('autumn') if 'level' in data else None,
                        data.get('level', {}).get('spring') if 'level' in data else None,
                        pereval_id
                    )
                )

                if 'images' in data:
                    cursor.execute("DELETE FROM pereval_image_links WHERE pereval_id = %s", (pereval_id,))
                    cursor.execute("DELETE FROM pereval_images WHERE id IN (SELECT image_id FROM pereval_image_links WHERE pereval_id = %s)", (pereval_id,))
                    for image in data['images']:
                        img_binary = base64.b64decode(image['data'])
                        cursor.execute(
                            "INSERT INTO pereval_images (img, title) VALUES (%s, %s) RETURNING id",
                            (img_binary, image['title'])
                        )
                        image_id = cursor.fetchone()[0]
                        cursor.execute(
                            "INSERT INTO pereval_image_links (pereval_id, image_id) VALUES (%s, %s)",
                            (pereval_id, image_id)
                        )

                self.conn.commit()
                return True
        except Exception as e:
            self.conn.rollback()
            raise
        finally:
            self.conn.close()

    def get_pereval_by_email(self, email: str) -> list:
        try:
            with self.conn.cursor() as cursor:
                cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
                user = cursor.fetchone()
                if not user:
                    return []

                user_id = user[0]
                cursor.execute("""
                    SELECT id, beauty_title, title, other_titles, connect, add_time, status,
                           level_winter, level_summer, level_autumn, level_spring
                    FROM pereval_added
                    WHERE user_id = %s
                """, (user_id,))

                return [{
                    'id': row[0],
                    'beauty_title': row[1],
                    'title': row[2],
                    'other_titles': row[3],
                    'connect': row[4],
                    'add_time': row[5].strftime("%Y-%m-%d %H:%M:%S"),
                    'status': row[6],
                    'level': {
                        'winter': row[7],
                        'summer': row[8],
                        'autumn': row[9],
                        'spring': row[10]
                    }
                } for row in cursor.fetchall()]
        finally:
            self.conn.close()