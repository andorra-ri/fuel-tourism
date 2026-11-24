import pandas as pd
import logging

from .CopertSegmentIdentification import segment_identification_for_each_category
from .EuroStandard import euro_standard_identification_by_year_of_manufacturing
from .ReClassification import (
    reclassification_light_commercial_to_heavy_duty_trucks,
    reclassification_heavy_duty_trucks_to_light_commercial_vehicles,
    reclassification_trial_bikes_to_off_road
                               )
from .MappingFunctions import category_mapper_itv_copert, fuel_mapper_itv_copert, check_unmapped_values
from .SegmentRedistribution import fill_nan_with_frequency
from .MappingConstants import NON_ELECTRIC_FUEL_TYPES, ELECTRIC_TYPES, HYBRID_PHEV_TYPES

logger = logging.getLogger('logger' + '.ClassificationWrapper')


# Passenger cars with an engine displacement out of this range (cm3) are discarded
MIN_PASSENGER_CAR_CC = 560
MAX_PASSENGER_CAR_CC = 8500


def normalise_fuels_to_copert(df: pd.DataFrame) -> pd.Series:
    """
    Assign the fuel of the vehicles whose combination Category-Fuel does not exist in the COPERT stock configuration
    (Stock_Configuration_Andorra.csv) to the closest one. Mild hybrids are vehicles with the emission factors of the
    conventional vehicle (EMEP/EEA guidebook, Passenger cars, hybrid). Modifies df in place.

    :return: mask of the Heavy Duty Trucks that were hybrids (COPERT has no hybrid Heavy Duty Trucks)
    """
    category = df['Category'].copy()  # Copies: the masks must use the values before the changes
    fuel = df['Fuel'].copy()
    petrol_like = ['Petrol Hybrid', 'Petrol PHEV']
    diesel_like = ['Diesel Hybrid', 'Diesel PHEV']
    hybrid_heavy_duty_trucks = (category == 'Heavy Duty Trucks') & fuel.isin(HYBRID_PHEV_TYPES)

    # There are no motorcycles other than Petrol
    df.loc[(category == 'L-Category') & fuel.isin(HYBRID_PHEV_TYPES + ['Diesel', 'LPG Bi-fuel']), 'Fuel'] = 'Petrol'
    # There are no hybrid Heavy Duty Trucks nor LPG ones
    df.loc[hybrid_heavy_duty_trucks, 'Fuel'] = 'Diesel'
    df.loc[(category == 'Heavy Duty Trucks') & (fuel == 'LPG Bi-fuel'), 'Fuel'] = 'Petrol'
    # Light Commercial Vehicles have only Petrol, Diesel and Battery electric
    df.loc[(category == 'Light Commercial Vehicles') & fuel.isin(petrol_like + ['LPG Bi-fuel']), 'Fuel'] = 'Petrol'
    df.loc[(category == 'Light Commercial Vehicles') & fuel.isin(diesel_like), 'Fuel'] = 'Diesel'
    # The Diesel hybrid Passenger Cars keep their fuel in the classification (as in the report 2023). COPERT has no such
    # category: in its file they are added to Passenger Cars - Diesel (see copert_stock_activity_table)
    return hybrid_heavy_duty_trucks


def passenger_cars_cc_out_of_range_mask(df: pd.DataFrame) -> pd.Series:
    """Mask of the non electric Passenger Cars with a known engine displacement out of the accepted range"""
    return ((df['Category'] == 'Passenger Cars') & df['Fuel'].isin(NON_ELECTRIC_FUEL_TYPES) &
            ((df['CC_CM3'] < MIN_PASSENGER_CAR_CC) | (df['CC_CM3'] > MAX_PASSENGER_CAR_CC)))


