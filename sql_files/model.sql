{{ config(materialized='table') }}

-- Table: Emp2
WITH source_data AS (
    SELECT *
    FROM {{ source('raw', 'emp2') }}
)

SELECT
    Emp_id,
    Name,
    Address
FROM source_data