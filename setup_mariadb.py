import os
import re
from pathlib import Path
import pymysql
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
DB_DIR = BASE_DIR / "db"
DATABASE_NAME = os.getenv("MARIADB_DATABASE", "olist_db")

DB_CONFIG = {
    "host": os.getenv("MARIADB_HOST", "localhost"),
    "port": int(os.getenv("MARIADB_PORT", "3306")),
    "user": os.getenv("MARIADB_USER", "root"),
    "password": os.getenv("MARIADB_PASSWORD"),
    "database": DATABASE_NAME,
    "charset": "utf8mb4",
}

TABLE_SQL_FILES = [
    "category_translation.sql",
    "customers.sql",
    "products.sql",
    "sellers.sql",
    "orders.sql",
    "order_items.sql",
    "order_payments.sql",
    "order_reviews.sql",
    "geolocation.sql",
]

def create_tables() -> None:
    if not re.fullmatch(r"[A-Za-z0-9_]+", DATABASE_NAME):
        raise ValueError(
            "MARIADB_DATABASE must contain only letters, numbers, and underscores."
        )
    if not DB_CONFIG["password"]:
        raise RuntimeError("請在 .env 或環境變數中設定 MARIADB_PASSWORD！")

    server_config = DB_CONFIG.copy()
    server_config.pop("database")
    connection = pymysql.connect(**server_config)
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                f"CREATE DATABASE IF NOT EXISTS `{DATABASE_NAME}` "
                "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
        connection.commit()
    finally:
        connection.close()

    connection = pymysql.connect(**DB_CONFIG)
    try:
        cursor = connection.cursor()
        try:
            for file_name in TABLE_SQL_FILES:
                path = DB_DIR / file_name
                if not path.is_file():
                    raise FileNotFoundError(f"找不到 SQL 檔案: {path}")

                raw_sql = path.read_text(encoding="utf-8")
                statements = [stmt.strip() for stmt in raw_sql.split(";") if stmt.strip()]

                for stmt in statements:
                    cursor.execute(stmt)

                print(f"Table 已就緒: {path.stem}")

            connection.commit()
        finally:
            cursor.close()
    finally:
        connection.close()

def main() -> None:
    print(f"正在 '{DATABASE_NAME}' 資料庫中建立資料表...")
    print("=" * 60)
    create_tables()
    print("\n所有 Data Tables 建立完成！")

if __name__ == "__main__":
    main()