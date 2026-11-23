from datetime import datetime
import pandas as pd
import logging


info_logger = logging.getLogger('info_logger' + '.Filters')


def filter_by_year_greater_or_equal_than(registre_df: pd.DataFrame, colname: str, date) -> pd.DataFrame:
    return registre_df[registre_df[colname] >= date]


def keep_row_if_na_in_column(registre_df: pd.DataFrame, colname: str) -> pd.DataFrame:
    return registre_df[registre_df[colname].isna()]


def drop_agricultural_vehicles(registre_df: pd.DataFrame) -> pd.DataFrame:
    num_agricultural_vehicles = registre_df[registre_df.CARBURANT == 'SENSE CARBURANT'].shape[0]
    info_logger.info(f'Total number of agricultural vehicles deleted: {num_agricultural_vehicles}')
    return registre_df[registre_df['TIPUS'] != 'VEHICLES AGRICOLS']


def drop_vehicles_with_no_fuel_associated(registre_df: pd.DataFrame) -> pd.DataFrame:
    num_vehicles_no_fuel = registre_df[registre_df.CARBURANT == 'SENSE CARBURANT'].shape[0]
    info_logger.info(f'Total number of vehicles with no fuel associated deleted: {num_vehicles_no_fuel}')
    return registre_df[registre_df['CARBURANT'] != 'SENSE CARBURANT']


def filter_by_year_smaller_than(registre_df: pd.DataFrame, colname: str, date) -> pd.DataFrame:
    return registre_df[(registre_df[colname] < date) | (registre_df[colname].isna())]


def filter_fleet_stock_at_reference_date(register_df: pd.DataFrame, reference_date: datetime, min_year: int,
                                         max_year: int, snapshot_date: datetime = None) -> pd.DataFrame:
    """
    Vehicles of the stock at the reference date (ex: 31/12 of the study year):
        - registered (DATA_ALTA) until the reference date
        - not decommissioned (DATA_BAIXA empty) or decommissioned after the reference date
        - year of manufacturing between min_year and max_year
        - with fuel (vehicles with fuel "SENSE CARBURANT" are dropped)
    The number of vehicles after each filter is logged.

    :param register_df: itv register dataframe
    :param reference_date: date of the stock
    :param min_year: minimum year of manufacturing
    :param max_year: maximum year of manufacturing
    :param snapshot_date: date of the extraction of the register, to log the vehicles with a later registration date
    """
    info_logger.info(f'Total number of vehicles loaded: {register_df.shape[0]}')
    if snapshot_date is not None:
        number_of_later_registrations = register_df[register_df['DATA_ALTA'] > snapshot_date].shape[0]
        info_logger.info(f'Number of vehicles with registration date after the extraction of the register '
                         f'({snapshot_date.date()}): {number_of_later_registrations}')

    df = register_df[(register_df['ANY_FABRICACIO'] >= min_year) & (register_df['ANY_FABRICACIO'] <= max_year)]
    info_logger.info(f'Number of vehicles manufactured between {min_year} and {max_year}: {df.shape[0]}')

    df = df[df['DATA_ALTA'] <= reference_date]
    info_logger.info(f'Number of vehicles registered until {reference_date.date()}: {df.shape[0]}')

    df = df[df['DATA_BAIXA'].isna() | (df['DATA_BAIXA'] > reference_date)]
    info_logger.info(f'Number of vehicles not decommissioned at {reference_date.date()}: {df.shape[0]}')

    df = drop_vehicles_with_no_fuel_associated(df)
    info_logger.info(f'Total number of vehicles of the stock at {reference_date.date()}: {df.shape[0]}')
    return df


def filter_by_partitions(df: pd.DataFrame, category=None, fuel=None, segment=None, euro=None):
    """
    Filters the groupby dataframe to match the values of the given partitions
    """
    filtered_groupby = df.copy()
    if euro:
        filtered_groupby = filtered_groupby[(filtered_groupby['Euro Standard'] == euro)]
    if category:
        filtered_groupby = filtered_groupby[(filtered_groupby['Category'] == category)]
    if segment:
        filtered_groupby = filtered_groupby[(filtered_groupby['Segment'] == segment)]
    if fuel:
        filtered_groupby = filtered_groupby[(filtered_groupby['Fuel'] == fuel)]

    return filtered_groupby
