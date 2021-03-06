import pandas as pd
import logging

info_logger = logging.getLogger('info_logger' + '.ReClassification')


def anti_join(x, y, on):
    """Return rows in x which are not present in y"""
    ans = pd.merge(left=x, right=y, how='left', indicator=True, on=on)
    ans = ans.loc[ans._merge == 'left_only', :].drop(columns='_merge')
    return ans


def anti_join_all_cols(x, y):
    """Return rows in x which are not present in y"""
    assert set(x.columns.values) == set(y.columns.values)
    return anti_join(x, y, x.columns.tolist())


def reclassification_light_commercial_to_heavy_duty_trucks(register_df: pd.DataFrame) -> pd.DataFrame:
    """
    Replace Category to Heavy Duty Trucks for Light Commercial Vehicles of weight above 3500kg.
    """
    anti = register_df[(register_df['TIPUS'] == 'CAMIONETES') &
                       (register_df['PES_BUIT'] >= 3500) &
                       (register_df['Category'] == 'Light Commercial Vehicles')]
    info_logger.info(f'Total number of Light Commercial Vehicles converted to Heavy Duty Trucks loaded: {anti.shape[0]}')

    result = anti_join_all_cols(register_df, anti)
    recategorized_rows = anti.assign(Category='Heavy Duty Trucks')

    return result.append(recategorized_rows)


def reclassification_heavy_duty_trucks_to_light_commercial_vehicles(register_df: pd.DataFrame) -> pd.DataFrame:
    """
    Replace Category to Light Commercial Vehicles for  Heavy Duty Trucks of weight below 3500kg
    Es Tracta de vehicles registrats TIPUS CAMIONS i per tant classificats en la categoria Heavy Duty Trucks quan no hi
    pertoquen degut a pes inferior a 3500kg.
    """
    anti = register_df[(register_df['TIPUS'] == 'CAMIONS') &
                       (register_df['PES_BUIT'] < 3500) &
                       (register_df['Category'] == 'Heavy Duty Trucks')]
    info_logger.info(f'Total number of Heavy Duty Trucks converted to Light Commercial Vehicles loaded: {anti.shape[0]}')
    result = anti_join_all_cols(register_df, anti)
    recategorized_rows = anti.assign(Category='Light Commercial Vehicles')

    return result.append(recategorized_rows)


def reclassification_trial_bikes_to_off_road(register_df: pd.DataFrame) -> pd.DataFrame:
    """
    Replace Category of trial bikes from L-Category to Off Road
    """
    anti = register_df[(register_df['Category'] == 'L-Category') &
                       (register_df['MODEL'].str.lower().str.contains('trial'))]
    info_logger.info(f'Total number of Trial bikes detected: {anti.shape[0]}')
    result = anti_join_all_cols(register_df, anti)
    recategorized_rows = anti.assign(Category='Off Road')

    return result.append(recategorized_rows)
