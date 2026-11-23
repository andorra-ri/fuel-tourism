import pandas as pd
import numpy as np
import logging
from ordered_set import OrderedSet

from .DateParser import date_parser

COLUMNS_SET = OrderedSet(['TIPUS', 'ANY_FABRICACIO', 'DATA_ALTA', 'DATA_BAIXA',
                          'MARCA', 'MODEL', 'CARBURANT', 'KW', 'CV', 'CO2', 'UNITATS_CO2',
                          'CC_CM3', 'PES_BUIT',
                          'PES_TOTAL_MÀXIM', 'DATA_DARRERA_ITV', 'KM_DARRERA_ITV',
                          'DATA_DARRERA_ITV2', 'KM_DARRERA_ITV2', 'DATA_DARRERA_ITV3',
                          'KM_DARRERA_ITV3', 'DATA_DARRERA_ITV4', 'KM_DARRERA_ITV4',
                          'DATA_DARRERA_ITV5', 'KM_DARRERA_ITV5'])

logger = logging.getLogger('logger' + '.Ingestion')


def register_ingestor_function(path_registre_vehicles: str) -> pd.DataFrame:
    """
    Load Excel file to dataframe after checking correct columns names and data types
    :param path_registre_vehicles: path of Original Excel ITV register file
    :return: Dataframe of the file parsed to correct formats
    """
    # Load Excel file
    logger.info("Loading Excel file")
    try:
        registre = pd.read_excel(path_registre_vehicles, header=0)
    except Exception as e:
        logger.error(f'Not able to read Registres Excel File: {path_registre_vehicles}', exc_info=True)
        raise

    # Check Columns names: the missing ones stop the execution, the new ones are only reported
    missing_columns = [column for column in COLUMNS_SET if column not in registre.columns]
    new_columns = [column for column in registre.columns if column not in COLUMNS_SET]
    if new_columns:
        logger.info(f'Columnes noves al fitxer {path_registre_vehicles}: {new_columns}')
    if missing_columns:
        message = f'Falten columnes obligatories al fitxer {path_registre_vehicles}: {missing_columns}'
        logger.error(message)
        raise ValueError(message)

    # Parsing of date columns
    try:
        registre['DATA_ALTA'] = registre['DATA_ALTA'].apply(date_parser)
    except KeyError:
        logger.error("No s'ha trobat columna DATA_ALTA", exc_info=True)
    try:
        registre['DATA_BAIXA'] = registre['DATA_BAIXA'].apply(date_parser)
    except KeyError:
        logger.error("No s'ha trobat columna DATA_BAIXA", exc_info=True)
    try:
        registre['DATA_DARRERA_ITV'] = registre['DATA_DARRERA_ITV'].apply(date_parser)
    except KeyError:
        logger.error(f"No s'ha trobat columna DATA_DARRERA_ITV al fitxer", exc_info=True)
    try:
        registre['DATA_DARRERA_ITV2'] = registre['DATA_DARRERA_ITV2'].apply(date_parser)
    except KeyError:
        logger.error(f"No s'ha trobat columna DATA_DARRERA_ITV2 al fitxer", exc_info=True)
    try:
        registre['DATA_DARRERA_ITV3'] = registre['DATA_DARRERA_ITV3'].apply(date_parser)
    except KeyError:
        logger.warning(f"No s'ha trobat columna DATA_DARRERA_ITV3 al fitxer")
    try:
        registre['DATA_DARRERA_ITV4'] = registre['DATA_DARRERA_ITV4'].apply(date_parser)
    except KeyError:
        logger.warning(f"No s'ha trobat columna DATA_DARRERA_ITV4 al fitxer")
    try:
        registre['DATA_DARRERA_ITV5'] = registre['DATA_DARRERA_ITV5'].apply(date_parser)
    except KeyError:
        logger.warning(f"No s'ha trobat columna DATA_DARRERA_ITV5 al fitxer")
    try:
        # If there is any empty cell pandas reads the column as decimal (ex: 2015.0), to_numeric handles both cases
        registre['ANY_FABRICACIO'] = pd.to_numeric(registre['ANY_FABRICACIO'], errors='coerce').astype(pd.Int32Dtype())
        number_of_empty_years = int(registre['ANY_FABRICACIO'].isna().sum())
        if number_of_empty_years > 0:
            logger.warning(f'Number of vehicles with no valid ANY_FABRICACIO: {number_of_empty_years}')
    except KeyError:
        logger.error("No s'ha trobat columna ANY_FABRICACIO", exc_info=True)
        raise

    return registre
