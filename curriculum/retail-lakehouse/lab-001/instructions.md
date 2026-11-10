# LAB-001: Build and Test a Retail Customer Staging Model

The table `raw_customers` holds 5 customer records. The data is not clean:
some values have spaces at the start or the end, and the letter case is not
consistent.

## Your task

Complete `models/staging/stg_customers.sql`. The model must return these
columns, in this order:

| Column | Rule |
|---|---|
| `customer_key` | `customer_id` cast to `bigint` |
| `customer_name` | spaces removed from the start and the end |
| `email` | spaces removed, lowercase |
| `country` | spaces removed, uppercase |
| `processed_at` | the current timestamp |

Read the data with `{{ source('retail_raw', 'raw_customers') }}`.

## Rules

- You can use `source()` and `ref()` only. Other Jinja is rejected.
- Select **Build and test** to run the model and the tests.
- You pass at a score of 80 or more, with all critical checks passed.
