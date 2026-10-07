import argparse
import os
from pathlib import Path

import pandas as pd
import pymysql
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
CLEAN_DIR = BASE_DIR / "data" / "clean"
CHUNK_SIZE = 5_000

DB_CONFIG = {
    "host": os.getenv("MARIADB_HOST", "localhost"),
    "port": int(os.getenv("MARIADB_PORT", "3306")),
    "user": os.getenv("MARIADB_USER", "root"),
    "password": os.getenv("MARIADB_PASSWORD"),
    "database": os.getenv("MARIADB_DATABASE", "olist_db"),
    "charset": "utf8mb4",
    "cursorclass": pymysql.cursors.Cursor,
}

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
            "geolocation_sample_count",
        ],
    },
}


def get_connection():
    if not DB_CONFIG["password"]:
        raise RuntimeError(
            "MARIADB_PASSWORD is not set. Please set it in .env or environment variable."
        )
    return pymysql.connect(**DB_CONFIG)


def convert_value(value):
    """確保任何缺值 (NaN, pd.NA, None, 空字串) 都被安全轉為 Python None"""
    if pd.isna(value) or value is None:
        return None
    val_str = str(value).strip()
    if val_str.lower() in ["nan", "nat", "<na>", "none", ""]:
        return None
    return val_str


def count_csv_rows(file_path: Path) -> int:
    return sum(
        len(chunk)
        for chunk in pd.read_csv(
            file_path,
            dtype=str,
            usecols=[0],
            chunksize=CHUNK_SIZE,
        )
    )


def import_table(connection, table_name: str, config: dict) -> None:
    file_path = CLEAN_DIR / config["file"]
    expected_columns = config["columns"]

    if not file_path.is_file():
        raise FileNotFoundError(f"Clean CSV not found: {file_path}")

    print(f"\n[{table_name}] Reading: {file_path.name}")

    header = pd.read_csv(file_path, dtype=str, nrows=0).columns.tolist()
    if header != expected_columns:
        raise ValueError(
            f"{table_name} columns do not match.\n"
            f"Expected: {expected_columns}\n"
            f"Actual:   {header}"
        )

    csv_rows = count_csv_rows(file_path)
    cursor = connection.cursor()
    try:
        cursor.execute(f"SELECT COUNT(*) FROM `{table_name}`")
        existing_rows = cursor.fetchone()[0]
    finally:
        cursor.close()

    if existing_rows == csv_rows:
        print(f"  skipped: table already has {existing_rows:,} rows")
        return
    if existing_rows:
        raise RuntimeError(
            f"{table_name} contains {existing_rows:,} rows, but its CSV has "
            f"{csv_rows:,}. No rows were changed; rerun with --replace to "
            "explicitly replace all imported tables."
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
        # 使用 standard python data structure 以避開 pandas.NA 轉譯問題
        for chunk in pd.read_csv(
            file_path,
            dtype=str,
            keep_default_na=False,  # 全部讀成字串，避免引入 pd.NA
            chunksize=CHUNK_SIZE,
        ):
            rows = [
                tuple(convert_value(val) for val in row)
                for row in chunk.itertuples(index=False, name=None)
            ]
            cursor.executemany(sql, rows)
            imported_rows += len(rows)
            print(f"  imported: {imported_rows:,} / {csv_rows:,}", end="\r")

        if imported_rows != csv_rows:
            raise RuntimeError(
                f"{table_name} imported {imported_rows:,} rows, "
                f"but its CSV contains {csv_rows:,}."
            )
        connection.commit()
        print(f"  imported: {imported_rows:,} / {csv_rows:,}")
    except Exception:
        connection.rollback()
        raise
    finally:
        cursor.close()


def validate_replace_inputs() -> None:
    for table_name, config in TABLES.items():
        file_path = CLEAN_DIR / config["file"]
        if not file_path.is_file():
            raise FileNotFoundError(f"Clean CSV not found: {file_path}")

        header = pd.read_csv(file_path, dtype=str, nrows=0).columns.tolist()
        if header != config["columns"]:
            raise ValueError(
                f"{table_name} columns do not match.\n"
                f"Expected: {config['columns']}\n"
                f"Actual:   {header}"
            )


def clear_imported_tables(connection) -> None:
    cursor = connection.cursor()
    try:
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0")
        for table_name in reversed(TABLES):
            cursor.execute(f"DELETE FROM `{table_name}`")
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        try:
            cursor.execute("SET FOREIGN_KEY_CHECKS = 1")
        finally:
            cursor.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Import cleaned Olist CSV files.")
    parser.add_argument(
        "--replace",
        action="store_true",
        help="Delete all imported table rows before loading the CSV files again.",
    )
    args = parser.parse_args()

    print("Olist -> MariaDB Importer")
    print("=" * 70)
    print(f"Database: {DB_CONFIG['database']}@{DB_CONFIG['host']}:{DB_CONFIG['port']}")

    if args.replace:
        validate_replace_inputs()

    connection = get_connection()
    try:
        if args.replace:
            print("Replacing all imported table rows as explicitly requested.")
            clear_imported_tables(connection)

        for table_name, config in TABLES.items():
            import_table(connection, table_name, config)
    finally:
        connection.close()

    print("\nImport completed successfully.")


if __name__ == "__main__":
    main()