# Global Omnichannel Retail Analytics (Power BI)

## Executive Summary
An enterprise-grade Power BI business intelligence solution designed to analyze multi-currency retail transactions, shipping logistics performance, and customer acquisition metrics across global markets (including MENA regional dynamics). 

The project transforms raw, unstructured multi-source data into an optimized, star-schema-backed analytical data model, leveraging upstream Power Query ETL workflows and dynamic DAX Time Intelligence calculations.

---

## Technical Architecture & Workflow

### 1. Data Generation & Ingestion
- Raw data pipeline configured using a custom Python framework (`pandas` + `Faker`) generating 125,000+ transaction records.
- Stored as modular CSV source files in `data/raw/`:
  - `raw_customers.csv` (Customer profiles, geography, signup dates)
  - `raw_products.csv` (Product catalog, category hierarchies, physical weight attributes)
  - `raw_sales_transactions.csv` (Omnichannel order header and item data)
  - `raw_fx_rates.csv` (Daily foreign exchange spot rates for multi-currency conversion)

---

### 2. Upstream Data Transformation (Power Query / M)

All initial transformations were executed within Power Query to maximize storage compression and maintain Query Folding principles:

- **DimCustomer Optimization:**
  - Standardized customer naming via text casing (`Capitalize Each Word`) and string trimming (`Trim`).
  - Deduplicated primary keys (`CustomerID`) to eliminate pipeline error records and ensure `1:Many` referential integrity.
  - Formatted regional attributes (`Country`, `City`) to standard text data types.

- **DimProduct & Decoupled DimCarrier (3NF Normalization):**
  - Extracted shipping carrier details by creating an upstream `Reference` query off `DimProduct` to instantiate `DimCarrier`.
  - Normalized carrier naming variations using M conditional logic mapping (e.g., standardizing `msc`, `MSC`, `Air`, `dhl`, `FedEx` to explicit corporate brand names).
  - Cleaned and trimmed carrier entity keys to resolve duplicate primary key constraints (`1:Many` downstream routing).
  - Standardized heterogeneous product weights (`kg`, `g`, `grams`, `lbs`) into a unified metric column (`WeightInKG`) via custom M parsing.

- **FactSales Standardization & Multi-Currency Stamping:**
  - Resolved culture-specific string date variations by parsing `TransactionDate` through US Locale formatting (`en-US`).
  - Filtered missing/blank `CustomerID` records to eliminate orphan fact rows.
  - Performed a composite multi-column merge (`TransactionDate` + `Currency` = `Date` + `Currency`) against `DimFX` to stamp historical daily exchange rates (`RateToUSD`) directly onto line-item transactions.
  - Computed materialized net sales revenue in base currency (`SalesAmountUSD`) inside Power Query for optimal VertiPaq engine row-level compression:
    `SalesAmountUSD = ([Quantity] * [UnitPrice] * (1 - [Discount])) / [RateToUSD]`

- **Dynamic Calendar Generation (DimDate):**
  - Generated a programmatically continuous calendar table spanning 2024–2026 using native M code (`List.Dates`) to support downstream DAX Time Intelligence.
  - Included attributes for Year, Month Number, Month Name, Quarter, and integer join keys (`YearMonth`).

---

### 3. Data Modeling (Star Schema)

The analytical data model follows a strict Star Schema architecture centered around `FactSales`:

- **FactSales (Center):** Core transactional table containing granular line items, quantities, discounts, and revenue in USD.
- **DimCustomer ($1 \rightarrow *$ FactSales):** Customer demographics and location context.
- **DimDate ($1 \rightarrow *$ FactSales):** Continuous calendar table powering temporal aggregation.
- **DimCarrier ($1 \rightarrow *$ DimProduct):** Decoupled dimension handling carrier attributes.
- **DimProduct ($1 \rightarrow *$ FactSales):** Product catalog, attributes, and category hierarchies.
- **DimFX (Disconnected Reference):** Rates stamped directly into `FactSales` during ETL; no active model relationship required.

All relationships enforce single-direction cross-filtering (`1` on Dimension side to `*` on Fact side) to eliminate ambivalence and circular filter propagation.

---

### 4. Analytical Measures Portfolio (DAX)

Measures are isolated inside a dedicated `_Key Measures` table for optimal repository maintenance:

#### Base Core Metrics
- **Total Revenue (USD):**
  `Total Revenue USD = SUM(FactSales[SalesAmountUSD])`
- **Total Orders:**
  `Total Orders = DISTINCTCOUNT(FactSales[TransactionID])`
- **Total Units Sold:**
  `Total Units Sold = SUM(FactSales[Quantity])`
- **Average Order Value (AOV):**
  `Average Order Value = DIVIDE([Total Revenue USD], [Total Orders], 0)`

#### Time Intelligence & Year-over-Year Growth
- **Revenue Prior Year (PY):**
  `Revenue PY = CALCULATE([Total Revenue USD], SAMEPERIODLASTYEAR(DimDate[Date]))`
- **Year-over-Year Revenue Growth ($):**
  `YoY Revenue Growth = [Total Revenue USD] - [Revenue PY]`
- **Year-over-Year Revenue Growth (%):**
  `YoY Revenue Growth % = DIVIDE([YoY Revenue Growth], [Revenue PY], 0)`

---

## Repository Structure

├── Global_Omnichannel_Analytics.pbix  # Main Power BI Desktop File
├── README.md                           # Technical Documentation
├── requirements.txt                    # Environment dependencies
├── scripts/
│   └── generate_data.py               # Python mock data engine
└── data/
    └── raw/                            # Generated source CSVs
        ├── raw_customers.csv
        ├── raw_fx_rates.csv
        ├── raw_products.csv
        └── raw_sales_transactions.csv

## Next Steps for Future Iterations
1. **Report View & UI/UX Design:** Build executive dashboard pages (Sales Overview, Logistics & Carrier Performance, Regional & Currency Analysis).
2. **Advanced Analytics:** Implement customer cohort retention analysis and Dynamic Pareto (80/20 Rule) product categorization via DAX.