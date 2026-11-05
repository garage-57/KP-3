from src.api_key_manager import get_country_bbox,get_airplanes_in_bbox
from http.client import responses
import psycopg2
import json
from psycopg2.extras import RealDictCursor
import time


class DBManager:
    def __init__(self, host, port, database, user, password):
        self.conn = psycopg2.connect(
            host=host, port=port, database=database, user=user, password=password
        )
        self.cur = self.conn.cursor(cursor_factory=RealDictCursor)

    def get_countries_and_aeroplanes_count(self):
        """Список стран и количество самолётов в их воздушном пространстве."""
        self.cur.execute("""
                SELECT c.name AS country_name,
                       COUNT(a.id) AS aeroplanes_count
                FROM countries c
                LEFT JOIN aeroplanes a ON a.country_id = c.id
                GROUP BY c.id, c.name
                ORDER BY aeroplanes_count DESC;
            """)
        return self.cur.fetchall()

    def get_all_aeroplanes(self):
        """Список всех воздушных судов."""
        self.cur.execute("""
                SELECT a.icao24, a.callsign, a.origin_country,
                       a.velocity, a.baro_altitude, a.latitude, a.longitude,
                       c.name AS country_name
                FROM aeroplanes a
                JOIN countries c ON c.id = a.country_id
                ORDER BY c.name, a.callsign;
            """)
        return self.cur.fetchall()

    def get_avg_speed(self):
        """Средняя скорость по всем самолётам (м/с)."""
        self.cur.execute(
            "SELECT AVG(velocity) AS avg_speed FROM aeroplanes WHERE velocity IS NOT NULL;"
        )
        row = self.cur.fetchone()
        return row["avg_speed"] if row else None

    def get_aeroplanes_with_higher_speed(self):
        """Самолёты со скоростью выше средней."""
        self.cur.execute("""
                SELECT icao24, callsign, velocity, origin_country
                FROM aeroplanes
                WHERE velocity > (SELECT AVG(velocity) FROM aeroplanes WHERE velocity IS NOT NULL)
                ORDER BY velocity DESC;
            """)
        return self.cur.fetchall()

    def get_aeroplanes_with_keyword(self, keyword: str):
        """Самолёты, в позывном которых есть переданные символы."""
        self.cur.execute(
            """
                SELECT icao24, callsign, velocity, origin_country
                FROM aeroplanes
                WHERE callsign ILIKE %s
                ORDER BY callsign;
            """,
            (f"%{keyword}%",),
        )
        return self.cur.fetchall()

    def close(self):
        self.cur.close()
        self.conn.close()

COUNTRY_NAMES = ["Germany", "USA", "Spain", "Canada"]

db = DBManager(
    host="localhost",
    port=5432,
    database="aeroplanes",
    user="postgres",
    password="verka1289",
)

# 2. Создание таблиц
db.cur.execute("""
CREATE TABLE IF NOT EXISTS countries (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL UNIQUE,
    latitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    bounding_box JSONB
);
CREATE TABLE IF NOT EXISTS aeroplanes (
    id SERIAL PRIMARY KEY,
    icao24 VARCHAR(10) NOT NULL,
    callsign VARCHAR(20),
    origin_country VARCHAR(100),
    velocity DOUBLE PRECISION,
    baro_altitude DOUBLE PRECISION,
    longitude DOUBLE PRECISION,
    latitude DOUBLE PRECISION,
    country_id INTEGER REFERENCES countries(id),
    UNIQUE(icao24, country_id)
);
""")
db.conn.commit()

for country in COUNTRY_NAMES:
    geo = get_country_bbox(country)
    if not geo:
        print(f"Не удалось получить координаты для {country}")
        continue
    lat, lon, bbox = geo


    db.cur.execute(
        """
        INSERT INTO countries (name, latitude, longitude, bounding_box)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (name) DO NOTHING
        RETURNING id;
    """,
        (country, lat, lon, json.dumps(bbox)),
    )
    row = db.cur.fetchone()
    if row is None:
        db.cur.execute("SELECT id FROM countries WHERE name = %s", (country,))
        country_id = db.cur.fetchone()["id"]
    else:
        country_id = row["id"]
    db.conn.commit()

    # Получение самолётов
    states = get_airplanes_in_bbox(bbox)
    print(f"{country}: найдено {len(states)} самолётов")

    for s in states:
        # Формат state vector
        icao24 = s[0]
        callsign = (s[1] or "").strip()
        origin_country = s[2]
        longitude = s[5]
        latitude = s[6]
        baro_altitude = s[7]
        velocity = s[9]

        db.cur.execute(
            """
            INSERT INTO aeroplanes
                (icao24, callsign, origin_country, velocity, baro_altitude,
                 longitude, latitude, country_id)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (icao24, country_id) DO NOTHING;
        """,
            (
                icao24,
                callsign,
                origin_country,
                velocity,
                baro_altitude,
                longitude,
                latitude,
                country_id,
            ),
        )
    db.conn.commit()
    time.sleep(10)  # пауза для OpenSky (анонимный доступ)

print("\n--- Страны и количество самолётов ---")
for r in db.get_countries_and_aeroplanes_count():
    print(r)

print("\n--- Средняя скорость (м/с) ---")
print(db.get_avg_speed())

print("\n--- Самолёты быстрее средней (первые 5) ---")
for r in db.get_aeroplanes_with_higher_speed()[:5]:
    print(r)

print("\n--- Самолёты с 'DLH' в позывном ---")
for r in db.get_aeroplanes_with_keyword("DLH")[:5]:
    print(r)

db.close()
