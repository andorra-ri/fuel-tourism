from typing import List
import pandas as pd
import logging

logger = logging.getLogger('logger' + '.AggregationFunctions')


def groupby_partitions(vehicles_df: pd.DataFrame, partitions: List) -> pd.DataFrame.groupby:
    """
    Group the vehicles register Dataframe into the given partitions
    Calculates the sum for the column Stock (number of vehicles in the given aggregation)
    Calculates the Mean of the column Activity for the given aggregation

    :param vehicles_df: with columns: ['Category', 'Fuel', 'Segment', 'Euro Standard', 'Num_of_days', 'Mileage',
     'Activity', 'Stock']
    :param partitions: must be one or more of :  ['Category', 'Fuel', 'Segment', 'Euro Standard']
    :return: grouped pd.Dataframe for the given partitions
    """
    try:
        groupby = vehicles_df.groupby(
            partitions, dropna=False, as_index=False).agg(
            Stock=('Stock', 'sum'),
            Mileage=('Mileage', 'sum'),
            Min_Activity=('Activity', 'min'),
            Max_Activity=('Activity', 'max'),
            Std_Activity=('Activity', 'std'),
            Mean_Activity=('Activity', 'mean'),
            Mean_Lifetime_Activity=('Lifetime Activity', 'mean'),
            Notna_Count=('Activity', 'count')
        )

    except Exception:
        logger.error(f'Unable to groupby {partitions}, the vehicles dataframe', exc_info=True)

    return groupby


def filter_groupby_partitions(groupby: pd.DataFrame.groupby, row: pd.Series, euro_standard: str, fuel_type: str) \
        -> pd.DataFrame.groupby:
    """
    Filters the groupby dataframe to match the values of the given row for the partitions:
    :param groupby: original dataframe
    :param row: row of the vehicles dataframe
    :param euro_standard: Value of the second last Euro Standard for the row(vehicle) Category
    :param fuel_type: fuel type to take into account for filtering (Hybrid types)
    :return: Groupby with matching values for the given partitions
    """
    partitions = groupby.columns.tolist()
    filtered_groupby = groupby.copy()
    if 'Euro Standard' in partitions:
        filtered_groupby = filtered_groupby[(filtered_groupby['Euro Standard'] == euro_standard)]
    if 'Category' in partitions:
        filtered_groupby = filtered_groupby[(filtered_groupby['Category'] == row['Category'])]
    if 'Segment' in partitions:
        filtered_groupby = filtered_groupby[(filtered_groupby['Segment'] == row['Segment'])]
    if 'Fuel' in partitions:
        filtered_groupby = filtered_groupby[(filtered_groupby['Fuel'] == fuel_type)]

    return filtered_groupby
