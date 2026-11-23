from datetime import datetime

import numpy as np
import pandas as pd
import pytest

from activity.ActivityCalculator import activity_time_and_km_between_itv_revisions as activity
from ingestion.DateParser import date_parser
from ingestion.YearParser import year_of_manufacturing_parser

MAX_DATE = datetime(2025, 12, 31)


def vehicle(registration, revisions):
    """Vehicle row. revisions: list of (date, km) from the most recent ITV (DATA_DARRERA_ITV) to the oldest"""
    row = {'DATA_ALTA': pd.Timestamp(registration)}
    for i, number in enumerate(['', '2', '3', '4', '5']):
        date, km = revisions[i] if i < len(revisions) else (None, None)
        row['DATA_DARRERA_ITV' + number] = pd.Timestamp(date) if date else pd.NaT
        row['KM_DARRERA_ITV' + number] = km if km is not None else np.nan
    return pd.Series(row)


# ---- dates (L1)
@pytest.mark.parametrize('value, expected', [
    (20201030, datetime(2020, 10, 30)),      # the days 10, 20 and 30 were corrupted by rstrip('.00')
    (20201030.0, datetime(2020, 10, 30)),
    (20200920, datetime(2020, 9, 20)),
    (19510915, datetime(1951, 9, 15)),
    (20191320, datetime(2019, 1, 1)),        # invalid month: only the year is used
])
def test_date_parser(value, expected):
    assert date_parser(value) == expected


@pytest.mark.parametrize('value', [np.nan, None, '', 'abc'])
def test_date_parser_returns_nat_when_not_valid(value):
    assert pd.isna(date_parser(value))


@pytest.mark.parametrize('value, expected', [(2015, 2015), ('2015', 2015), (2015.0, 2015), (np.nan, None), ('x', None)])
def test_year_parser(value, expected):
    assert year_of_manufacturing_parser(value) == expected


# ---- activity (I1)
def test_activity_between_two_revisions():
    days, mileage, km_per_year, lifetime, method, pairs = activity(
        vehicle('2015-01-01', [('2025-06-01', 100000), ('2024-06-01', 90000)]), MAX_DATE)
    assert (days, mileage, km_per_year, lifetime, method, pairs) == (365, 10000, 10000.0, 100000, 'itv_pair', 1)


def test_revisions_after_the_max_date_are_ignored():
    result = activity(vehicle('2015-01-01', [('2026-03-01', 110000), ('2025-03-01', 100000),
                                             ('2024-03-01', 90000)]), MAX_DATE)
    assert result[1] == 10000 and result[3] == 100000


def test_close_revisions_are_merged_keeping_the_most_recent():
    days, mileage, km_per_year, lifetime, method, pairs = activity(
        vehicle('2015-01-01', [('2025-06-08', 100500), ('2025-06-01', 100000), ('2024-06-01', 90000)]), MAX_DATE)
    assert (days, mileage, lifetime) == (372, 10500, 100500)


def test_next_pair_is_used_when_the_mileage_does_not_increase():
    result = activity(vehicle('2015-01-01', [('2025-06-01', 100000), ('2024-06-01', 100000),
                                             ('2023-06-01', 80000)]), MAX_DATE)
    assert result[1] == 20000 and result[5] == 2


def test_revisions_in_disorder_are_sorted():
    result = activity(vehicle('2015-01-01', [('2024-06-01', 90000), ('2025-06-01', 100000)]), MAX_DATE)
    assert result[1] == 10000


def test_single_revision_only_if_enabled():
    row = vehicle('2020-01-01', [('2025-01-01', 50000)])
    assert pd.isna(activity(row, MAX_DATE)[2])
    result = activity(row, MAX_DATE, use_single_itv=True)
    assert result[4] == 'single_itv' and result[2] == pytest.approx(50000 / 1827 * 365)


def test_lifetime_activity_without_valid_pair():
    result = activity(vehicle('2015-01-01', [('2025-06-01', 100000), ('2024-06-01', 100000)]), MAX_DATE)
    assert pd.isna(result[2]) and result[3] == 100000 and result[4] == 'no_activity'


def test_no_revision_before_the_max_date():
    result = activity(vehicle('2020-01-01', [('2026-01-01', 50000)]), MAX_DATE)
    assert pd.isna(result[2]) and pd.isna(result[3])


def test_covid_max_date_leaves_out_later_revisions():
    row = vehicle('2015-01-01', [('2025-06-01', 100000), ('2024-06-01', 90000), ('2019-01-01', 60000),
                                 ('2018-01-01', 50000)])
    assert activity(row, datetime(2019, 3, 1))[1] == 10000
