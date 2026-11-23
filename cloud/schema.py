"""
Names, types and views of the BigQuery tables.

Datasets (same European region as the bucket):
    fuel_curated      vehicles: one row per vehicle (private, with restricted permissions)
    fuel_aggregated   stock_activity, stock_by_manufacturing_year, stock_by_registration_year
                      and the views copert_stock_activity and leap_stock_activity (the only ones to share)
All the tables have the columns snapshot_date (date of the extraction of the register, partition of the table) and
study_year.
"""
import re
import unicodedata

import pandas as pd

# BigQuery types of the aggregated tables, by the name of the column in the csv file written by the stage calculate
AGGREGATED_SCHEMAS = {
    'stock_activity': {
        'snapshot_date': 'DATE', 'study_year': 'INT64',
        'Category': 'STRING', 'Fuel': 'STRING', 'Segment': 'STRING', 'Euro Standard': 'STRING',
        'Stock': 'INT64', 'Mileage_between_itv_km_sum': 'FLOAT64',
        'Mean_Activity': 'INT64', 'Min_Activity': 'INT64', 'Max_Activity': 'INT64', 'Std_Activity': 'INT64',
        'Mean_Lifetime_Activity': 'INT64', 'Activity_Grouping': 'STRING',
    },
    'stock_by_manufacturing_year': {
        'snapshot_date': 'DATE', 'study_year': 'INT64',
        'Category': 'STRING', 'Fuel': 'STRING', 'Segment': 'STRING', 'ANY_FABRICACIO': 'INT64', 'Stock': 'INT64',
    },
    'stock_by_registration_year': {
        'snapshot_date': 'DATE', 'study_year': 'INT64',
        'Category': 'STRING', 'Fuel': 'STRING', 'Segment': 'STRING', 'ANY_ALTA': 'INT64', 'Stock': 'INT64',
    },
}


def to_snake_case(name: str) -> str:
    """
    Name of a column in BigQuery: lowercase ASCII with underscores.
    Ex: 'Euro Standard' -> 'euro_standard', 'Lifetime Activity' -> 'lifetime_activity',
        'PES_TOTAL_MÀXIM' -> 'pes_total_maxim'
    """
    ascii_name = unicodedata.normalize('NFKD', str(name)).encode('ascii', 'ignore').decode('ascii')
    return re.sub(r'[^0-9a-zA-Z]+', '_', ascii_name).strip('_').lower()


def bigquery_type(dtype, column_name: str = '') -> str:
    """BigQuery type of the dtype of a column of a dataframe (DATA_* columns are dates)"""
    if pd.api.types.is_datetime64_any_dtype(dtype):
        return 'DATE'
    if pd.api.types.is_bool_dtype(dtype):
        return 'BOOL'
    if pd.api.types.is_integer_dtype(dtype):
        return 'INT64'
    if pd.api.types.is_float_dtype(dtype):
        return 'FLOAT64'
    return 'STRING'


def curated_schema(vehicles_df: pd.DataFrame) -> dict:
    """Types of the columns of the table of vehicles (original column name -> BigQuery type)"""
    schema = {column: bigquery_type(dtype, column) for column, dtype in vehicles_df.dtypes.items()}
    schema['snapshot_date'] = 'DATE'
    schema['study_year'] = 'INT64'
    return schema


def snake_case_schema(schema: dict) -> dict:
    """The same schema with the names of the columns in snake_case. Two columns cannot have the same name"""
    result = {to_snake_case(column): type_ for column, type_ in schema.items()}
    if len(result) != len(schema):
        raise ValueError('Two columns have the same name in snake_case')
    return result


def copert_view_sql(project: str, dataset: str) -> str:
    """
    View with the names that COPERT uses (same as exports/copert): LPG Bifuel, segment "-" and Euro Standard empty when
    there is none. Off Road and electric motorcycles, that COPERT does not cover, are left out.
    """
    return f"""
CREATE OR REPLACE VIEW `{project}.{dataset}.copert_stock_activity` AS
SELECT snapshot_date, study_year,
       category AS Category,
       IF(fuel = 'LPG Bi-fuel', 'LPG Bifuel', fuel) AS Fuel,
       IFNULL(segment, '-') AS Segment,
       IFNULL(euro_standard, '') AS `Euro Standard`,
       stock AS Stock, mean_activity AS Mean_Activity, mean_lifetime_activity AS Mean_Lifetime_Activity
FROM `{project}.{dataset}.stock_activity`
WHERE category != 'Off Road' AND NOT (category = 'L-Category' AND fuel = 'Battery electric')
"""


def leap_view_sql(project: str, dataset: str) -> str:
    """View with the stock and the mean activity per branch of LEAP (Category\\Fuel\\Segment, names with underscore)"""
    return f"""
CREATE OR REPLACE VIEW `{project}.{dataset}.leap_stock_activity` AS
SELECT snapshot_date, study_year,
       CONCAT(REPLACE(category, '-', '_'), '\\\\', fuel, '\\\\', REPLACE(IFNULL(segment, ''), '-', '_')) AS branch,
       SUM(stock) AS stock,
       SAFE_DIVIDE(SUM(stock * mean_activity), SUM(stock)) AS mean_activity
FROM `{project}.{dataset}.stock_activity`
GROUP BY snapshot_date, study_year, branch
"""
