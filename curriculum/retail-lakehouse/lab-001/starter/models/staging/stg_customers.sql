-- Complete this model. See the instructions for the column rules.
with source_data as (
    select
        customer_id,
        customer_name,
        email,
        country
    from {{ source('retail_raw', 'raw_customers') }}
)
select
    customer_id as customer_key,
    customer_name,
    email,
    country
from source_data
