import logging

import pandas as pd

logger = logging.getLogger('logger' + '.type_conversion')

ACTIVITY_STATISTICS_COLUMNS = ['Mean_Activity', 'Min_Activity', 'Max_Activity', 'Std_Activity', 'Mean_Lifetime_Activity']


def convert_to_integer_df_columns(stock_and_mileage_df: pd.DataFrame):
    """
    Convert to integer (nullable Int64) the activity statistics columns of the stock and mileage dataframe.
    Values that could not be calculated are kept as null, they are not replaced by 0, and the number of them is logged.
    """
    for column in ACTIVITY_STATISTICS_COLUMNS:
        values = pd.to_numeric(stock_and_mileage_df[column], errors='coerce')
        number_of_nulls = int(values.isna().sum())
        if number_of_nulls > 0:
            logger.warning(f'Check for nan values in the stock_and_mileage dataframe: {column}. '
                           f'Number of categories with no value: {number_of_nulls}')
        stock_and_mileage_df[column] = values.round().astype('Int64')
