import os
from pathlib import Path

import pandas as pd
import pymysql

from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
CLEAN_DIR = BASE_DIR / "data" / "clean"
CHUNK_SIZE = 5_000


# Set MARIADB_PASSWORD before running instead of storing the password here.
DB_CONFIG = {
    "host": os.getenv("MARIADB_HOST", "localhost"),
    "port": int(os.getenv("MARIADB_PORT", "3306")),
    "user": os.getenv("MARIADB_USER", "root"),
    "password": os.getenv("MARIADB_PASSWORD"),
    "database": os.getenv("MARIADB_DATABASE", "olist_db"),
    "charset": "utf8mb4",
    "cursorclass": pymysql.cursors.Cursor,
}


# Parent tables are imported before tables that normally reference them.
TABLES = {
    "category_translation": {
        "file": "category_translation_clean.csv",
        "columns": [
            "product_category_name",
            "product_category_name_english",
        ],
    },
    "customers": {
        "file": "customers_clean.csv",
        "columns": [
            "customer_id",
            "customer_unique_id",
            "customer_zip_code_prefix",
            "customer_city",
            "customer_state",
        ],
    },
    "products": {
        "file": "products_clean.csv",
        "columns": [
            "product_id",
            "product_category_name",
            "product_name_length",
            "product_description_length",
            "product_photos_qty",
            "product_weight_g",
            "product_length_cm",
            "product_height_cm",
            "product_width_cm",
        ],
    },
    "sellers": {
        "file": "sellers_clean.csv",
        "columns": [
            "seller_id",
            "seller_zip_code_prefix",
            "seller_city",
            "seller_state",
        ],
    },
    "orders": {
        "file": "orders_clean.csv",
        "columns": [
            "order_id",
            "customer_id",
            "order_status",
            "order_purchase_timestamp",
            "order_approved_at",
            "order_delivered_carrier_date",
            "order_delivered_customer_date",
            "order_estimated_delivery_date",
        ],
    },
    "order_items": {
        "file": "order_items_clean.csv",
        "columns": [
            "order_id",
            "order_item_id",
            "product_id",
            "seller_id",
            "shipping_limit_date",
            "price",
            "freight_value",
        ],
    },
    "order_payments": {
        "file": "order_payments_clean.csv",
        "columns": [
            "order_id",
            "payment_sequential",
            "payment_type",
            "payment_installments",
            "payment_value",
        ],
    },
    "order_reviews": {
        "file": "order_reviews_clean.csv",
        "columns": [
            "review_id",
            "order_id",
            "review_score",
            "review_comment_title",
            "review_comment_message",
            "review_creation_date",
            "review_answer_timestamp",
        ],
    },
    "geolocation": {
        "file": "geolocation_clean.csv",
        "columns": [
            "geolocation_zip_code_prefix",
            "geolocation_lat",
            "geolocation_lng",
            "geolocation_city",
            "geolocation_state",
        ],
    },
}


def get_connection():
    if not DB_CONFIG["password"]:
        raise RuntimeError(
            "MARIADB_PASSWORD is not set. Set it before running the importer."
        )

    return pymysql.connect(**DB_CONFIG)


def convert_value(value):
    if pd.isna(value):
        return None
    return value


def count_csv_rows(file_path: Path) -> int:
    return sum(
        len(chunk)
        for chunk in pd.read_csv(
            file_path,
            dtype="string",
            usecols=[0],
            chunksize=CHUNK_SIZE,
        )
    )


def get_table_row_count(connection, table_name: str) -> int:
    cursor = connection.cursor()
    try:
        cursor.execute(f"SELECT COUNT(*) FROM `{table_name}`")
        return int(cursor.fetchone()[0])
    finally:
        cursor.close()


def validate_review_primary_key(connection) -> None:
    cursor = connection.cursor()
    try:
        cursor.execute(
            """
            SELECT COLUMN_NAME
            FROM information_schema.KEY_COLUMN_USAGE
            WHERE TABLE_SCHEMA = DATABASE()
              AND TABLE_NAME = 'order_reviews'
              AND CONSTRAINT_NAME = 'PRIMARY'
            ORDER BY ORDINAL_POSITION
            """
        )
        primary_key = [row[0] for row in cursor.fetchall()]
    finally:
        cursor.close()

    expected = ["review_id", "order_id"]
    if primary_key != expected:
        raise RuntimeError(
            "order_reviews must have PRIMARY KEY (review_id, order_id), "
            f"but the database has PRIMARY KEY ({', '.join(primary_key)}). "
            "Run: ALTER TABLE order_reviews DROP PRIMARY KEY, "
            "ADD PRIMARY KEY (review_id, order_id);"
        )


def import_table(connection, table_name: str, config: dict) -> None:
    file_path = CLEAN_DIR / config["file"]
    expected_columns = config["columns"]

    if not file_path.is_file():
        raise FileNotFoundError(f"Clean CSV not found: {file_path}")

    print(f"\n[{table_name}] Reading: {file_path.name}")

    csv_rows = count_csv_rows(file_path)
    existing_rows = get_table_row_count(connection, table_name)
    if existing_rows == csv_rows:
        print(f"  already contains {existing_rows:,} rows; skipped")
        return
    if existing_rows:
        raise RuntimeError(
            f"{table_name} already contains {existing_rows:,} of {csv_rows:,} rows. "
            "Refusing to append to a partially imported table."
        )

    header = pd.read_csv(file_path, dtype="string", nrows=0).columns.tolist()
    if header != expected_columns:
        raise ValueError(
            f"{table_name} columns do not match.\n"
            f"Expected: {expected_columns}\n"
            f"Actual:   {header}"
        )

    placeholders = ", ".join(["%s"] * len(expected_columns))
    column_sql = ", ".join(f"`{column}`" for column in expected_columns)
    sql = (
        f"INSERT INTO `{table_name}` ({column_sql}) "
        f"VALUES ({placeholders})"
    )

    imported_rows = 0
    cursor = connection.cursor()
    try:
        for chunk in pd.read_csv(
            file_path,
            dtype="string",
            keep_default_na=True,
            na_filter=True,
            chunksize=CHUNK_SIZE,
        ):
            rows = [
                tuple(convert_value(value) for value in row)
                for row in chunk.itertuples(index=False, name=None)
            ]
            cursor.executemany(sql, rows)
            imported_rows += len(rows)
            print(f"  imported: {imported_rows:,}", end="\r")

        connection.commit()
        print(f"  imported: {imported_rows:,}")
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()


def main() -> None:
    print("Olist -> MariaDB")
    print("=" * 70)
    print(f"Database: {DB_CONFIG['database']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}")
    print("Existing rows are not deleted. Re-running may fail on duplicate keys.")

    connection = get_connection()
    try:
        validate_review_primary_key(connection)
        for table_name, config in TABLES.items():
            import_table(connection, table_name, config)
    finally:
        connection.close()

    print("\nImport completed.")


if __name__ == "__main__":
    main()