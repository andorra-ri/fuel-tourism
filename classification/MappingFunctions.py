import logging
import pandas as pd
from .MappingConstants import CATEGORY_MAPPING_DICT, FUEL_MAPPING_DICT

logger = logging.getLogger('logger' + '.MappingFunctions')


def category_mapper_itv_copert(registre_df: pd.DataFrame) -> pd.DataFrame:
    """ Create column Category with corresponding category of the vehicle taken from original column TIPUS"""
    df = registre_df.copy()
    df['Category'] = df['TIPUS'].map(CATEGORY_MAPPING_DICT)  # Create new column Category
    return df


def fuel_mapper_itv_copert(registre_df: pd.DataFrame) -> pd.DataFrame:
    """ Create column Fuel with the fuel type of the vehicle taken from original column CARBURANT"""
    df = registre_df.copy()
    df['Fuel'] = df['CARBURANT'].map(FUEL_MAPPING_DICT)  # Create new column Fuel
    return df


def check_unmapped_values(df: pd.DataFrame):
    """
    Check that every TIPUS and CARBURANT value of the register has been mapped to a Category and a Fuel.
    The original values that were not mapped are logged with the number of vehicles, and a ValueError is raised, as
    a new name of a vehicle type or fuel in the Excel file would otherwise leave vehicles with no Category or Fuel.
    The fuel "SENSE CARBURANT" is mapped to None on purpose, those vehicles are dropped before the classification.
    """
    problems = []
    for original_column, mapped_column, mapping in (('TIPUS', 'Category', CATEGORY_MAPPING_DICT),
                                                    ('CARBURANT', 'Fuel', FUEL_MAPPING_DICT)):
        unmapped = df[df[mapped_column].isna() & ~df[original_column].isin(
            [value for value, mapped in mapping.items() if mapped is None])]
        if not unmapped.empty:
            counts = unmapped[original_column].value_counts(dropna=False).to_dict()
            problems.append(f'{original_column} values with no {mapped_column} associated: {counts}')
    if problems:
        message = 'Values of the register not present in the mapping dictionaries (MappingConstants.py): ' +                   '; '.join(problems)
        logger.error(message)
        raise ValueError(message)
