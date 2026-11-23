import pandas as pd
import logging

info_logger = logging.getLogger('info_logger' + '.ReClassification')


def reclassification_light_commercial_to_heavy_duty_trucks(register_df: pd.DataFrame) -> pd.DataFrame:
    """
    Replace Category to Heavy Duty Trucks for Light Commercial Vehicles of weight above 3500kg.
    """
    df = register_df.copy()
    mask = ((df['TIPUS'] == 'CAMIONETES') &
            (df['PES_BUIT'] >= 3500) &
            (df['Category'] == 'Light Commercial Vehicles'))
    info_logger.info(f'Total number of Light Commercial Vehicles converted to Heavy Duty Trucks loaded: {mask.sum()}')
    df.loc[mask, 'Category'] = 'Heavy Duty Trucks'

    return df


def reclassification_heavy_duty_trucks_to_light_commercial_vehicles(register_df: pd.DataFrame) -> pd.DataFrame:
    """
    Replace Category to Light Commercial Vehicles for  Heavy Duty Trucks of weight below 3500kg
    Es Tracta de vehicles registrats TIPUS CAMIONS i per tant classificats en la categoria Heavy Duty Trucks quan no hi
    pertoquen degut a pes inferior a 3500kg.
    """
    df = register_df.copy()
    mask = ((df['TIPUS'] == 'CAMIONS') &
            (df['PES_BUIT'] < 3500) &
            (df['Category'] == 'Heavy Duty Trucks'))
    info_logger.info(f'Total number of Heavy Duty Trucks converted to Light Commercial Vehicles loaded: {mask.sum()}')
    df.loc[mask, 'Category'] = 'Light Commercial Vehicles'

    return df


def reclassification_trial_bikes_to_off_road(register_df: pd.DataFrame) -> pd.DataFrame:
    """
    Replace Category of trial bikes from L-Category to Off Road
    """
    df = register_df.copy()
    mask = ((df['Category'] == 'L-Category') &
            (df['MODEL'].astype(str).str.lower().str.contains('trial', na=False)))
    info_logger.info(f'Total number of Trial bikes detected: {mask.sum()}')
    df.loc[mask, 'Category'] = 'Off Road'

    return df
