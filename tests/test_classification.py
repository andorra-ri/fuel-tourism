import numpy as np
import pandas as pd
import pytest

from classification.EuroStandard import euro_standard_identification_by_year_of_manufacturing as euro
from classification.MappingFunctions import check_unmapped_values, category_mapper_itv_copert, fuel_mapper_itv_copert
from classification.ReClassification import (
    reclassification_light_commercial_to_heavy_duty_trucks,
    reclassification_heavy_duty_trucks_to_light_commercial_vehicles,
    reclassification_trial_bikes_to_off_road
)
from classification.SegmentRedistribution import fill_nan_with_frequency
from classification.ClassificationWrapper import passenger_cars_cc_out_of_range_mask


def test_segment_is_filled_with_the_distribution_of_its_own_category():
    df = pd.DataFrame({
        'Category': ['Passenger Cars'] * 6 + ['Heavy Duty Trucks'] * 4 + ['Off Road'] * 2,
        'Segment': ['Small', 'Small', 'Medium', None, None, 'Small', 'Rigid <=7,5 t', 'Rigid <=7,5 t', None, None,
                    None, None]})
    first, second = df.copy(), df.copy()
    fill_nan_with_frequency(first, 'Segment', seed=1)
    fill_nan_with_frequency(second, 'Segment', seed=1)
    assert first.equals(second)  # reproducible
    assert first.loc[first.Category == 'Heavy Duty Trucks', 'Segment'].eq('Rigid <=7,5 t').all()
    assert first.loc[first.Category == 'Passenger Cars', 'Segment'].isin(['Small', 'Medium']).all()
    assert first.loc[first.Category == 'Off Road', 'Segment'].isna().all()


def test_reclassifications_keep_the_index_and_the_rows():
    df = pd.DataFrame({'TIPUS': ['CAMIONETES', 'CAMIONS', 'MOTOS', 'CAMIONETES'], 'PES_BUIT': [4000, 3000, 100, 2000],
                       'Category': ['Light Commercial Vehicles', 'Heavy Duty Trucks', 'L-Category',
                                    'Light Commercial Vehicles'],
                       'MODEL': ['x', 'y', 'Gas Gas TRIAL', 'z']}, index=[5, 5, 7, 9])
    result = reclassification_light_commercial_to_heavy_duty_trucks(df)
    result = reclassification_heavy_duty_trucks_to_light_commercial_vehicles(result)
    result = reclassification_trial_bikes_to_off_road(result)
    assert result['Category'].tolist() == ['Heavy Duty Trucks', 'Light Commercial Vehicles', 'Off Road',
                                           'Light Commercial Vehicles']
    assert result.index.tolist() == [5, 5, 7, 9]


def test_unmapped_values_stop_the_execution():
    df = pd.DataFrame({'TIPUS': ['TURISME', 'TIPUS NOU'], 'CARBURANT': ['GASOLINA', 'HIB.NOU']})
    df = fuel_mapper_itv_copert(category_mapper_itv_copert(df))
    with pytest.raises(ValueError, match='TIPUS NOU'):
        check_unmapped_values(df)


def test_known_values_and_fuel_without_fuel_pass_the_check():
    df = pd.DataFrame({'TIPUS': ['TURISME', 'MOTOS'], 'CARBURANT': ['GASOLINA-GLP', 'SENSE CARBURANT']})
    check_unmapped_values(fuel_mapper_itv_copert(category_mapper_itv_copert(df)))


def test_passenger_cars_cc_out_of_range():
    df = pd.DataFrame({'Category': ['Passenger Cars'] * 5 + ['L-Category'],
                       'Fuel': ['Petrol', 'Petrol', 'Petrol', 'Battery electric', 'Diesel', 'Petrol'],
                       'CC_CM3': [500, 560, 9000, 0, np.nan, 50]})
    assert passenger_cars_cc_out_of_range_mask(df).tolist() == [True, False, True, False, False, False]


@pytest.mark.parametrize('year, expected', [(1978, 'ECE 15/02'), (1981, 'ECE 15/03'), (1985, 'ECE 15/04'),
                                            (2016, 'Euro 6 a/b/c'), (2021, 'Euro 6 d/e')])
def test_euro_standard_of_passenger_cars_has_no_gaps(year, expected):
    assert euro(pd.Series({'Category': 'Passenger Cars', 'Fuel': 'Petrol', 'Segment': 'Medium',
                           'ANY_FABRICACIO': year})) == expected


@pytest.mark.parametrize('fuel', ['Diesel', 'Petrol'])
@pytest.mark.parametrize('year, expected', [(2016, 'Euro 5'), (2017, 'Euro 6 a/b/c'), (2019, 'Euro 6 a/b/c'),
                                            (2020, 'Euro 6 d-temp')])
def test_euro_standard_of_light_commercial_vehicles_n1_ii(fuel, year, expected):
    assert euro(pd.Series({'Category': 'Light Commercial Vehicles', 'Fuel': fuel, 'Segment': 'N1-II',
                           'ANY_FABRICACIO': year})) == expected


def test_fuels_without_copert_equivalent_are_normalised():
    from classification.ClassificationWrapper import normalise_fuels_to_copert
    df = pd.DataFrame({
        'Category': ['Passenger Cars', 'Light Commercial Vehicles', 'Light Commercial Vehicles', 'Heavy Duty Trucks',
                     'L-Category', 'Passenger Cars'],
        'Fuel': ['Diesel Hybrid', 'Petrol Hybrid', 'Diesel PHEV', 'Diesel Hybrid', 'Diesel', 'Diesel PHEV']})
    hybrid_trucks = normalise_fuels_to_copert(df)
    assert df['Fuel'].tolist() == ['Diesel', 'Petrol', 'Diesel', 'Diesel', 'Petrol', 'Diesel PHEV']
    assert hybrid_trucks.tolist() == [False, False, False, True, False, False]


def test_electric_light_commercial_vehicles_have_euro_in_every_segment():
    for segment in ['N1-I', 'N1-II', 'N1-III']:
        row = pd.Series({'Category': 'Light Commercial Vehicles', 'Fuel': 'Battery electric', 'Segment': segment,
                         'ANY_FABRICACIO': 2022})
        assert euro(row) == 'Euro 6 d/e'


def test_copert_file_uses_the_names_of_copert():
    from pipeline.calculation import copert_stock_activity_table
    stock = pd.DataFrame({
        'Category': ['Passenger Cars', 'L-Category', 'Off Road', 'Buses'],
        'Fuel': ['LPG Bi-fuel', 'Battery electric', 'Petrol', 'Battery electric'],
        'Segment': ['Small', None, None, None], 'Euro Standard': ['Euro 6 d/e', None, None, 'Euro VI D/E'],
        'Stock': [1, 2, 3, 4], 'Mean_Activity': [1, 1, 1, 1], 'Mean_Lifetime_Activity': [1, 1, 1, 1]})
    table = copert_stock_activity_table(stock)
    assert table['Fuel'].tolist() == ['LPG Bifuel', 'Battery electric']
    assert table['Segment'].tolist() == ['Small', '-']
