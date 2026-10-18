import os
import random
import numpy as np
import pandas as pd
from faker import Faker

# Initialize Faker and seed for reproducibility
fake = Faker()
Faker.seed(42)
np.random.seed(42)
random.seed(42)

# Ensure output directory exists
OUTPUT_DIR = "../data/raw"
os.makedirs(OUTPUT_DIR, exist_ok=True)

NUM_CUSTOMERS = 1500
NUM_PRODUCTS = 120
NUM_TRANSACTIONS = 125000

print("Generating synthetic enterprise dataset with deliberate real-world flaws...")

# ---------------------------------------------------------
# 1. DimCustomer (Messy text, casing, extra spaces)
# ---------------------------------------------------------
customer_ids = [f"CUST-{1000 + i}" for i in range(NUM_CUSTOMERS)]

casing_variations = [
    lambda x: x.upper(),
    lambda x: x.lower(),
    lambda x: f"  {x}   ",
    lambda x: x.title(),
]

customers = []
for cid in customer_ids:
    raw_name = fake.name()
    # Intentionally mess up formatting for Power Query cleaning practice
    formatted_name = random.choice(casing_variations)(raw_name)

    country = random.choice(
        ["Lebanon", "United States", "UAE", "France", "Germany", "Saudi Arabia"]
    )
    city = fake.city()

    customers.append(
        {
            "CustomerID": cid,
            "CustomerName": formatted_name,
            "Country": country,
            "City": city,
            "SignupDate": fake.date_between(
                start_date="-3y", end_date="today"
            ).strftime("%Y-%m-%d"),
        }
    )

df_customers = pd.DataFrame(customers)
# Inject 2% duplicate rows to simulate CRM pipeline errors
df_customers = pd.concat(
    [df_customers, df_customers.sample(frac=0.02)], ignore_index=True
)
df_customers.to_csv(f"{OUTPUT_DIR}/raw_customers.csv", index=False)
print("✔ Saved raw_customers.csv")

# ---------------------------------------------------------
# 2. DimProduct (Inconsistent weight units, messy carriers)
# ---------------------------------------------------------
product_categories = ["Electronics", "Home & Office", "Apparel", "Industrial"]
raw_brands = [
    "msc",
    "MSC Logistics",
    "Air",
    "Air Freight",
    "DHL Express",
    "dhl",
    "FedEx Corp",
    "fedex",
]

products = []
for i in range(1, NUM_PRODUCTS + 1):
    pid = f"PROD-{5000 + i}"
    category = random.choice(product_categories)

    # Mixed weight units (kg, g, lbs)
    weight_val = round(random.uniform(0.1, 25.0), 2)
    unit = random.choice(["kg", "KG", "g", "Grams", "lbs", "LBS"])
    weight_str = f"{weight_val} {unit}"

    carrier = random.choice(raw_brands)
    base_price = round(random.uniform(10.0, 850.0), 2)

    products.append(
        {
            "ProductID": pid,
            "ProductName": f"Item {fake.word().title()} {i}",
            "Category": category,
            "Weight": weight_str,
            "PrimaryCarrier": carrier,
            "UnitPriceUSD": base_price,
        }
    )

df_products = pd.DataFrame(products)
df_products.to_csv(f"{OUTPUT_DIR}/raw_products.csv", index=False)
print("✔ Saved raw_products.csv")

# ---------------------------------------------------------
# 3. DimFX (Exchange rates for multi-currency handling)
# ---------------------------------------------------------
dates = pd.date_range(start="2024-01-01", end="2026-10-01", freq="D")
fx_records = []

for d in dates:
    date_str = d.strftime("%Y-%m-%d")
    # Base USD = 1.0
    fx_records.append({"Date": date_str, "Currency": "USD", "RateToUSD": 1.0})
    # EUR fluctuating around 0.92
    fx_records.append(
        {
            "Date": date_str,
            "Currency": "EUR",
            "RateToUSD": round(np.random.normal(0.92, 0.02), 4),
        }
    )
    # LBP parallel vs official rate simulation
    fx_records.append(
        {
            "Date": date_str,
            "Currency": "LBP",
            "RateToUSD": round(np.random.normal(89500, 500), 2),
        }
    )
    # AED pegged around 3.67
    fx_records.append(
        {
            "Date": date_str,
            "Currency": "AED",
            "RateToUSD": round(np.random.normal(3.67, 0.01), 4),
        }
    )

df_fx = pd.DataFrame(fx_records)
df_fx.to_csv(f"{OUTPUT_DIR}/raw_fx_rates.csv", index=False)
print("✔ Saved raw_fx_rates.csv")

# ---------------------------------------------------------
# 4. FactSales (Inconsistent date formats, dynamic currencies)
# ---------------------------------------------------------
dates_list = pd.date_range(start="2024-01-01", end="2026-09-30", freq="D")

# Inconsistent date string formats
date_formatters = [
    lambda d: d.strftime("%Y-%m-%d"),
    lambda d: d.strftime("%m/%d/%Y"),
    lambda d: d.strftime("%d-%b-%Y"),
    lambda d: d.strftime("%Y/%m/%d"),
]

sales = []
for i in range(1, NUM_TRANSACTIONS + 1):
    trans_id = f"TRX-{100000 + i}"
    raw_date = random.choice(dates_list)
    formatted_date = random.choice(date_formatters)(raw_date)

    cust_id = random.choice(customer_ids)
    prod_id = f"PROD-{random.randint(5001, 5000 + NUM_PRODUCTS)}"
    quantity = random.randint(1, 15)

    currency = random.choices(
        ["USD", "EUR", "LBP", "AED"], weights=[0.55, 0.20, 0.15, 0.10]
    )[0]
    channel = random.choice(
        ["Online Web", "Mobile App", "Retail Store", "Distributor"]
    )

    # Unit price based roughly on base currency with variations
    base_price = round(random.uniform(15.0, 500.0), 2)
    if currency == "LBP":
        unit_price = base_price * 89500
    elif currency == "EUR":
        unit_price = base_price * 0.92
    elif currency == "AED":
        unit_price = base_price * 3.67
    else:
        unit_price = base_price

    sales.append(
        {
            "TransactionID": trans_id,
            "TransactionDate": formatted_date,
            "CustomerID": cust_id,
            "ProductID": prod_id,
            "Channel": channel,
            "Currency": currency,
            "Quantity": quantity,
            "UnitPrice": round(unit_price, 2),
            "Discount": round(random.choice([0.0, 0.05, 0.10, 0.15, 0.20]), 2),
        }
    )

df_sales = pd.DataFrame(sales)

# Inject nulls in CustomerID (1% of transactions) to simulate missing records
df_sales.loc[df_sales.sample(frac=0.01).index, "CustomerID"] = np.nan

df_sales.to_csv(f"{OUTPUT_DIR}/raw_sales_transactions.csv", index=False)
print("✔ Saved raw_sales_transactions.csv")

print("\n--- All Raw Datasets Successfully Generated! ---")