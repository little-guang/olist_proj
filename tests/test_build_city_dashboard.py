import unittest
from unittest.mock import patch

from scripts import build_city_dashboard


class BuildDashboardDataTests(unittest.TestCase):
    def test_business_totals_and_breakdowns_reconcile(self):
        tables = {
            "customers_clean.csv": [
                {
                    "customer_id": "c1",
                    "customer_unique_id": "buyer-a",
                    "customer_city": "City A",
                    "customer_state": "sp",
                },
                {
                    "customer_id": "c2",
                    "customer_unique_id": "buyer-a",
                    "customer_city": "City A",
                    "customer_state": "SP",
                },
                {
                    "customer_id": "c3",
                    "customer_unique_id": "buyer-b",
                    "customer_city": "City B",
                    "customer_state": "RJ",
                },
            ],
            "category_translation_clean.csv": [
                {
                    "product_category_name": "cat",
                    "product_category_name_english": "category_en",
                },
            ],
            "products_clean.csv": [
                {"product_id": "p1", "product_category_name": "cat"},
                {"product_id": "p2", "product_category_name": "unknown"},
            ],
            "sellers_clean.csv": [
                {"seller_id": "s1", "seller_state": "SP"},
                {"seller_id": "s2", "seller_state": "RJ"},
            ],
            "orders_clean.csv": [
                {
                    "order_id": "o1",
                    "customer_id": "c1",
                    "order_purchase_timestamp": "2020-01-10 10:00:00",
                    "order_approved_at": "2020-01-10 12:00:00",
                    "order_delivered_carrier_date": "2020-01-10 18:00:00",
                    "order_status": "delivered",
                    "order_delivered_customer_date": "2020-01-11 10:00:00",
                    "order_estimated_delivery_date": "2020-01-12 00:00:00",
                },
                {
                    "order_id": "o2",
                    "customer_id": "c2",
                    "order_purchase_timestamp": "2020-03-10 10:00:00",
                    "order_approved_at": "2020-03-10 11:00:00",
                    "order_delivered_carrier_date": "2020-03-10 12:00:00",
                    "order_status": "delivered",
                    "order_delivered_customer_date": "2020-03-15 10:00:00",
                    "order_estimated_delivery_date": "2020-03-12 00:00:00",
                },
                {
                    "order_id": "o3",
                    "customer_id": "c3",
                    "order_purchase_timestamp": "2020-03-20 10:00:00",
                    "order_approved_at": "",
                    "order_delivered_carrier_date": "",
                    "order_status": "processing",
                    "order_delivered_customer_date": "",
                    "order_estimated_delivery_date": "",
                },
            ],
            "order_items_clean.csv": [
                {
                    "order_id": "o1",
                    "product_id": "p1",
                    "seller_id": "s1",
                    "price": "10.00",
                    "freight_value": "2.00",
                },
                {
                    "order_id": "o1",
                    "product_id": "p2",
                    "seller_id": "s1",
                    "price": "5.00",
                    "freight_value": "1.00",
                },
                {
                    "order_id": "o2",
                    "product_id": "p1",
                    "seller_id": "s2",
                    "price": "100.00",
                    "freight_value": "20.00",
                },
                {
                    "order_id": "o3",
                    "product_id": "p2",
                    "seller_id": "s2",
                    "price": "200.00",
                    "freight_value": "40.00",
                },
            ],
            "order_reviews_clean.csv": [
                {"order_id": "o1", "review_score": "2"},
                {"order_id": "o2", "review_score": "5"},
                {"order_id": "o3", "review_score": "1"},
            ],
            "order_payments_clean.csv": [
                {
                    "order_id": "o1",
                    "payment_type": "credit_card",
                    "payment_value": "17.00",
                    "payment_installments": "1",
                },
                {
                    "order_id": "o2",
                    "payment_type": "boleto",
                    "payment_value": "120.00",
                    "payment_installments": "3",
                },
                {
                    "order_id": "o3",
                    "payment_type": "credit_card",
                    "payment_value": "240.00",
                    "payment_installments": "1",
                },
                {
                    "order_id": "o3",
                    "payment_type": "not_defined",
                    "payment_value": "0.00",
                    "payment_installments": "1",
                },
            ],
        }

        with patch.object(
            build_city_dashboard,
            "read_csv",
            side_effect=lambda file_name: iter(tables[file_name]),
        ):
            result = build_city_dashboard.build_dashboard_data()

        self.assertEqual(result["period"]["months"], ["2020-01", "2020-02", "2020-03"])
        self.assertEqual(result["totals"]["orders"], 3)
        self.assertEqual(result["totals"]["items"], 4)
        self.assertEqual(result["totals"]["revenue_cents"], 31_500)
        self.assertEqual(result["totals"]["freight_cents"], 6_300)
        self.assertEqual(result["totals"]["new_buyers"], 2)
        self.assertEqual(result["totals"]["buyers"], 2)
        self.assertEqual(result["totals"]["delivered"], 2)
        self.assertEqual(result["totals"]["on_time"], 1)
        self.assertEqual(result["totals"]["delayed"], 1)
        self.assertEqual(result["totals"]["undelivered"], 1)
        self.assertEqual(result["totals"]["payment_cents"], 37_700)

        price_freight = result["price_freight_analysis"]
        self.assertEqual(len(price_freight["segments"]), 4)
        segment_by_key = {
            segment["key"]: segment for segment in price_freight["segments"]
        }
        self.assertEqual(
            sum(row["items"] for row in segment_by_key["low_price_low_freight"]["series"]),
            2,
        )
        self.assertEqual(
            sum(row["orders"] for row in segment_by_key["low_price_low_freight"]["series"]),
            1,
        )
        self.assertEqual(
            sum(row["revenue_cents"] for row in segment_by_key["high_price_high_freight"]["series"]),
            30_000,
        )

        geography = result["geography_analysis"]
        state_by_code = {state["state"]: state for state in geography["states"]}
        self.assertEqual(geography["same_state_item_share"], 0.75)
        self.assertEqual(geography["cross_state_item_share"], 0.25)
        self.assertEqual(state_by_code["SP"]["orders"], 2)
        self.assertEqual(state_by_code["SP"]["customers"], 1)
        self.assertEqual(state_by_code["SP"]["active_sellers"], 1)

        demand = {row["month"]: row for row in result["demand"]["months"]}
        self.assertEqual(demand["2020-01"]["hours"][10], 1)
        self.assertEqual(demand["2020-02"]["hours"], [0] * 24)
        self.assertEqual(demand["2020-03"]["hours"][10], 2)
        self.assertEqual(demand["2020-01"]["weekdays"][4], 1)
        self.assertEqual(demand["2020-03"]["weekdays"][1], 1)
        self.assertEqual(demand["2020-03"]["weekdays"][4], 1)

        delivery = {row["month"]: row for row in result["delivery_analysis"]}
        self.assertEqual(delivery["2020-01"]["duration_buckets"][0]["review_count"], 1)
        self.assertEqual(delivery["2020-01"]["duration_buckets"][0]["review_score_sum"], 2)
        self.assertEqual(delivery["2020-01"]["delay_buckets"][0]["key"], "on_time")
        self.assertEqual(delivery["2020-01"]["delay_buckets"][0]["low_review_count"], 1)
        march_delay = next(
            item for item in delivery["2020-03"]["delay_buckets"]
            if item["key"] == "late_4_7"
        )
        self.assertEqual(march_delay["orders"], 1)
        self.assertEqual(march_delay["review_score_sum"], 5)
        self.assertEqual(
            delivery["2020-01"]["stages"]["purchase_to_approval"]["low_review_hours"],
            2,
        )
        self.assertEqual(delivery["2020-03"]["correlation"]["count"], 1)

        monthly = {row["month"]: row for row in result["monthly"]}
        self.assertEqual(monthly["2020-02"].get("buyers", 0), 0)
        self.assertEqual(monthly["2020-02"].get("orders", 0), 0)
        self.assertEqual(monthly["2020-03"]["buyers"], 2)
        self.assertEqual(monthly["2020-03"]["new_buyers"], 1)
        self.assertEqual(monthly["2020-03"]["delayed"], 1)

        category_totals = {
            category["name"]: sum(row.get("revenue_cents", 0) for row in category["series"])
            for category in result["categories"]
        }
        self.assertEqual(category_totals["category_en"], 11_000)
        self.assertEqual(category_totals["unknown"], 20_500)
        self.assertEqual(sum(category_totals.values()), result["totals"]["revenue_cents"])

        payment_total = sum(
            row.get("payment_cents", 0)
            for payment in result["payments"]
            for row in payment["series"]
        )
        self.assertEqual(payment_total, result["totals"]["payment_cents"])
        not_defined = next(
            payment for payment in result["payments"] if payment["type"] == "not_defined"
        )
        self.assertEqual(
            sum(row.get("payment_count", 0) for row in not_defined["series"]),
            1,
        )
        self.assertTrue(
            all("payment_cents" not in row for row in not_defined["series"])
        )

        rfm_buyers = sum(segment["customers"] for segment in result["rfm"]["segments"])
        rfm_repeat_buyers = sum(
            segment["repeat_customers"] for segment in result["rfm"]["segments"]
        )
        self.assertEqual(rfm_buyers, 2)
        self.assertEqual(rfm_repeat_buyers, 1)


if __name__ == "__main__":
    unittest.main()
