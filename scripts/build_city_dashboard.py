import csv
import json
from collections import defaultdict
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
CLEAN_DIR = BASE_DIR / "data" / "clean"
OUTPUT_PATH = BASE_DIR / "docs" / "data" / "business_summary.json"
CITY_OUTPUT_PATH = BASE_DIR / "docs" / "data" / "cities.json"
ZERO_METRICS = (
    "orders",
    "items",
    "revenue_cents",
    "freight_cents",
    "delivered",
    "on_time",
    "delayed",
    "undelivered",
    "delay_days",
    "early_days",
    "delivery_days",
    "review_score_sum",
    "review_count",
    "low_review_count",
    "buyers",
    "new_buyers",
    "payment_cents",
    "payment_count",
    "installment_sum",
)


def read_csv(file_name: str):
    path = CLEAN_DIR / file_name
    if not path.is_file():
        raise FileNotFoundError(f"Clean CSV not found: {path}")

    with path.open("r", encoding="utf-8-sig", newline="") as csv_file:
        yield from csv.DictReader(csv_file)


def empty_metrics() -> dict[str, int]:
    return {name: 0 for name in ZERO_METRICS}


def monthly_bucket(groups: dict, key, month: str) -> dict[str, int]:
    return groups[key].setdefault(month, empty_metrics())


def add_money(value: str | None) -> int:
    if not value:
        return 0
    return int(
        (Decimal(value) * 100).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    )


def parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value)


def public_series(months: list[str], data: dict[str, dict]) -> list[dict]:
    return [
        {
            "month": month,
            **{name: value for name, value in data[month].items() if value},
        }
        for month in months
        if month in data
    ]


