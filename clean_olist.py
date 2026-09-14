from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parent
RAW_DIR = BASE_DIR / "data" / "raw"
CLEAN_DIR = BASE_DIR / "data" / "clean"


TABLES = {
    "customers": {
        "raw": "olist_customers_dataset.csv",
        "clean": "customers_clean.csv",
        "zip_columns": ["customer_zip_code_prefix"],
        "numeric_columns": [],
        "date_columns": [],
    },
    "orders": {
        "raw": "olist_orders_dataset.csv",
        "clean": "orders_clean.csv",
        "zip_columns": [],
        "numeric_columns": [],
        "date_columns": [
            "order_purchase_timestamp",
            "order_approved_at",
            "order_delivered_carrier_date",
            "order_delivered_customer_date",
            "order_estimated_delivery_date",
        ],
    },
    "order_items": {
        "raw": "olist_order_items_dataset.csv",
        "clean": "order_items_clean.csv",
        "zip_columns": [],
        "numeric_columns": ["order_item_id", "price", "freight_value"],
        "date_columns": ["shipping_limit_date"],
    },
    "order_payments": {
        "raw": "olist_order_payments_dataset.csv",
        "clean": "order_payments_clean.csv",
        "zip_columns": [],
        "numeric_columns": [
            "payment_sequential",
            "payment_installments",
            "payment_value",
        ],
        "date_columns": [],
    },
    "order_reviews": {
        "raw": "olist_order_reviews_dataset.csv",
        "clean": "order_reviews_clean.csv",
        "zip_columns": [],
        "numeric_columns": ["review_score"],
        "date_columns": ["review_creation_date", "review_answer_timestamp"],
    },
    "products": {
        "raw": "olist_products_dataset.csv",
        "clean": "products_clean.csv",
        "zip_columns": [],
        "numeric_columns": [
            "product_name_length",
            "product_description_length",
            "product_photos_qty",
            "product_weight_g",
            "product_length_cm",
            "product_height_cm",
            "product_width_cm",
        ],
        "date_columns": [],
    },
    "sellers": {
        "raw": "olist_sellers_dataset.csv",
        "clean": "sellers_clean.csv",
        "zip_columns": ["seller_zip_code_prefix"],
        "numeric_columns": [],
        "date_columns": [],
    },
    "geolocation": {
        "raw": "olist_geolocation_dataset.csv",
        "clean": "geolocation_clean.csv",
        "zip_columns": ["geolocation_zip_code_prefix"],
        "numeric_columns": ["geolocation_lat", "geolocation_lng"],
        "date_columns": [],
    },
    "category_translation": {
        "raw": "product_category_name_translation.csv",
        "clean": "category_translation_clean.csv",
        "zip_columns": [],
        "numeric_columns": [],
        "date_columns": [],
    },
}


def clean_column_names(df: pd.DataFrame) -> pd.DataFrame:
    columns = (
        df.columns.astype("string")
        .str.strip()
        .str.lower()
        .str.replace(r"[^a-z0-9]+", "_", regex=True)
        .str.strip("_")
        .str.replace("lenght", "length", regex=False)
    )

    if columns.duplicated().any():
        duplicates = columns[columns.duplicated()].tolist()
        raise ValueError(f"Duplicate column names after cleaning: {duplicates}")

    df.columns = columns.tolist()
    return df


def clean_text_columns(df: pd.DataFrame) -> pd.DataFrame:
    for column in df.columns:
        df[column] = df[column].astype("string").str.strip()
        df[column] = df[column].replace(r"^\s*$", pd.NA, regex=True)
    return df


def clean_dates(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    for column in columns:
        if column in df.columns:
            parsed = pd.to_datetime(df[column], errors="coerce", format="mixed")
            df[column] = parsed.dt.strftime("%Y-%m-%d %H:%M:%S")
    return df


def clean_numeric(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    for column in columns:
        if column in df.columns:
            df[column] = pd.to_numeric(df[column], errors="coerce")
    return df


def clean_zip_codes(df: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    for column in columns:
        if column in df.columns:
            df[column] = df[column].astype("string").str.replace(r"\.0$", "", regex=True)
            df[column] = df[column].str.zfill(5)
    return df


def clean_table(name: str, config: dict) -> None:
    input_path = RAW_DIR / config["raw"]
    output_path = CLEAN_DIR / config["clean"]

    df = pd.read_csv(input_path, dtype="string", low_memory=False)
    df = clean_column_names(df)
    df = clean_text_columns(df)
    df = clean_dates(df, config["date_columns"])
    df = clean_numeric(df, config["numeric_columns"])
    df = clean_zip_codes(df, config["zip_columns"])

    df.to_csv(output_path, index=False, encoding="utf-8")

    print(
        f"{name:<22} rows preserved: {len(df):>9,}"
    )


def main() -> None:
    CLEAN_DIR.mkdir(parents=True, exist_ok=True)

    print("Olist data cleaning")
    print("=" * 70)
    for name, config in TABLES.items():
        clean_table(name, config)
    print(f"\nClean files written to: {CLEAN_DIR}")


if __name__ == "__main__":
    main()
