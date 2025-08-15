-- 1. Таблица пользователей
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    fam VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    otc VARCHAR(255),
    phone VARCHAR(20) NOT NULL
);

-- 2. Таблица координат
CREATE TABLE coords (
    id SERIAL PRIMARY KEY,
    latitude NUMERIC(9,6) NOT NULL,
    longitude NUMERIC(9,6) NOT NULL,
    height INTEGER NOT NULL,
    UNIQUE (latitude, longitude, height)
);

-- 3. Основная таблица перевалов
CREATE TABLE pereval_added (
    id SERIAL PRIMARY KEY,
    beauty_title VARCHAR(255) NOT NULL,
    title VARCHAR(255) NOT NULL,
    other_titles VARCHAR(255),
    connect TEXT,
    add_time TIMESTAMP WITHOUT TIME ZONE NOT NULL,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    coord_id INTEGER NOT NULL REFERENCES coords(id) ON DELETE CASCADE,
    status VARCHAR(20) NOT NULL DEFAULT 'new' CHECK (status IN ('new', 'pending', 'accepted', 'rejected')),
    level_winter VARCHAR(10),
    level_summer VARCHAR(10) NOT NULL,
    level_autumn VARCHAR(10) NOT NULL,
    level_spring VARCHAR(10)
);

-- 4. Таблица изображений
CREATE TABLE pereval_images (
    id SERIAL PRIMARY KEY,
    img BYTEA NOT NULL,
    title VARCHAR(255) NOT NULL,
    date_added TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 5. Таблица связи перевалов и изображений
CREATE TABLE pereval_image_links (
    pereval_id INTEGER NOT NULL REFERENCES pereval_added(id) ON DELETE CASCADE,
    image_id INTEGER NOT NULL REFERENCES pereval_images(id) ON DELETE CASCADE,
    PRIMARY KEY (pereval_id, image_id)
);


-- Предоставление прав пользователю pereval_user
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO pereval_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO pereval_user;