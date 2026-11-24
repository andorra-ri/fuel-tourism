"""
Electricity demand for LEAP (Final Energy Demand, fuel Electricity, branch Demand\\Transport, units Terajoules), in the
same format as energy_demand_electric_transport_2023.xlsx: one row per branch Category\\Fuel\\Segment and one column per
year.

The energy of the vehicles is calculated by COPERT from the stock and activity of the stage calculate
(exports/copert/copert_stock_activity_*.csv). This module needs the results of COPERT as exported by COPERT (as
consum_total_copert_2023_andorra.xlsx, sheet EXPORT) in an Excel or csv file with the columns:

    Emission, Category, Fuel, Segment, Euro Standard, EC [TJ], ..., Total     (energy consumption in terajoules)

All the types of Emission (Hot, Cold, A/C, Evaporation) are added, as in the report of 2023 (1812 TJ), as well as the
rows of the same Category, Fuel and Segment. A csv with the columns Category, Fuel, Segment and Energy_TJ is also valid.

It builds the electricity demand with these rules, as in the report of 2023:
    - Battery electric vehicles: all their energy is electricity.
    - PHEV vehicles: a share of their energy (PHEV_ELECTRICITY_SHARE, 40 %) is electricity.
    - Electric motorcycles: COPERT does not cover them, their energy is calculated from the stock and the mean
      activity of the electric L-Category vehicles and a consumption of ELECTRIC_MOTORCYCLES_MJ_PER_100KM.
"""
import logging
from types import SimpleNamespace

import pandas as pd
from openpyxl import Workbook

from pipeline.paths import OutputPaths

logger = logging.getLogger('logger' + '.leap')

PHEV_FUELS = ['Petrol PHEV', 'Diesel PHEV']
ELECTRIC_FUEL = 'Battery electric'
ELECTRIC_MOTORCYCLES_SEGMENT = 'Electric Motorcycles'
MJ_IN_A_TERAJOULE = 1_000_000
COPERT_RESULTS_COLUMNS = ['Category', 'Fuel', 'Segment', 'Energy_TJ']
COPERT_EXPORT_SHEET = 'EXPORT'
COPERT_EXPORT_ENERGY_COLUMN = 'Total'
COPERT_EXPORT_POLLUTANT_COLUMN = 'EC [TJ]'
COPERT_ENERGY_CONSUMPTION = 'EC'
LEAP_HEADER = ['Final Energy Demand', 'Fuel: Electricity', 'Branch: Demand\\Transport', 'Units: Terajoules']


def leap_name(name: str) -> str:
    """Name of a Category or Segment in LEAP: the hyphen is an underscore (ex: Large-SUV-Executive)"""
    return str(name).replace('-', '_')


def electric_motorcycles_energy_tj(stock_activity_df: pd.DataFrame, mj_per_100km: float) -> float:
    """
    Electricity demand (TJ) of the electric motorcycles: vehicles x mean activity (km/year) x consumption.
    Ex (report 2023): 143 vehicles x 2572 km x 16 MJ/100 km = 0.0588 TJ
    """
    electric = stock_activity_df[(stock_activity_df['Category'] == 'L-Category') &
                                 (stock_activity_df['Fuel'] == ELECTRIC_FUEL)]
    total_km = (electric['Stock'] * electric['Mean_Activity']).sum()
    return float(total_km * mj_per_100km / 100 / MJ_IN_A_TERAJOULE)


def read_copert_results(path) -> pd.DataFrame:
    """Results of COPERT from an Excel file (sheet EXPORT, or the first one) or a csv file"""
    path = str(path)
    if path.lower().endswith(('.xlsx', '.xlsm', '.xls')):
        sheets = pd.ExcelFile(path).sheet_names
        return pd.read_excel(path, sheet_name=COPERT_EXPORT_SHEET if COPERT_EXPORT_SHEET in sheets else sheets[0])
    return pd.read_csv(path)


def copert_energy_column(copert_results_df: pd.DataFrame) -> pd.DataFrame:
    """
    Return the results of COPERT with the column Energy_TJ. In the export of COPERT it is the column Total, and only the
    rows of energy consumption are kept (column 'EC [TJ]' = EC), if the file has that column.
    """
    results = copert_results_df.copy()
    if COPERT_EXPORT_POLLUTANT_COLUMN in results.columns:
        results = results[results[COPERT_EXPORT_POLLUTANT_COLUMN] == COPERT_ENERGY_CONSUMPTION]
    if 'Energy_TJ' not in results.columns and COPERT_EXPORT_ENERGY_COLUMN in results.columns:
        results['Energy_TJ'] = results[COPERT_EXPORT_ENERGY_COLUMN]
    missing = [column for column in COPERT_RESULTS_COLUMNS if column not in results.columns]
    if missing:
        raise ValueError(f'The results of COPERT must have the columns Category, Fuel, Segment and Total (export of '
                         f'COPERT) or Energy_TJ, missing: {missing}')
    return results


