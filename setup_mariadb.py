import os
import re
from pathlib import Path

import pymysql
from dotenv import load_dotenv

load_dotenv()

import import_to_mariadb


BASE_DIR = Path(__file__).resolve().parent
DB_DIR = BASE_DIR / "db"
DATABASE_NAME = os.getenv("MARIADB_DATABASE", "olist_db")
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


def validate_database_name(name: str) -> str:
    if not re.fullmatch(r"[A-Za-z0-9_]+", name):
        raise ValueError(
            "MARIADB_DATABASE must contain only letters, numbers, and underscores."
        )
    return name


def connect_without_database():
    config = import_to_mariadb.DB_CONFIG.copy()
    config.pop("database", None)
    return pymysql.connect(**config)


def create_database() -> None:
    database_name = validate_database_name(DATABASE_NAME)
    connection = connect_without_database()
    try:
        cursor = connection.cursor()
        try:
            cursor.execute(
                f"CREATE DATABASE IF NOT EXISTS `{database_name}` "
                "CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
            )
            connection.commit()
        finally:
            cursor.close()
    finally:
        connection.close()
    print(f"Database ready: {database_name}")


def create_tables() -> None:
    connection = import_to_mariadb.get_connection()
    try:
        for file_name in TABLE_SQL_FILES:
            path = DB_DIR / file_name
            if not path.is_file():
                raise FileNotFoundError(f"Table SQL not found: {path}")
            sql = path.read_text(encoding="utf-8").replace(
                "CREATE TABLE ", "CREATE TABLE IF NOT EXISTS ", 1
            )
            cursor = connection.cursor()
            try:
                cursor.execute(sql)
                connection.commit()
            finally:
                cursor.close()
            print(f"Table ready: {path.stem}")
    finally:
        connection.close()


def main() -> None:
    print("Olist -> MariaDB database setup")
    print("=" * 70)
    print("This command does not delete databases, tables, or rows.")

    create_database()
    create_tables()
    print("\nDatabase and tables are ready. Run import_to_mariadb.py to import data.")


if __name__ == "__main__":
    main()