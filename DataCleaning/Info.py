import logging
import pandas as pd

from Classification import CATEGORIES

info_logger = logging.getLogger('info_logger' + '.ActivityCalculator')


def print_info(register_df: pd.DataFrame):
    number_of_vehicles_with_close_revision_dates = register_df[register_df.DATA_DARRERA_ITV2.notnull() &
                                                               register_df.Mileage.isnull()].shape[0]
    info_logger.info(f'Nombre de vehicles amb revisions ITV molt pròximes: {number_of_vehicles_with_close_revision_dates}')

    number_of_vehicles_with_null_CC_CM3_data = register_df[register_df['CC_CM3'].isna()].shape[0]
    info_logger.info(f'Nombre de vehicles sense dades de cilindrada CC_CM3: {number_of_vehicles_with_null_CC_CM3_data}')
    pass


def save_to_csv_vehicles_with_erroneous_data(register_df: pd.DataFrame, paths,
                                             activity_outliers_per_category_mapping: dict,
                                             discarded_passenger_cars_df: pd.DataFrame = None):
    """
    Save to csv files (quality assurance tables) the vehicles with erroneous data.

    :param register_df: classified vehicles dataframe, with the activity calculated
    :param paths: OutputPaths of the study
    :param activity_outliers_per_category_mapping: max activity (km/year) accepted for each Category
    :param discarded_passenger_cars_df: Passenger Cars discarded for having the engine displacement out of range
    """
    if discarded_passenger_cars_df is not None:
        discarded_passenger_cars_df.to_csv(paths.qa_passenger_cars_cc_out_of_range, index=False)

    df3 = register_df[(register_df['Category'] == 'L-Category') & (register_df['CC_CM3'] < 40)]
    df3.to_csv(paths.qa_l_category_cc_out_of_range, index=False)

    # Vehicles of every category with an activity above the maximum threshold of its category
    vehicles_with_erroneous_activity = []
    for category in CATEGORIES:
        if category not in activity_outliers_per_category_mapping:
            continue
        vehicles_with_erroneous_activity.append(
            register_df[(register_df['Category'] == category) &
                        (register_df['Activity'] > activity_outliers_per_category_mapping[category]['Max_Activity'])])
    pd.concat(vehicles_with_erroneous_activity).to_csv(paths.qa_activity_outliers, index=False)

    df4 = register_df[(register_df['KM_DARRERA_ITV'] < register_df['KM_DARRERA_ITV2']) |
                      (register_df['KM_DARRERA_ITV2'] < register_df['KM_DARRERA_ITV3']) |
                      (register_df['KM_DARRERA_ITV3'] < register_df['KM_DARRERA_ITV4'])]
    df4.to_csv(paths.qa_km_decreasing_between_itv, index=False)
