from pathlib import Path

import pandas as pd


BASE_DIR = Path(__file__).resolve().parent
CLEAN_DIR = BASE_DIR / "data" / "clean"


SCHEMAS = {
    "customers": [
        "customer_id", "customer_unique_id", "customer_zip_code_prefix",
        "customer_city", "customer_state",
    ],
    "orders": [
        "order_id", "customer_id", "order_status", "order_purchase_timestamp",
        "order_approved_at", "order_delivered_carrier_date",
        "order_delivered_customer_date", "order_estimated_delivery_date",
    ],
    "order_items": [
        "order_id", "order_item_id", "product_id", "seller_id",
        "shipping_limit_date", "price", "freight_value",
    ],
    "order_payments": [
        "order_id", "payment_sequential", "payment_type",
        "payment_installments", "payment_value",
    ],
    "order_reviews": [
        "review_id", "order_id", "review_score", "review_comment_title",
        "review_comment_message", "review_creation_date",
        "review_answer_timestamp",
    ],
    "products": [
        "product_id", "product_category_name", "product_name_length",
        "product_description_length", "product_photos_qty", "product_weight_g",
        "product_length_cm", "product_height_cm", "product_width_cm",
    ],
    "sellers": [
        "seller_id", "seller_zip_code_prefix", "seller_city", "seller_state",
    ],
    "geolocation": [
        "geolocation_zip_code_prefix", "geolocation_lat", "geolocation_lng",
        "geolocation_city", "geolocation_state",
    ],
    "category_translation": [
        "product_category_name", "product_category_name_english",
    ],
}

FILES = {name: f"{name}_clean.csv" for name in SCHEMAS}
DATE_COLUMNS = {
    "orders": [
        "order_purchase_timestamp", "order_approved_at",
        "order_delivered_carrier_date", "order_delivered_customer_date",
        "order_estimated_delivery_date",
    ],
    "order_items": ["shipping_limit_date"],
    "order_reviews": ["review_creation_date", "review_answer_timestamp"],
}
NUMERIC_COLUMNS = {
    "order_items": ["order_item_id", "price", "freight_value"],
    "order_payments": [
        "payment_sequential", "payment_installments", "payment_value",
    ],
    "order_reviews": ["review_score"],
    "products": [
        "product_name_length", "product_description_length", "product_photos_qty",
        "product_weight_g", "product_length_cm", "product_height_cm",
        "product_width_cm",
    ],
    "geolocation": ["geolocation_lat", "geolocation_lng"],
}
ZIP_COLUMNS = {
    "customers": ["customer_zip_code_prefix"],
    "sellers": ["seller_zip_code_prefix"],
    "geolocation": ["geolocation_zip_code_prefix"],
}
PRIMARY_KEYS = {
    "customers": ["customer_id"],
    "orders": ["order_id"],
    "order_items": ["order_id", "order_item_id"],
    "order_payments": ["order_id", "payment_sequential"],
    "order_reviews": ["review_id", "order_id"],
    "products": ["product_id"],
    "sellers": ["seller_id"],
}
FOREIGN_KEYS = {
    "orders.customer_id": ("customers", "customer_id"),
    "order_items.order_id": ("orders", "order_id"),
    "order_items.product_id": ("products", "product_id"),
    "order_items.seller_id": ("sellers", "seller_id"),
    "order_payments.order_id": ("orders", "order_id"),
    "order_reviews.order_id": ("orders", "order_id"),
}


def check_table(name: str, tables: dict[str, pd.DataFrame], errors: list[str]) -> None:
    path = CLEAN_DIR / FILES[name]
    if not path.is_file():
        errors.append(f"{name}: missing file {path}")
        return

    frame = pd.read_csv(path, dtype="string", low_memory=False)
    tables[name] = frame
    if frame.columns.tolist() != SCHEMAS[name]:
        errors.append(f"{name}: columns do not match expected schema")

    null_count = int(frame.isna().sum().sum())
    print(f"{name:<22} rows={len(frame):>9,} nulls={null_count:>7,}")

    keys = PRIMARY_KEYS.get(name)
    if keys and frame.duplicated(keys).any():
        errors.append(f"{name}: duplicate primary/composite key rows")

    for column in DATE_COLUMNS.get(name, []):
        parsed = pd.to_datetime(frame[column], errors="coerce", format="mixed")
        invalid = frame[column].notna() & parsed.isna()
        if invalid.any():
            errors.append(f"{name}.{column}: {int(invalid.sum())} invalid dates")

    for column in NUMERIC_COLUMNS.get(name, []):
        values = pd.to_numeric(frame[column], errors="coerce")
        invalid = frame[column].notna() & values.isna()
        if invalid.any():
            errors.append(f"{name}.{column}: {int(invalid.sum())} invalid numbers")

    for column in ZIP_COLUMNS.get(name, []):
        invalid = frame[column].notna() & ~frame[column].str.fullmatch(r"\d{5}")
        if invalid.any():
            errors.append(f"{name}.{column}: {int(invalid.sum())} invalid ZIP codes")


def check_foreign_keys(tables: dict[str, pd.DataFrame], errors: list[str]) -> None:
    for source, (target_table, target_column) in FOREIGN_KEYS.items():
        source_table, source_column = source.split(".")
        if source_table not in tables or target_table not in tables:
            continue
        source_values = tables[source_table][source_column].dropna()
        target_values = set(tables[target_table][target_column].dropna())
        missing = source_values[~source_values.isin(target_values)]
        if not missing.empty:
            errors.append(
                f"{source}: {len(missing):,} values missing in "
                f"{target_table}.{target_column}"
            )


def main() -> int:
    print("Olist clean data quality check")
    print("=" * 70)
    tables: dict[str, pd.DataFrame] = {}
    errors: list[str] = []
    for name in SCHEMAS:
        check_table(name, tables, errors)
    check_foreign_keys(tables, errors)

    if errors:
        print("\nErrors:")
        for error in errors:
            print(f"- {error}")
        return 1

    print("\nAll checks passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())