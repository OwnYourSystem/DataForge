with source_data as (
    select
        customer_id,
        customer_name,
        email,
        country
    from {{ source('retail_raw', 'raw_customers') }}
),
cleaned as (
    select
        cast(customer_id as bigint) as customer_key,
        trim(customer_name) as customer_name,
        lower(trim(email)) as email,
        upper(trim(country)) as country,
        current_timestamp as processed_at
    from source_data
)
select *
from cleaned
