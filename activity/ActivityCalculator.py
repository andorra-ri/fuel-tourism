from typing import List, Tuple
import numpy as np
import pandas as pd
from datetime import timedelta, datetime
import logging

DAYS_IN_A_YEAR = 365
ITV_NUMBERS = ['', '2', '3', '4', '5']  # Suffix of the columns DATA_DARRERA_ITV{n} and KM_DARRERA_ITV{n}

# Values of the column activity_method
METHOD_ITV_PAIR = 'itv_pair'      # Activity from the km and days between two ITV revisions
METHOD_SINGLE_ITV = 'single_itv'  # Activity from the km of the only ITV and the days since the registration
METHOD_NO_ACTIVITY = 'no_activity'

info_logger = logging.getLogger('info_logger' + '.ActivityCalculator')
logger = logging.getLogger('logger' + '.ActivityCalculator')


def time_between_dates(date1: datetime, date2: datetime) -> timedelta:
    """Take two dates and return the time difference between them. """
    try:
        timedelta_between_dates = date1 - date2
        return timedelta_between_dates
    except Exception:
        logger.error(f'Unable to compare date1 and date2.', exc_info=True)


def valid_itv_revisions(row: pd.Series, max_date: datetime) -> List[Tuple[datetime, float]]:
    """
    List of the (date, km) of the ITV revisions of the vehicle (DATA_DARRERA_ITV to DATA_DARRERA_ITV5) that have date
    and km, and a date not later than max_date, sorted from the most recent to the oldest.
    """
    revisions = []
    for number in ITV_NUMBERS:
        date = row.get(f'DATA_DARRERA_ITV{number}', pd.NaT)
        km = row.get(f'KM_DARRERA_ITV{number}', np.nan)
        if pd.notna(date) and pd.notna(km) and date <= max_date:
            revisions.append((date, km))
    revisions.sort(key=lambda revision: revision[0], reverse=True)
    return revisions


def merge_close_revisions(revisions: List[Tuple[datetime, float]], min_days_between_revisions: int
                          ) -> List[Tuple[datetime, float]]:
    """
    Merge the consecutive revisions separated by less than (or exactly) the minimum number of days, as they are not a
    real new revision (ex: a failed revision repeated the following week). From each group of close revisions the
    most recent one is kept.

    :param revisions: list of (date, km) sorted from the most recent to the oldest
    :param min_days_between_revisions: minimum number of days between revisions
    :return: list of (date, km) sorted from the most recent to the oldest, with more than the minimum days between them
    """
    merged = []
    previous_date = None
    for date, km in revisions:
        if previous_date is None or (previous_date - date) > timedelta(days=min_days_between_revisions):
            merged.append((date, km))
        previous_date = date
    return merged


def activity_time_and_km_between_itv_revisions(row, max_date: datetime, min_days_between_revisions: int = 150,
                                               use_single_itv: bool = False):
    """
    Calculate the time in days between 2 consecutives itv revisions and the corresponding mileage.
    Only the revisions made until max_date are taken into account (ex: end of the study year, or before covid).
     - The revisions separated by less than the minimum number of days are merged (avoiding therefore revisions not
       passed), keeping the most recent of them.
     - Starting from the most recent revision, the first pair of consecutive revisions with an increasing mileage is
       used. If a pair is not valid, the next older pair is tried.
     - If the vehicle has just one revision and use_single_itv is True, the activity is the mileage of the revision
       divided by the days since the registration (DATA_ALTA).

    :param row: vehicle pd.Serie from register dataframe
    :param max_date: max date to take into account
    :param min_days_between_revisions: minimum number of days between revisions
    :param use_single_itv: calculate the activity of vehicles with just one revision
    :return: tuple (number of days between revisions, mileage between those revisions in Km, activity in km/year,
                    Lifetime cumulative activity (km), activity_method, itv_pairs_used).
                    itv_pairs_used is the position of the pair of revisions used (1 is the most recent pair)
    """
    revisions = valid_itv_revisions(row, max_date)
    if not revisions:
        return np.nan, np.nan, np.nan, np.nan, METHOD_NO_ACTIVITY, 0

    lifetime_activity = revisions[0][1]
    revisions = merge_close_revisions(revisions, min_days_between_revisions)

    for position, ((date, km), (previous_date, previous_km)) in enumerate(zip(revisions[:-1], revisions[1:]), start=1):
        days = (date - previous_date).days
        mileage = km - previous_km
        if days > 0 and mileage > 0:
            return days, mileage, (mileage / days) * DAYS_IN_A_YEAR, lifetime_activity, METHOD_ITV_PAIR, position

    # Vehicle with just one revision: activity since the registration
    if use_single_itv and len(revisions) == 1 and pd.notna(row.get('DATA_ALTA', pd.NaT)):
        days = (revisions[0][0] - row['DATA_ALTA']).days
        if days > min_days_between_revisions and lifetime_activity > 0:
            return days, lifetime_activity, (lifetime_activity / days) * DAYS_IN_A_YEAR, lifetime_activity, \
                   METHOD_SINGLE_ITV, 0

    return np.nan, np.nan, np.nan, lifetime_activity, METHOD_NO_ACTIVITY, 0
