"""
Stage 1: calculation of the stock and the activity of the fleet.

Reads the Excel register of ITV and saves:
    curated/     one row per vehicle, classified, with its activity
    aggregated/  stock and activity per category, stock per year of manufacturing, stock per year of registration
    qa/          vehicles with erroneous data
    exports/     input files for COPERT
"""
import logging
from pathlib import Path
from types import SimpleNamespace

import pandas as pd

from activity import (
    activity_time_and_km_between_itv_revisions,
    check_for_activity_outliers,
    calculate_activity_outliers_thresholds,
    activity_stats_calculator_by_grouping
)
from classification import (
    category_fuel_segment_euro_classification_wrapper_function,
    MAPPING_CATEGORY_LAST_EURO_STANDARD
)
from data_cleaning import (
    filter_fleet_stock_at_reference_date,
    convert_to_integer_df_columns,
    print_info,
    save_to_csv_vehicles_with_erroneous_data
)
from ingestion import register_ingestor_function
from pipeline.paths import OutputPaths

logger = logging.getLogger('logger' + '.calculation')
info_logger = logging.getLogger('info_logger' + '.calculation')

PARTITIONS = ['Category', 'Fuel', 'Segment', 'Euro Standard']
ACTIVITY_COLUMNS = ['Mean_Activity', 'Min_Activity', 'Max_Activity', 'Std_Activity', 'Mean_Lifetime_Activity']
# Columns of the file with the stock and activity per category that are the input of COPERT
COPERT_COLUMNS = PARTITIONS + ['Stock', 'Mean_Activity', 'Mean_Lifetime_Activity']
# Stock configuration of COPERT for Andorra: the combinations Category, Fuel, Segment and Euro Standard it accepts
COPERT_STOCK_CONFIGURATION = Path(__file__).resolve().parent.parent / 'classification' / 'Stock_Configuration_Andorra.csv'
# Names that are different in COPERT
COPERT_FUEL_NAMES = {'LPG Bi-fuel': 'LPG Bifuel'}
# COPERT has no Diesel hybrid Passenger Cars: they are entered as Passenger Cars - Diesel (same Segment and Euro
# Standard), assuming that their emissions do not differ significantly from those of the comparable diesel vehicle
COPERT_FOLDED_FUELS = {('Passenger Cars', 'Diesel Hybrid'): 'Diesel'}


def add_snapshot_columns(df: pd.DataFrame, settings: SimpleNamespace) -> pd.DataFrame:
    """Add the columns that identify the extraction of the register and the year of the study to a table"""
    df = df.copy()
    df.insert(0, 'snapshot_date', settings.SNAPSHOT_DATE.date())
    df.insert(1, 'study_year', settings.STUDY_YEAR)
    return df


def classify_fleet(settings: SimpleNamespace, paths: OutputPaths):
    """Load the register, keep the stock of the reference date and classify it. Returns (vehicles, discarded cars)"""
    if not settings.path_registre_vehicles.exists() and settings.GCS_BUCKET:
        # Cloud execution: the original Excel is in the bucket (raw/<AAAAMMDD>/)
        from cloud.upload import download_raw_file
        download_raw_file(settings)
    itv_raw = register_ingestor_function(settings.path_registre_vehicles)
    stock_df = filter_fleet_stock_at_reference_date(
        itv_raw, settings.REFERENCE_DATE, settings.MIN_YEAR, settings.MAX_YEAR, settings.SNAPSHOT_DATE)
    return category_fuel_segment_euro_classification_wrapper_function(
        stock_df, random_seed=settings.SEGMENT_RANDOM_SEED, return_discarded=True)


def calculate_vehicles_activity(vehicles_df: pd.DataFrame, settings: SimpleNamespace) -> pd.DataFrame:
    """Add the columns Num_of_days, Mileage, Activity, Lifetime Activity, activity_method and itv_pairs_used"""
    # The covid period can be left out of the activity, without removing the vehicles from the stock
    max_date = settings.COVID_START_DATE if settings.COVID_MILEAGE_ACTIVE else settings.ACTIVITY_MAX_DATE

    result = vehicles_df.apply(
        lambda row: activity_time_and_km_between_itv_revisions(
            row, max_date, settings.MIN_DAYS_BETWEEN_REVISIONS, settings.USE_SINGLE_ITV), axis=1)
    df = vehicles_df.copy()
    (df['Num_of_days'], df['Mileage'], df['Activity'], df['Lifetime Activity'],
     df['activity_method'], df['itv_pairs_used']) = zip(*result)
    return df


