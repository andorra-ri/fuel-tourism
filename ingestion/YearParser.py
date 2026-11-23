def year_of_manufacturing_parser(year) -> int:
    """ Parse the ANY_FABRICACIO column to an integer. Accepts 2015, '2015' and 2015.0, returns None if not valid"""
    try:
        return int(float(year))
    except (ValueError, TypeError, OverflowError):
        return None
