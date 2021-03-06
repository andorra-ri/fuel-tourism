import logging

info_logger = logging.getLogger('info_logger' + '.EuroStandard')


def euro_standard_identification_by_year_of_manufacturing(row) -> str:
    """
    Returns the Euro Standard Legislation/technology depending of the vehicle Category, Fuel and year of manufacturing
    The dates are taken from the Date(first registration) on https://en.wikipedia.org/wiki/European_emission_standards

    :param row: row of a pd.DataFrame that contains itv register data
    :return: Euro Standard techonology
    """

    if row['Category'] == 'Passenger Cars':
        if row['Fuel'] != 'Battery Electric':  # No Euro Category for electric cars
            # Acording to Copert there is no Petrol Mini less than EURO 4
            if row['Fuel'] == 'Petrol' and row['Segment'] == 'Mini' and row['ANY_FABRICACIO'] < 2011:
                return 'Euro 4'
            # Acording to Copert there is no Petrol Hybrid less than EURO 4
            if row['Fuel'] == 'Petrol Hybrid' and row['ANY_FABRICACIO'] < 2011:
                return 'Euro 4'
            # Acording to Copert there is no Petrol/Diesel PHEV less than EURO 6 a/b/c
            if (row['Fuel'] == 'Petrol PHEV' or row['Fuel'] == 'Diesel PHEV') and row['ANY_FABRICACIO'] < 2020:
                return 'Euro 6 a/b/c'

            if row['ANY_FABRICACIO'] < 1978:
                if row['Fuel'] == 'Diesel':
                    return 'Conventional'
                return 'ECE 15/00-01'
            elif 1978 < row['ANY_FABRICACIO'] < 1981:
                if row['Fuel'] == 'Diesel':
                    return 'Conventional'
                return 'ECE 15/02'
            elif 1981 < row['ANY_FABRICACIO'] < 1985:
                if row['Fuel'] == 'Diesel':
                    return 'Conventional'
                return 'ECE 15/03'
            elif 1985 < row['ANY_FABRICACIO'] < 1993:
                if row['Fuel'] == 'Diesel':
                    return 'Conventional'
                return 'ECE 15/04'
            elif 1993 <= row['ANY_FABRICACIO'] < 1997:
                return 'Euro 1'
            elif 1997 <= row['ANY_FABRICACIO'] < 2001:
                return 'Euro 2'
            elif 2001 <= row['ANY_FABRICACIO'] < 2006:
                return 'Euro 3'
            elif 2006 <= row['ANY_FABRICACIO'] < 2011:
                return 'Euro 4'
            elif 2011 <= row['ANY_FABRICACIO'] < 2016:
                return 'Euro 5'
            elif 2016 <= row['ANY_FABRICACIO'] < 2020:
                return 'Euro 6 a/b/c'
            elif 2020 <= row['ANY_FABRICACIO'] < 2021:
                return 'Euro 6 d-temp'
            elif row['ANY_FABRICACIO'] >= 2021:
                return 'Euro 6 d'
        else:
            return None

    # Technology classification of Light Commercial Vehicles
    elif row['Category'] == 'Light Commercial Vehicles':
        if row['Segment'] == 'N1-I':
            if row['Fuel'] == 'Diesel' or row['Fuel'] == 'Petrol':
                if row['ANY_FABRICACIO'] < 1995:
                    return 'Conventional'
                elif 1995 <= row['ANY_FABRICACIO'] < 1998:
                    return 'Euro 1'
                elif 1998 <= row['ANY_FABRICACIO'] < 2001:
                    return 'Euro 2'
                elif 2001 <= row['ANY_FABRICACIO'] < 2006:
                    return 'Euro 3'
                elif 2006 <= row['ANY_FABRICACIO'] < 2011:
                    return 'Euro 4'
                elif 2011 <= row['ANY_FABRICACIO'] < 2016:  # Euro 6: September 2015
                    return 'Euro 5'
                elif 2016 <= row['ANY_FABRICACIO'] < 2020:
                    return 'Euro 6 a/b/c'
                elif 2020 <= row['ANY_FABRICACIO'] < 2021:
                    return 'Euro 6 d-temp'
                elif row['ANY_FABRICACIO'] >= 2021:
                    return 'Euro 6 d'

        else:  # Segments N1-II and N1-III
            if row['Fuel'] == 'Diesel':
                if row['ANY_FABRICACIO'] < 1995:
                    return 'Conventional'
                elif 1995 <= row['ANY_FABRICACIO'] < 1999:
                    return 'Euro 1'
                elif 1999 <= row['ANY_FABRICACIO'] < 2002:
                    return 'Euro 2'
                elif 2002 <= row['ANY_FABRICACIO'] < 2007:
                    return 'Euro 3'
                elif 2007 <= row['ANY_FABRICACIO'] < 2012:
                    return 'Euro 4'
                elif 2012 <= row['ANY_FABRICACIO'] < 2017:
                    return 'Euro 5'
                elif 2016 <= row['ANY_FABRICACIO'] < 2021:
                    return 'Euro 6 a/b/c'
                elif 2020 <= row['ANY_FABRICACIO'] < 2022:
                    return 'Euro 6 d-temp'
                elif row['ANY_FABRICACIO'] >= 2022:
                    return 'Euro 6 d'
            elif row['Fuel'] == 'Petrol':
                if row['ANY_FABRICACIO'] < 1995:
                    return 'Conventional'
                elif 1995 <= row['ANY_FABRICACIO'] < 1999:
                    return 'Euro 1'
                elif 1999 <= row['ANY_FABRICACIO'] < 2002:
                    return 'Euro 2'
                elif 2002 <= row['ANY_FABRICACIO'] < 2007:
                    return 'Euro 3'
                elif 2007 <= row['ANY_FABRICACIO'] < 2012:
                    return 'Euro 4'
                elif 2012 <= row['ANY_FABRICACIO'] < 2017:
                    return 'Euro 5'
                elif 2016 <= row['ANY_FABRICACIO'] < 2021:
                    return 'Euro 6 a/b/c'
                elif 2020 <= row['ANY_FABRICACIO'] < 2021:
                    return 'Euro 6 d-temp'
                elif row['ANY_FABRICACIO'] >= 2021:
                    return 'Euro 6 d'
            elif row['Fuel'] == 'Battery Electric':
                return None

    # Technology classification of Heavy Duty Trucks
    elif row['Category'] == 'Heavy Duty Trucks':
        if row['Fuel'] == 'Diesel' or row['Fuel'] == 'Petrol' or row['Fuel'] == 'Diesel Hybrid':
            if row['ANY_FABRICACIO'] < 1992:
                return 'Conventional'
            elif 1992 <= row['ANY_FABRICACIO'] < 1996:
                return 'Euro I'
            elif 1996 <= row['ANY_FABRICACIO'] < 2000:
                return 'Euro II'
            elif 2000 <= row['ANY_FABRICACIO'] < 2005:
                return 'Euro III'
            elif 2005 <= row['ANY_FABRICACIO'] < 2009:
                return 'Euro IV'
            elif 2009 <= row['ANY_FABRICACIO'] < 2013:
                return 'Euro V'
            elif 2013 <= row['ANY_FABRICACIO'] < 2020:
                return 'Euro VI A/B/C'
            elif row['ANY_FABRICACIO'] >= 2020:
                return 'Euro VI D/E'
        elif row['Fuel'] == 'Diesel Hybrid':
            return None
        else:
            info_logger.warning('Heavy Duty Truck with no Euro Standard:')
            info_logger.warning(row)

    # Technology classification of Buses
    elif row['Category'] == 'Buses':
        if row['Fuel'] == 'Diesel':
            if row['ANY_FABRICACIO'] < 1992:
                return 'Conventional'
            elif 1992 <= row['ANY_FABRICACIO'] < 1996:
                return 'Euro I'
            elif 1996 <= row['ANY_FABRICACIO'] < 2000:
                return 'Euro II'
            elif 2000 <= row['ANY_FABRICACIO'] < 2005:
                return 'Euro III'
            elif 2005 <= row['ANY_FABRICACIO'] < 2009:
                return 'Euro IV'
            elif 2009 <= row['ANY_FABRICACIO'] < 2013:
                return 'Euro V'
            elif 2013 <= row['ANY_FABRICACIO'] < 2020:
                return 'Euro VI A/B/C'
            elif row['ANY_FABRICACIO'] >= 2020:
                return 'Euro VI D/E'
        elif row['Fuel'] == 'Diesel Hybrid':
            if 2012 <= row['ANY_FABRICACIO'] < 2020:
                return 'Euro VI A/B/C'
            elif row['ANY_FABRICACIO'] >= 2020:
                return 'Euro VI D/E'
        else:
            info_logger.warning('Bus with no Euro Standard: ')
            info_logger.warning(row)

    # Technology classification of L-Category
    elif row['Category'] == 'L-Category':
        if row['Fuel'] == 'Diesel' or row['Fuel'] == 'Petrol':
            if row['ANY_FABRICACIO'] < 1999:
                return 'Conventional'
            elif 1999 <= row['ANY_FABRICACIO'] < 2003:
                return 'Euro 1'
            elif 2003 <= row['ANY_FABRICACIO'] < 2006:
                return 'Euro 2'
            elif 2006 <= row['ANY_FABRICACIO'] < 2013:
                return 'Euro 3'
            elif 2013 <= row['ANY_FABRICACIO'] < 2020:
                return 'Euro 4'
            elif row['ANY_FABRICACIO'] >= 2020:
                return 'Euro 5'
        else:
            return None
    elif row['Category'] == 'Off Road':
        return None
    else:
        info_logger.warning('Heavy Duty Truck with no Euro Standard:')
        info_logger.warning(row)
        return None