def build_leap_electricity_table(copert_results_df: pd.DataFrame, stock_activity_df: pd.DataFrame,
                                 phev_electricity_share: float, electric_motorcycles_mj_per_100km: float
                                 ) -> pd.DataFrame:
    """
    :param copert_results_df: results of COPERT (see the module documentation)
    :param stock_activity_df: stock and activity table of the stage calculate
    :return: dataframe with the columns Branch and Energy_TJ, sorted by branch
    """
    energy = copert_energy_column(copert_results_df)
    energy = energy[~((energy['Category'] == 'L-Category') & (energy['Fuel'] == ELECTRIC_FUEL))]
    energy = energy[energy['Fuel'].isin([ELECTRIC_FUEL] + PHEV_FUELS)]
    energy['Energy_TJ'] = pd.to_numeric(energy['Energy_TJ'], errors='raise')
    energy.loc[energy['Fuel'].isin(PHEV_FUELS), 'Energy_TJ'] *= phev_electricity_share
    energy = energy.groupby(['Category', 'Fuel', 'Segment'], as_index=False, dropna=False).agg(
        Energy_TJ=('Energy_TJ', 'sum'))
    energy = energy[energy['Energy_TJ'] > 0]  # branches without energy (ex: electric buses) are not in LEAP
    energy['Branch'] = energy.apply(
        lambda row: '\\'.join([leap_name(row['Category']), row['Fuel'], leap_name(row['Segment'])]), axis=1)
    table = energy[['Branch', 'Energy_TJ']]

    motorcycles = electric_motorcycles_energy_tj(stock_activity_df, electric_motorcycles_mj_per_100km)
    if motorcycles > 0:
        motorcycles_row = pd.DataFrame({'Branch': [f'L_Category\\{ELECTRIC_FUEL}\\{ELECTRIC_MOTORCYCLES_SEGMENT}'],
                                        'Energy_TJ': [motorcycles]})
        table = pd.concat([table, motorcycles_row], ignore_index=True)
    return table.sort_values('Branch').reset_index(drop=True)


def write_leap_excel(table: pd.DataFrame, year: int, path) -> None:
    """Excel file in the format of the LEAP import: header, a row per branch with the energy of the year, and Total"""
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = 'Sheet1'
    for line in LEAP_HEADER:
        sheet.append([line])
    sheet.append([])
    sheet.append(['Branch', year])
    for branch, energy in zip(table['Branch'], table['Energy_TJ']):
        sheet.append([branch, float(energy)])
    sheet.append(['Total', float(table['Energy_TJ'].sum())])
    sheet.column_dimensions['A'].width = 44.7
    for row in sheet.iter_rows(min_row=7, min_col=2, max_col=2):
        row[0].number_format = '#,##0.000'
    workbook.save(path)


def run_leap_export(settings: SimpleNamespace, paths: OutputPaths, copert_results_file: str = None):
    """
    Create the Excel file for LEAP in exports/leap/ from the results of COPERT and the stock and activity table.

    :param copert_results_file: Excel or csv file with the results of COPERT (see the module documentation)
    """
    if not copert_results_file:
        raise ValueError('The export for LEAP needs the results of COPERT: use --copert-results file.xlsx '
                         '(export of COPERT, or csv with the columns Category, Fuel, Segment, Energy_TJ)')
    copert_results = read_copert_results(copert_results_file)
    stock_activity = pd.read_csv(paths.stock_activity)
    table = build_leap_electricity_table(copert_results, stock_activity, settings.PHEV_ELECTRICITY_SHARE,
                                         settings.ELECTRIC_MOTORCYCLES_MJ_PER_100KM)
    paths.exports_leap.mkdir(parents=True, exist_ok=True)
    write_leap_excel(table, settings.STUDY_YEAR, paths.leap_electricity_demand)
    logger.info(f'File for LEAP saved: {paths.leap_electricity_demand}. Total: {table["Energy_TJ"].sum():.3f} TJ')