def build_dashboard_data() -> dict:
    customers: dict[str, dict] = {}
    for row in read_csv("customers_clean.csv"):
        city = row["customer_city"].strip() or "Unknown"
        state = row["customer_state"].strip().upper() or "?"
        customers[row["customer_id"]] = {
            "buyer_id": row["customer_unique_id"],
            "city": city,
            "state": state,
        }

    category_translation = {
        row["product_category_name"]: row["product_category_name_english"]
        for row in read_csv("category_translation_clean.csv")
    }
    products = {
        row["product_id"]: category_translation.get(
            row["product_category_name"],
            row["product_category_name"] or "unknown",
        )
        for row in read_csv("products_clean.csv")
    }

    groups: dict[str, dict] = {
        "all": defaultdict(dict),
        "cities": defaultdict(dict),
        "states": defaultdict(dict),
        "categories": defaultdict(dict),
        "payments": defaultdict(dict),
    }
    buyer_profiles: dict[str, dict] = {}
    orders: dict[str, dict] = {}
    monthly_buyers: dict[str, set[str]] = defaultdict(set)
    monthly_city_buyers: dict[tuple[str, str, str], set[str]] = defaultdict(set)
    category_orders: dict[tuple[str, str], set[str]] = defaultdict(set)
    seller_orders: dict[str, set[str]] = defaultdict(set)
    order_sellers: dict[str, set[str]] = defaultdict(set)
    seller_metrics: dict[str, dict] = defaultdict(
        lambda: {
            "items": 0,
            "orders": set(),
            "revenue_cents": 0,
            "delivered": 0,
            "delayed": 0,
            "review_score_sum": 0,
            "review_count": 0,
        }
    )

    def add_to_monthly(name: str, key, month: str, **values: int) -> dict:
        bucket = monthly_bucket(groups[name], key, month)
        for field, value in values.items():
            bucket[field] += value
        return bucket

    for row in read_csv("orders_clean.csv"):
        customer = customers[row["customer_id"]]
        purchased = parse_datetime(row["order_purchase_timestamp"])
        if purchased is None:
            raise ValueError(f"Order {row['order_id']} has no purchase timestamp.")
        month = purchased.strftime("%Y-%m")
        order = {
            "month": month,
            "purchased": purchased,
            "status": row["order_status"],
            "delivered_at": parse_datetime(row["order_delivered_customer_date"]),
            "estimated_at": parse_datetime(row["order_estimated_delivery_date"]),
            "city": customer["city"],
            "state": customer["state"],
            "buyer_id": customer["buyer_id"],
            "revenue_cents": 0,
        }
        orders[row["order_id"]] = order
        monthly_buyers[month].add(customer["buyer_id"])
        monthly_city_buyers[(order["city"], order["state"], month)].add(
            customer["buyer_id"]
        )
        profile = buyer_profiles.setdefault(
            customer["buyer_id"],
            {
                "orders": 0,
                "revenue_cents": 0,
                "first_at": purchased,
                "last_at": purchased,
                "last_state": customer["state"],
                "last_city": customer["city"],
            },
        )
        profile["orders"] += 1
        if purchased < profile["first_at"]:
            profile["first_at"] = purchased
        if purchased >= profile["last_at"]:
            profile["last_at"] = purchased
            profile["last_state"] = customer["state"]
            profile["last_city"] = customer["city"]

        bucket = add_to_monthly("all", "all", month, orders=1)
        add_to_monthly("cities", (order["city"], order["state"]), month, orders=1)
        add_to_monthly("states", order["state"], month, orders=1)

        delivered = order["delivered_at"]
        estimated = order["estimated_at"]
        if row["order_status"] == "delivered" and delivered and estimated:
            bucket["delivered"] += 1
            diff = (delivered - estimated).total_seconds() / 86400
            delivery_days = max(
                0, (delivered - purchased).total_seconds() / 86400
            )
            delivery_fields = {
                "delivered": 1,
                "delivery_days": round(delivery_days * 100),
            }
            city_bucket = add_to_monthly(
                "cities", (order["city"], order["state"]), month, **delivery_fields
            )
            state_bucket = add_to_monthly(
                "states", order["state"], month, **delivery_fields
            )
            bucket["delivery_days"] += round(delivery_days * 100)
            if diff <= 0:
                early_days = round(max(0, -diff) * 100)
                bucket["on_time"] += 1
                bucket["early_days"] += early_days
                city_bucket["on_time"] += 1
                city_bucket["early_days"] += early_days
                state_bucket["on_time"] += 1
                state_bucket["early_days"] += early_days
            else:
                delay_days = round(diff * 100)
                bucket["delayed"] += 1
                bucket["delay_days"] += delay_days
                city_bucket["delayed"] += 1
                city_bucket["delay_days"] += delay_days
                state_bucket["delayed"] += 1
                state_bucket["delay_days"] += delay_days
        else:
            bucket["undelivered"] += 1
            add_to_monthly(
                "cities",
                (order["city"], order["state"]),
                month,
                undelivered=1,
            )
            add_to_monthly("states", order["state"], month, undelivered=1)

    active_months = sorted(groups["all"]["all"])
    if not active_months:
        raise ValueError("No valid orders were found in the cleaned order CSV.")
    first_year, first_month = (int(part) for part in active_months[0].split("-"))
    last_year, last_month = (int(part) for part in active_months[-1].split("-"))
    month_count = (last_year - first_year) * 12 + last_month - first_month + 1
    months = [
        f"{year:04d}-{month:02d}"
        for offset in range(month_count)
        for year, month in [
            (first_year + (first_month - 1 + offset) // 12,
             (first_month - 1 + offset) % 12 + 1)
        ]
    ]
    reference_at = max(profile["last_at"] for profile in buyer_profiles.values())

    for month in months:
        monthly_bucket(groups["all"], "all", month)
        for buyer_id in monthly_buyers[month]:
            profile = buyer_profiles[buyer_id]
            if profile["first_at"].strftime("%Y-%m") == month:
                groups["all"]["all"][month]["new_buyers"] += 1
        groups["all"]["all"][month]["buyers"] = len(monthly_buyers[month])
    for (city, state, month), buyer_ids in monthly_city_buyers.items():
        groups["cities"][(city, state)][month]["buyers"] = len(buyer_ids)

    for row in read_csv("order_items_clean.csv"):
        order_id = row["order_id"]
        order = orders[order_id]
        category = products.get(row["product_id"], "unknown") or "unknown"
        price_cents = add_money(row["price"])
        freight_cents = add_money(row["freight_value"])
        order["revenue_cents"] += price_cents
        buyer_profiles[order["buyer_id"]]["revenue_cents"] += price_cents

        values = {
            "items": 1,
            "revenue_cents": price_cents,
            "freight_cents": freight_cents,
        }
        add_to_monthly("all", "all", order["month"], **values)
        add_to_monthly(
            "cities", (order["city"], order["state"]), order["month"], **values
        )
        add_to_monthly("states", order["state"], order["month"], **values)
        add_to_monthly("categories", category, order["month"], **values)

        category_orders[(category, order["month"])].add(order_id)

        seller_id = row["seller_id"]
        order_sellers[order_id].add(seller_id)
        seller = seller_metrics[seller_id]
        seller["items"] += 1
        seller["orders"].add(order_id)
        seller["revenue_cents"] += price_cents
        seller_orders[seller_id].add(order_id)

    for (category, month), order_ids in category_orders.items():
        groups["categories"][category][month]["orders"] = len(order_ids)

    for row in read_csv("order_reviews_clean.csv"):
        order = orders[row["order_id"]]
        try:
            score = int(row["review_score"])
        except (TypeError, ValueError):
            continue
        values = {
            "review_score_sum": score,
            "review_count": 1,
            "low_review_count": int(score <= 2),
        }
        add_to_monthly("all", "all", order["month"], **values)
        add_to_monthly(
            "cities",
            (order["city"], order["state"]),
            order["month"],
            **values,
        )
        add_to_monthly("states", order["state"], order["month"], **values)
        order["review_score"] = score
        for seller_id in order_sellers[row["order_id"]]:
            seller = seller_metrics[seller_id]
            seller["review_score_sum"] += score
            seller["review_count"] += 1

    for row in read_csv("order_payments_clean.csv"):
        order = orders[row["order_id"]]
        payment_value = add_money(row["payment_value"])
        try:
            installments = int(row["payment_installments"] or 0)
        except ValueError:
            installments = 0
        add_to_monthly(
            "payments",
            row["payment_type"] or "unknown",
            order["month"],
            payment_cents=payment_value,
            payment_count=1,
            installment_sum=installments,
        )
        add_to_monthly(
            "all",
            "all",
            order["month"],
            payment_cents=payment_value,
            payment_count=1,
            installment_sum=installments,
        )

    public_cities = []
    for (city, state), series in groups["cities"].items():
        public_cities.append(
            {"city": city, "state": state, "series": public_series(months, series)}
        )
    public_cities.sort(key=lambda item: (item["state"], item["city"].casefold()))

    public_categories = []
    for name, series in groups["categories"].items():
        public_categories.append(
            {"name": name, "series": public_series(months, series)}
        )
    public_categories.sort(key=lambda item: item["name"].casefold())

    public_states = [
        {"state": state, "series": public_series(months, series)}
        for state, series in sorted(groups["states"].items())
    ]
    public_payments = [
        {"type": payment_type, "series": public_series(months, series)}
        for payment_type, series in sorted(groups["payments"].items())
    ]

    profiles = list(buyer_profiles.values())
    recency_values = sorted((reference_at - p["last_at"]).days for p in profiles)
    frequency_values = sorted(p["orders"] for p in profiles)
    monetary_values = sorted(p["revenue_cents"] for p in profiles)

    def percentile(values: list[int], fraction: float) -> int:
        if not values:
            return 0
        return values[min(len(values) - 1, int((len(values) - 1) * fraction))]

    recency_cutoffs = [
        percentile(recency_values, fraction)
        for fraction in (0.2, 0.4, 0.6, 0.8)
    ]
    frequency_cutoffs = [
        percentile(frequency_values, fraction)
        for fraction in (0.2, 0.4, 0.6, 0.8)
    ]
    monetary_cutoffs = [
        percentile(monetary_values, fraction)
        for fraction in (0.2, 0.4, 0.6, 0.8)
    ]

    def quintile(value: int, cutoffs: list[int], reverse: bool = False) -> int:
        score = 1 + sum(value > cutoff for cutoff in cutoffs)
        return 6 - score if reverse else score

    rfm_segments: dict[str, dict] = defaultdict(
        lambda: {"customers": 0, "revenue_cents": 0, "repeat_customers": 0}
    )
    aov_buckets: dict[str, dict] = defaultdict(
        lambda: {"customers": 0, "repeat_customers": 0, "revenue_cents": 0}
    )
    for profile in profiles:
        recency = (reference_at - profile["last_at"]).days
        r_score = quintile(recency, recency_cutoffs, reverse=True)
        f_score = quintile(profile["orders"], frequency_cutoffs)
        m_score = quintile(profile["revenue_cents"], monetary_cutoffs)
        if r_score >= 4 and f_score >= 4 and m_score >= 4:
            segment = "Champions"
        elif r_score <= 2 and m_score >= 4:
            segment = "High-value at risk"
        elif r_score <= 2 and f_score >= 3:
            segment = "At risk"
        elif f_score >= 4 and r_score >= 3:
            segment = "Loyal"
        elif profile["orders"] == 1 and r_score >= 4:
            segment = "Recent one-time"
        elif r_score <= 2 and f_score <= 2:
            segment = "Hibernating"
        else:
            segment = "Potential"
        segment_row = rfm_segments[segment]
        segment_row["customers"] += 1
        segment_row["revenue_cents"] += profile["revenue_cents"]
        segment_row["repeat_customers"] += int(profile["orders"] > 1)

        average_order_cents = profile["revenue_cents"] // max(1, profile["orders"])
        bucket_name = (
            "< R$100"
            if average_order_cents < 10_000
            else "R$100–R$500"
            if average_order_cents < 50_000
            else "≥ R$500"
        )
        bucket = aov_buckets[bucket_name]
        bucket["customers"] += 1
        bucket["repeat_customers"] += int(profile["orders"] > 1)
        bucket["revenue_cents"] += profile["revenue_cents"]

    final_metrics = groups["all"]["all"]
    all_totals = empty_metrics()
    for month in months:
        for name in ZERO_METRICS:
            all_totals[name] += final_metrics.get(month, empty_metrics())[name]
    all_totals["buyers"] = len(buyer_profiles)

    delivery_by_seller: dict[str, set[str]] = seller_orders
    public_sellers = []
    for seller_id, metrics in seller_metrics.items():
        delivered_count = 0
        late_count = 0
        for order_id in delivery_by_seller[seller_id]:
            order = orders[order_id]
            if (
                order["status"] == "delivered"
                and order["delivered_at"]
                and order["estimated_at"]
            ):
                delivered_count += 1
                late_count += int(order["delivered_at"] > order["estimated_at"])
        late_rate = late_count / delivered_count if delivered_count else None
        average_score = (
            metrics["review_score_sum"] / metrics["review_count"]
            if metrics["review_count"]
            else None
        )
        if delivered_count < 10:
            risk = "Low sample"
        elif (late_rate is not None and late_rate > 0.2) or (
            average_score is not None and average_score <= 3.5
        ):
            risk = "High"
        elif (late_rate is not None and late_rate > 0.1) or (
            average_score is not None and average_score < 4
        ):
            risk = "Watch"
        else:
            risk = "Normal"
        public_sellers.append(
            {
                "seller_id": seller_id,
                "orders": len(metrics["orders"]),
                "items": metrics["items"],
                "revenue_cents": metrics["revenue_cents"],
                "delivered_orders": delivered_count,
                "late_orders": late_count,
                "late_rate": late_rate,
                "average_review_score": average_score,
                "risk": risk,
            }
        )
    public_sellers.sort(
        key=lambda seller: (
            {"High": 0, "Watch": 1, "Normal": 2, "Low sample": 3}[seller["risk"]],
            -(seller["late_rate"] or 0),
            seller["seller_id"],
        )
    )

    return {
        "source": "Brazilian E-Commerce Public Dataset by Olist",
        "source_url": "https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce",
        "license": "CC BY-NC-SA 4.0",
        "period": {"start": months[0], "end": months[-1], "months": months},
        "totals": all_totals,
        "monthly": public_series(months, groups["all"]["all"]),
        "cities": public_cities,
        "states": public_states,
        "categories": public_categories,
        "payments": public_payments,
        "rfm": {
            "as_of": reference_at.date().isoformat(),
            "cutoffs": {
                "recency_days": recency_cutoffs,
                "frequency_orders": frequency_cutoffs,
                "monetary_cents": monetary_cutoffs,
            },
            "segments": [
                {"name": name, **values}
                for name, values in sorted(rfm_segments.items())
            ],
        },
        "aov_buckets": [
            {"name": name, **values}
            for name, values in aov_buckets.items()
        ],
        "sellers": public_sellers,
    }


def main() -> None:
    data = build_dashboard_data()
    city_data = {
        "period": data["period"],
        "cities": data.pop("cities"),
    }
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(data, ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    CITY_OUTPUT_PATH.write_text(
        json.dumps(city_data, ensure_ascii=False, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote business analytics to {OUTPUT_PATH}")
    print(f"Wrote city details to {CITY_OUTPUT_PATH}")


if __name__ == "__main__":
    main()