def fold_fuels_not_in_copert(table: pd.DataFrame) -> pd.DataFrame:
    """
    Rename the fuels that COPERT does not have (COPERT_FOLDED_FUELS) to the one they are entered with, and add the rows
    that end up in the same Category, Fuel, Segment and Euro Standard: the Stock is added and the mean activities are
    the average weighted by the Stock (the total km do not change).
    """
    table = table.copy()
    changed = pd.Series(False, index=table.index)
    for (category, fuel), copert_fuel in COPERT_FOLDED_FUELS.items():
        mask = (table['Category'] == category) & (table['Fuel'] == fuel)
        table.loc[mask, 'Fuel'] = copert_fuel
        changed |= mask
    if not changed.any():
        return table

    mean_columns = ['Mean_Activity', 'Mean_Lifetime_Activity']
    grouped = table.groupby(PARTITIONS, as_index=False, dropna=False)
    result = grouped.agg(Stock=('Stock', 'sum'))
    for column in mean_columns:
        weights = table['Stock'].where(table[column].notna(), 0)
        weighted = (table['Stock'] * table[column]).where(table[column].notna(), 0)
        sums = pd.DataFrame({column: weighted, 'weight': weights, **{p: table[p] for p in PARTITIONS}}).groupby(
            PARTITIONS, as_index=False, dropna=False).sum()
        sums[column] = (sums[column] / sums['weight'].where(sums['weight'] > 0)).round().astype('Int64')
        result = result.merge(sums[PARTITIONS + [column]], on=PARTITIONS, how='left')
    return result[PARTITIONS + ['Stock'] + mean_columns]


def copert_stock_activity_table(stock_activity_df: pd.DataFrame, configuration_file=COPERT_STOCK_CONFIGURATION
                                ) -> pd.DataFrame:
    """
    Stock and activity with the names of COPERT. The categories that COPERT does not cover are left out: Off Road and
    electric motorcycles (their electricity demand is calculated apart for LEAP). The Segment of the vehicles with no
    segment is "-". The Diesel hybrid Passenger Cars are added to the Diesel ones (the stock is added and the mean
    activity is weighted by the stock). The combinations that are not in the stock configuration of COPERT are logged
    as a warning.
    """
    table = stock_activity_df.copy()
    not_covered = ((table['Category'] == 'Off Road') |
                   ((table['Category'] == 'L-Category') & (table['Fuel'] == 'Battery electric')))
    logger.info(f'Vehicles that COPERT does not cover, left out of its file: {int(table.loc[not_covered, "Stock"].sum())}')
    table = table[~not_covered].copy()
    table['Fuel'] = table['Fuel'].replace(COPERT_FUEL_NAMES)
    table['Segment'] = table['Segment'].fillna('-')
    table['Euro Standard'] = table['Euro Standard'].fillna('')
    table = fold_fuels_not_in_copert(table)

    if Path(configuration_file).exists():
        configuration = pd.read_csv(configuration_file, index_col=False).dropna(subset=['Category'])
        configuration = configuration[configuration['Include']].fillna({'Segment': '-', 'Euro Standard': ''})
        merged = table.merge(configuration[PARTITIONS].assign(in_configuration=True), on=PARTITIONS, how='left')
        missing = merged[merged['in_configuration'].isna()]
        if not missing.empty:
            logger.warning(f'Categories that are not in the stock configuration of COPERT: {missing.shape[0]}, with '
                           f'{int(missing["Stock"].sum())} vehicles: '
                           f'{missing[PARTITIONS + ["Stock"]].to_dict("records")}')
    return table[COPERT_COLUMNS]


def stock_by_year(vehicles_df: pd.DataFrame, year_column: str) -> pd.DataFrame:
    """Number of vehicles (Stock) per Category, Fuel, Segment and year"""
    df = vehicles_df.copy()
    if year_column == 'ANY_ALTA':
        df['ANY_ALTA'] = df['DATA_ALTA'].dt.year
    result = df.groupby(['Category', 'Fuel', 'Segment', year_column], dropna=False, as_index=False).agg(
        Stock=(year_column, 'count'))
    return result.sort_values(by=['Category', 'Fuel', 'Segment', year_column], ascending=True)


def stock_and_activity_per_category(vehicles_df: pd.DataFrame, settings: SimpleNamespace) -> pd.DataFrame:
    """Stock and activity statistics per Category, Fuel, Segment and Euro Standard"""
    df = vehicles_df.copy()
    df['Stock'] = 1

    stock_df = df.groupby(PARTITIONS, dropna=False, as_index=False).agg(Stock=('Stock', 'sum'))
    mileage_df = df.groupby(PARTITIONS, dropna=False, as_index=False).agg(
        Mileage=('Mileage', 'sum'),
        Min_Activity=('Activity', 'min'),
        Max_Activity=('Activity', 'max'),
        Std_Activity=('Activity', 'std'),
        Mean_Activity=('Activity', 'mean'),
        Mean_Lifetime_Activity=('Lifetime Activity', 'mean'),
        Notna_Count=('Activity', 'count')
    )

    # Join stock configuration with associated mileage
    stock_and_mileage_df = pd.merge(stock_df, mileage_df, on=PARTITIONS, how='left')
    stock_and_mileage_df['Notna_Count'] = stock_and_mileage_df['Notna_Count'].fillna(0)

    # Calculate stadistics for categorizations that do not have enough data, by grouping
    stats_df = stock_and_mileage_df.apply(
        lambda row: activity_stats_calculator_by_grouping(
            row, df, MAPPING_CATEGORY_LAST_EURO_STANDARD, settings.MIN_STOCK_FOR_MEAN_ACTIVITY_CALCULATION),
        result_type='expand', axis='columns')
    stats_df.columns = ACTIVITY_COLUMNS + ['Activity_Grouping']

    # Join stock with updated activity statistics
    stock_and_mileage_df = pd.concat([stock_and_mileage_df.drop(ACTIVITY_COLUMNS, axis=1), stats_df], axis='columns')

    # Convert activity statistics columns to integer and check for nan values
    convert_to_integer_df_columns(stock_and_mileage_df)
    return stock_and_mileage_df


