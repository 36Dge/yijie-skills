# CSV Schema Definitions

Both CSVs are MANDATORY deliverables. Do NOT merge them. Do NOT skip either one.

## `final_recommendations.csv`

| Column | Description | Required |
|--------|-------------|----------|
| asin | Amazon Standard Identification Number | ✅ |
| title | Product title | ✅ |
| brand | Brand name | ✅ |
| price | Current listing price (USD) | ✅ |
| sales_cnt_30d | Estimated units sold in last 30 days | ✅ |
| rating | Average star rating (e.g., 4.5) | ✅ **MUST fill** |
| reviews | Total review count (e.g., 1234) | ✅ **MUST fill** |
| net_margin_pct | Estimated net margin percentage | ✅ |
| prodUrl | `https://www.amazon.com/dp/{asin}` | ✅ |
| imageUrl | Product image URL | ✅ |
| recommendation_source | One of: `analysis-driven`, `data-filtered`, `search` | ✅ |
| recommendation_reason | Why this product was recommended (dimension conclusion / filter strategy / search keyword) | ✅ |
| reference_id | Reference ID from `info_search` shopping results. Used for product display tags in report (per `<markdown_formatting_protocol>`). Empty for products not found in shopping search. | ⚠️ Fill when available |

⚠️ Every row MUST have all columns filled. Do NOT leave rating/reviews empty.

## `alibaba_supply.csv`

| Column | Description | Required |
|--------|-------------|----------|
| title | Product title on Alibaba | ✅ |
| supplier_name | Supplier/manufacturer name | ✅ |
| price_min | Minimum unit price (USD) | ✅ |
| price_max | Maximum unit price (USD) | ✅ |
| moq | Minimum order quantity | ✅ |
| supplier_rating | Supplier rating/score | ✅ |
| url | Product page URL on Alibaba | ✅ |
| reference_id | Reference ID from `product_supplier_search`. Used for product display tags in Section 7 (per `<markdown_formatting_protocol>`). | ⚠️ Fill when available |

