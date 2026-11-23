from datetime import timedelta
import numpy as np
import pandas as pd
from typing import Dict, Tuple
import logging

from Classification.MappingConstants import CATEGORIES

info_logger = logging.getLogger('info_logger' + '.ActivityChecks')
logger = logging.getLogger('logger' + '.ActivityChecks')

# Categories whose activity (km/year) outliers thresholds are calculated
CATEGORIES_WITH_ACTIVITY = [category for category in CATEGORIES if category != 'Off Road']

# Default values of the outliers thresholds (can be changed in the settings file)
IQR_MAX_FACTOR = 5          # Maximum activity: Q3 + IQR_MAX_FACTOR * IQR
IQR_MIN_FACTOR = 1.5        # Minimum activity: Q1 - IQR_MIN_FACTOR * IQR
MIN_ACTIVITY_FLOOR = 250    # Minimum activity (km/year) below which a vehicle is an outlier, whatever the IQR is


def check_if_timedelta_greater_than_minimum_days(time_difference: timedelta, min_days: int) -> bool:
    """Check if timedelta greater than a minimum number of days"""
    if time_difference > timedelta(days=min_days):
        return True
    else:
        return False


def activity_thresholds(values: pd.Series, iqr_max_factor: float, iqr_min_factor: float,
                        min_activity_floor: float) -> Tuple[float, float]:
    """Minimum and maximum activity to not be considered an outlier, with the IQR method"""
    q1 = np.quantile(values, 0.25)
    q3 = np.quantile(values, 0.75)
    iqr = q3 - q1
    return max(q1 - iqr_min_factor * iqr, min_activity_floor), q3 + iqr_max_factor * iqr


def calculate_activity_outliers_thresholds(categorized_vehicles_df: pd.DataFrame,
                                           iqr_max_factor: float = IQR_MAX_FACTOR,
                                           iqr_min_factor: float = IQR_MIN_FACTOR,
                                           min_activity_floor: float = MIN_ACTIVITY_FLOOR) -> Tuple[Dict, Dict]:
    """
    Calculates outliers with the IQR method for each category and returns a dictionary with the min and max values,
    for the Activity and for the Lifetime Activity.
    """
    activity_outliers_per_category_mapping = {category: {'Min_Activity': 0, 'Max_Activity': 0}
                                              for category in CATEGORIES}
    lifetime_activity_outliers_per_category_mapping = {category: {'Min_Activity': 0, 'Max_Activity': 0}
                                                       for category in CATEGORIES}

    for category in CATEGORIES_WITH_ACTIVITY:
        category_df = categorized_vehicles_df[categorized_vehicles_df['Category'] == category]
        for column, mapping in (('Activity', activity_outliers_per_category_mapping),
                                ('Lifetime Activity', lifetime_activity_outliers_per_category_mapping)):
            data = category_df[column].dropna()
            if data.empty:
                logger.warning(f'No {column} values for Category {category}, outliers thresholds not calculated')
                # No outlier is detected in a category without data
                mapping[category] = {'Min_Activity': -np.inf, 'Max_Activity': np.inf}
                continue
            min_threshold, max_threshold = activity_thresholds(data, iqr_max_factor, iqr_min_factor,
                                                               min_activity_floor)
            mapping[category]['Max_Activity'] = max_threshold
            mapping[category]['Min_Activity'] = min_threshold

    info_logger.info(f'Activity outliers per Category: ')
    info_logger.info((activity_outliers_per_category_mapping))

    return activity_outliers_per_category_mapping, lifetime_activity_outliers_per_category_mapping


def check_for_activity_outliers(row: pd.Series, activity_outliers_per_category_mapping: Dict,
                                lifetime_activity_outliers_per_category_mapping: Dict):
    """Assign to nan Activity and Lifetime Activity outliers"""

    activity = row['Activity']
    lifetime_activity = row['Lifetime Activity']

    # Check activity outliers
    if row['Activity'] < activity_outliers_per_category_mapping[row['Category']]['Min_Activity']:
        info_logger.info(f"Vehicle amb activitat inferior al llindar mínim: "
                         f"{activity_outliers_per_category_mapping[row['Category']]['Min_Activity']}")
        info_logger.info(row)
        activity = np.nan
    elif row['Activity'] > activity_outliers_per_category_mapping[row['Category']]['Max_Activity']:
        activity = np.nan

    # Check Lifetime Activity outliers
    if row['Lifetime Activity'] < lifetime_activity_outliers_per_category_mapping[row['Category']]['Min_Activity']:
        info_logger.info(f"Vehicle amb Lifetime cumulative activity inferior al llindar mínim: "
                         f"{lifetime_activity_outliers_per_category_mapping[row['Category']]['Min_Activity']}")
        info_logger.info(row)
        lifetime_activity = np.nan
    elif row['Lifetime Activity'] > lifetime_activity_outliers_per_category_mapping[row['Category']]['Max_Activity']:
        lifetime_activity = np.nan

    return activity, lifetime_activity

