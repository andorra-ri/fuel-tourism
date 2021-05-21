import pandas as pd

from .CopertSegmentIdentification import segment_identification_for_each_category
from .EuroStandard import euro_standard_identification_by_year_of_manufacturing
from .ReClassification import (reclassification_light_commercial_to_heavy_duty_trucks,
                               reclassification_heavy_duty_trucks_to_light_commercial_vehicles
                               )
from .MappingFunctions import category_mapper_itv_copert, fuel_mapper_itv_copert


def category_fuel_segment_euro_classification_wrapper_function(register_df: pd.DataFrame) -> pd.DataFrame:
    """Return the input itv register df with the columns Category, Fuel, Segment, Euro Standard for each vehicle(row)"""

    df = category_mapper_itv_copert(register_df)
    df = fuel_mapper_itv_copert(df)
    df = reclassification_light_commercial_to_heavy_duty_trucks(df)
    df = reclassification_heavy_duty_trucks_to_light_commercial_vehicles(df)

    df['Segment'] = df.apply(lambda row: segment_identification_for_each_category(row), axis=1)
    df['Euro Standard'] = df.apply(lambda row: euro_standard_identification_by_year_of_manufacturing(row), axis=1)
    return df