def category_fuel_segment_euro_classification_wrapper_function(register_df: pd.DataFrame,
                                                              random_seed: int = 42,
                                                              return_discarded: bool = False):
    """
    Return the input itv register df with the columns Category, Fuel, Segment, Euro Standard for each vehicle(row).
    Non electric Passenger Cars with an engine displacement out of the range 560-8500 cm3 are discarded. Those without
    displacement data are kept and their Segment is assigned by the distribution of the Passenger Cars.

    :param register_df: itv register dataframe
    :param random_seed: seed used to assign Segment to vehicles with erroneous data, so results are reproducible
    :param return_discarded: if True returns a tuple (classified df, discarded vehicles df)
    """
    logger.info('Starting Vehicle Classification')
    df = category_mapper_itv_copert(register_df)
    df = fuel_mapper_itv_copert(df)
    check_unmapped_values(df)
    out_of_range = passenger_cars_cc_out_of_range_mask(df)
    discarded_df = df[out_of_range].copy()
    logger.info(f'Passenger Cars discarded for having an engine displacement out of range: {discarded_df.shape[0]}')
    df = df[~out_of_range].copy()
    df = reclassification_light_commercial_to_heavy_duty_trucks(df)
    df = reclassification_heavy_duty_trucks_to_light_commercial_vehicles(df)
    df = reclassification_trial_bikes_to_off_road((df))
    hybrid_heavy_duty_trucks = normalise_fuels_to_copert(df)

    df['Segment'] = df.apply(lambda row: segment_identification_for_each_category(row), axis=1)
    # For non electric vehicles with erroneous weight or CC_M3 data, assigns Segment by the distribution of their own
    # Category. It is done before the Euro Standard identification, because for some vehicles it depends on the Segment.
    # Electrical and Off Road vehicles are not filled
    has_segment = df['Fuel'].isin(NON_ELECTRIC_FUEL_TYPES) & (df['Category'] != 'Off Road')
    fill_nan_with_frequency(df, 'Segment', seed=random_seed, eligible_rows=has_segment)
    df['Euro Standard'] = df.apply(lambda row: euro_standard_identification_by_year_of_manufacturing(row), axis=1)

    # Assign Segment value of Electrical and Off Road vehicles to None
    df.loc[~df['Fuel'].isin(NON_ELECTRIC_FUEL_TYPES + ELECTRIC_TYPES), 'Segment'] = None
    df.loc[df['Category'] == 'Off Road', 'Segment'] = None

    # Addapt Segment results not present in Copert Stock Configuration
    # There is no Mini segment below Euro 4
    df.loc[(df['Category'] == 'Passenger Cars') &
           (df['Segment'] == 'Mini') &
           ((df['Euro Standard'] == 'Euro 3') | (df['Euro Standard'] == 'Euro 1') |
            (df['Euro Standard'] == 'Conventional') | (df['Euro Standard'] == 'ECE 15/04') |
            (df['Euro Standard'] == 'ECE 15/02') | (df['Euro Standard'] == 'ECE 15/03')), 'Segment'] = 'Small'
    # There is no Small, Medium or small segments in L-Category nor Light Commercial Vehicles
    df.loc[(df['Category'] == 'L-Category') &
           ((df['Segment'] == 'Small') | (df['Segment'] == 'Medium') | (df['Segment'] == 'Large-SUV-Executive')),
           'Segment'] = 'Motorcycles 4-stroke <250 cm³'
    df.loc[(df['Category'] == 'Light Commercial Vehicles') &
           ((df['Segment'] == 'Small') | (df['Segment'] == 'Medium') | (df['Segment'] == 'Large-SUV-Executive')),
           'Segment'] = 'N1-III'
    # There is no mini segment below Euro 4, we assign them to Euro 4
    df.loc[(df['Category'] == 'Passenger Cars') &
           (df['Segment'] == 'Mini') &
           ((df['Euro Standard'] == 'Euro 3') | (df['Euro Standard'] == 'Euro 2') | (df['Euro Standard'] == 'Euro 1')),
           'Euro Standard'] = 'Euro 4'
    # Hybrid Heavy Duty Trucks (now Diesel, see normalise_fuels_to_copert) are assigned a newer Euro Standard
    df.loc[hybrid_heavy_duty_trucks, 'Euro Standard'] = 'Euro VI D/E'
    # COPERT has a single segment, without Euro Standard changes, for the Petrol Heavy Duty Trucks
    petrol_heavy_duty_trucks = (df['Category'] == 'Heavy Duty Trucks') & (df['Fuel'] == 'Petrol')
    df.loc[petrol_heavy_duty_trucks, 'Segment'] = '>3,5 t'
    df.loc[petrol_heavy_duty_trucks, 'Euro Standard'] = 'Conventional'
    # Disel PHEV Passenger Cars can only be Large-SUV-Executive
    df.loc[(df['Category'] == 'Passenger Cars') &
           (df['Fuel'] == 'Diesel PHEV'), 'Segment'] = 'Large-SUV-Executive'

    if return_discarded:
        return df, discarded_df
    return df
