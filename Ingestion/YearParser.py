def year_of_manufacturing_parser(year: str) -> int:
    """ Parse the ANY_FABRICACIO column to an integer"""
    year = str(year)
    try:
        year = int(year)
        return year
    except ValueError as e:
        return None
