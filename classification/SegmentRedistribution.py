import numpy as np
import pandas as pd
from .MappingConstants import CATEGORIES
# TODO: Solve problem with normal_distribution values


def fill_nan_with_frequency(df: pd.DataFrame, column_name: str, seed: int = 42, eligible_rows: pd.Series = None):
    """
    Fill na values of a given column, for every Category, with the frequency distribution of that same Category.
    Categories with no values in the column (ex: Off Road) are skipped.

    :param df: dataframe with a Category column. It is modified in place
    :param column_name: column whose nan values are filled
    :param seed: seed of the random generator, so every execution gives the same result
    :param eligible_rows: optional boolean mask, only rows where it is True are filled
    """
    rng = np.random.default_rng(seed)
    for category in CATEGORIES:
        in_category = df['Category'] == category
        distribution = df.loc[in_category, column_name].value_counts(normalize=True)
        if distribution.empty:
            continue
        rows_to_fill = in_category & df[column_name].isna()
        if eligible_rows is not None:
            rows_to_fill = rows_to_fill & eligible_rows
        number_of_rows = int(rows_to_fill.sum())
        if number_of_rows == 0:
            continue
        df.loc[rows_to_fill, column_name] = rng.choice(
            distribution.index.to_numpy(), p=distribution.values, size=number_of_rows)