def save_curated_vehicles(vehicles_df: pd.DataFrame, paths: OutputPaths):
    """Save the vehicles to csv and, if pyarrow is installed, to parquet (that keeps the types of the columns)"""
    vehicles_df.to_csv(paths.fleet_vehicles_csv, index=False)
    try:
        vehicles_df.to_parquet(paths.fleet_vehicles_parquet, index=False)
    except ImportError:
        logger.warning('pyarrow is not installed, the vehicles are not saved to parquet')
    except Exception:
        logger.warning('Unable to save the vehicles to parquet', exc_info=True)


def run_calculation(settings: SimpleNamespace, paths: OutputPaths) -> dict:
    """
    Run the stage 1.

    :return: dictionary with the dataframes: 'vehicles', 'stock_activity', 'stock_by_manufacturing_year',
        'stock_by_registration_year'
    """
    logger.info(f'Calculation of the stock and activity of the year {settings.STUDY_YEAR} with the register of '
                f'{settings.SNAPSHOT_DATE.date()}')

    # LOADING, STOCK AND CLASSIFICATION
    categorized_vehicles_df, discarded_cars_df = classify_fleet(settings, paths)
    info_logger.info(f'Total number of vehicles taken into account: {categorized_vehicles_df.shape[0]}')

    # ACTIVITY
    categorized_vehicles_df = calculate_vehicles_activity(categorized_vehicles_df, settings)

    # Assign to nan Activity outliers
    activity_outliers, lifetime_activity_outliers = calculate_activity_outliers_thresholds(
        categorized_vehicles_df, settings.IQR_MAX_FACTOR, settings.IQR_MIN_FACTOR, settings.MIN_ACTIVITY_FLOOR)
    save_to_csv_vehicles_with_erroneous_data(categorized_vehicles_df, paths, activity_outliers, discarded_cars_df)
    categorized_vehicles_df['Activity'], categorized_vehicles_df['Lifetime Activity'] = zip(
        *categorized_vehicles_df.apply(
            lambda row: check_for_activity_outliers(row, activity_outliers, lifetime_activity_outliers), axis=1))
    # The vehicles whose activity is an outlier have no activity
    outliers = categorized_vehicles_df['Activity'].isna()
    categorized_vehicles_df.loc[outliers, 'activity_method'] = 'no_activity'
    print_info(categorized_vehicles_df)

    # CURATED: one row per vehicle
    logger.info('Saving cleaned, categorized data and vehicle activity')
    vehicles_to_save = add_snapshot_columns(categorized_vehicles_df, settings)
    save_curated_vehicles(vehicles_to_save, paths)

    # AGGREGATED
    by_manufacturing_year = add_snapshot_columns(stock_by_year(categorized_vehicles_df, 'ANY_FABRICACIO'), settings)
    by_manufacturing_year.to_csv(paths.stock_by_manufacturing_year, index=False)
    by_registration_year = add_snapshot_columns(stock_by_year(categorized_vehicles_df, 'ANY_ALTA'), settings)
    by_registration_year.to_csv(paths.stock_by_registration_year, index=False)

    stock_activity = stock_and_activity_per_category(categorized_vehicles_df, settings)
    logger.info(f'Number of categories: {stock_activity.shape[0]}')
    # Mileage is the sum of the km between ITV revisions of different periods, not an annual mileage
    stock_activity_to_save = stock_activity.drop(['Notna_Count'], axis=1).rename(
        columns={'Mileage': 'Mileage_between_itv_km_sum'})
    stock_activity_to_save = add_snapshot_columns(stock_activity_to_save, settings)
    stock_activity_to_save.to_csv(paths.stock_activity, index=False)

    # EXPORT: input of COPERT, with the names of the columns that it uses
    copert_stock_activity_table(stock_activity).to_csv(paths.copert_stock_activity, index=False)

    logger.info('Calculation finished')
    return {'vehicles': vehicles_to_save, 'stock_activity': stock_activity_to_save,
            'stock_by_manufacturing_year': by_manufacturing_year, 'stock_by_registration_year': by_registration_year}
