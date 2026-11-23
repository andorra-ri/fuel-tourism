from datetime import datetime
import pandas as pd
import logging

logger = logging.getLogger('logger' + '.DateParser')


def date_parser(date: int):
    """ Parse DATA_ALTA and DATA-BAIXA columns of "Registre de vehicles Excel file"

    :param date: Date in format type %Y%m%d, ex: 19510915 (pandas may read it as float, ex: 19510915.0)
    :return: datetime of the date, or pd.NaT if the value is empty or cannot be parsed
    """
    if pd.isna(date):
        return pd.NaT

    # Remove only the ".0" suffix that appears when pandas reads the column as float
    date = str(date).strip().removesuffix('.0')
    if date in ('', 'nan'):
        return pd.NaT

    try:
        return datetime.strptime(date, '%Y%m%d')
    except ValueError:
        try:
            # Some dates only have a valid year
            result = datetime.strptime(date[:4], '%Y')
            logger.warning(f'Date {date} is not valid, only its year is used')
            return result
        except ValueError:
            logger.error(f'Unable to parse date {date}, with function date_parser')
            return pd.NaT
