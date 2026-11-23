from datetime import datetime
from types import SimpleNamespace
from unittest import mock

import pandas as pd
import pytest

from cloud import schema, upload
from exports.leap import build_leap_electricity_table, electric_motorcycles_energy_tj, write_leap_excel
from pipeline.paths import OutputPaths
from data_cleaning.type_conversion import convert_to_integer_df_columns


def make_settings(tmp_path):
    return SimpleNamespace(SNAPSHOT_DATE=datetime(2026, 10, 19), STUDY_YEAR=2025, BASE_FOLDER=tmp_path,
                           OUTPUT_FOLDER='output', GCP_PROJECT='project', GCS_BUCKET='bucket', BQ_LOCATION='EU',
                           BQ_DATASET_CURATED='curated_fleet', BQ_DATASET_AGGREGATED='aggregated_fleet',
                           UPLOAD_RAW=False, UPLOAD_CURATED=False,
                           RAW_FILENAME='raw.xlsx', path_registre_vehicles=tmp_path / 'raw.xlsx')


# ---- output names
def test_output_paths_convention(tmp_path):
    paths = OutputPaths(make_settings(tmp_path))
    assert paths.stock_activity == tmp_path / 'output' / '20261019' / 'aggregated' / 'fleet_stock_activity_2025_20261019.csv'
    assert paths.chart('mean_activity').name == 'chart_mean_activity_2025_20261019.html'
    paths.create_folders()
    assert paths.exports_leap.is_dir() and paths.qa.is_dir()


def test_values_without_calculation_are_not_exported_as_zero():
    df = pd.DataFrame({column: [1.4, None, 3.6] for column in
                       ['Mean_Activity', 'Min_Activity', 'Max_Activity', 'Std_Activity', 'Mean_Lifetime_Activity']})
    convert_to_integer_df_columns(df)
    assert df['Mean_Activity'].tolist()[0] == 1 and pd.isna(df['Mean_Activity'].iloc[1])


# ---- LEAP
def test_electric_motorcycles_energy_as_in_the_report_2023():
    stock = pd.DataFrame({'Category': ['L-Category'], 'Fuel': ['Battery electric'], 'Stock': [143],
                          'Mean_Activity': [2572]})
    assert electric_motorcycles_energy_tj(stock, 16) == pytest.approx(0.0588, abs=1e-4)


def test_leap_table_and_excel(tmp_path):
    stock = pd.DataFrame({'Category': ['L-Category'], 'Fuel': ['Battery electric'], 'Stock': [143],
                          'Mean_Activity': [2572]})
    copert = pd.DataFrame({
        'Category': ['Passenger Cars', 'Passenger Cars', 'Passenger Cars', 'Passenger Cars', 'L-Category'],
        'Fuel': ['Battery electric', 'Petrol PHEV', 'Petrol PHEV', 'Petrol', 'Battery electric'],
        'Segment': ['Large-SUV-Executive', 'Medium', 'Medium', 'Small', 'x'],
        'Energy_TJ': [1.6, 5.0, 5.426, 100, 9]})
    table = build_leap_electricity_table(copert, stock, 0.4, 16)
    assert table['Branch'].tolist() == ['L_Category\\Battery electric\\Electric Motorcycles',
                                        'Passenger Cars\\Battery electric\\Large_SUV_Executive',
                                        'Passenger Cars\\Petrol PHEV\\Medium']
    assert table['Energy_TJ'].iloc[2] == pytest.approx(4.1704)  # 40 % of the energy of the PHEV is electricity

    import openpyxl
    write_leap_excel(table, 2025, tmp_path / 'leap.xlsx')
    rows = list(openpyxl.load_workbook(tmp_path / 'leap.xlsx').active.iter_rows(values_only=True))
    assert rows[0][0] == 'Final Energy Demand' and rows[5] == ('Branch', 2025) and rows[-1][0] == 'Total'
    assert rows[-1][1] == pytest.approx(table['Energy_TJ'].sum())


def test_leap_needs_the_columns_of_copert():
    with pytest.raises(ValueError):
        build_leap_electricity_table(pd.DataFrame({'Category': []}), pd.DataFrame(), 0.4, 16)


# ---- BigQuery
@pytest.mark.parametrize('name, expected', [('Euro Standard', 'euro_standard'), ('Lifetime Activity', 'lifetime_activity'),
                                            ('Mean_Activity', 'mean_activity'), ('PES_TOTAL_MÀXIM', 'pes_total_maxim'),
                                            ('DATA_DARRERA_ITV2', 'data_darrera_itv2')])
def test_snake_case(name, expected):
    assert schema.to_snake_case(name) == expected


def test_curated_schema_types():
    df = pd.DataFrame({'DATA_ALTA': pd.to_datetime(['2020-01-01']), 'ANY_FABRICACIO': pd.array([2020], dtype='Int32'),
                       'Activity': [1.5], 'Category': ['Passenger Cars']})
    assert schema.curated_schema(df) == {'DATA_ALTA': 'DATE', 'ANY_FABRICACIO': 'INT64', 'Activity': 'FLOAT64',
                                         'Category': 'STRING', 'snapshot_date': 'DATE', 'study_year': 'INT64'}


def test_prepare_table_has_snake_case_columns_and_types():
    df = pd.DataFrame({'snapshot_date': ['2026-10-19'], 'study_year': [2025], 'Category': ['Buses'], 'Fuel': ['Diesel'],
                       'Segment': [None], 'ANY_FABRICACIO': [2020.0], 'Stock': [3]})
    table = upload.prepare_table(df, schema.AGGREGATED_SCHEMAS['stock_by_manufacturing_year'])
    assert table.columns.tolist() == ['snapshot_date', 'study_year', 'category', 'fuel', 'segment', 'any_fabricacio',
                                      'stock']
    assert str(table['any_fabricacio'].dtype) == 'Int64'


def test_load_table_deletes_the_same_snapshot_and_study_before_loading():
    client, bigquery = mock.MagicMock(), mock.MagicMock()
    df = pd.DataFrame({'snapshot_date': [datetime(2026, 10, 19).date()], 'study_year': [2025]})
    upload.load_table(client, bigquery, 'project', 'dataset', 'table', df,
                      {'snapshot_date': 'DATE', 'study_year': 'INT64'}, datetime(2026, 10, 19).date(), 2025, 'EU')
    sql = client.query.call_args.args[0]
    assert 'DELETE FROM `project.dataset.table`' in sql and 'snapshot_date = @snapshot_date' in sql
    assert client.load_table_from_dataframe.called


def test_load_table_does_not_delete_if_the_table_does_not_exist():
    client, bigquery = mock.MagicMock(), mock.MagicMock()
    client.get_table.side_effect = Exception('Not found')
    df = pd.DataFrame({'snapshot_date': [datetime(2026, 10, 19).date()], 'study_year': [2025]})
    upload.load_table(client, bigquery, 'project', 'dataset', 'table', df,
                      {'snapshot_date': 'DATE', 'study_year': 'INT64'}, datetime(2026, 10, 19).date(), 2025, 'EU')
    assert not client.query.called and client.load_table_from_dataframe.called


def test_upload_files_uses_the_layers_of_the_bucket(tmp_path):
    settings = make_settings(tmp_path)
    paths = OutputPaths(settings)
    paths.create_folders()
    settings.path_registre_vehicles.write_text('excel')
    paths.stock_activity.write_text('a,b')
    storage_client = mock.MagicMock()
    paths.fleet_vehicles_csv.write_text('plate,1')
    uploaded = upload.upload_files(settings, paths, storage_client)
    # Only the aggregated tables: no data of individual vehicles nor the original Excel
    assert uploaded == ['aggregated/20261019/fleet_stock_activity_2025_20261019.csv']

    settings.UPLOAD_RAW = True
    settings.UPLOAD_CURATED = True
    uploaded = upload.upload_files(settings, paths, storage_client)
    assert 'raw/20261019/raw.xlsx' in uploaded
    assert 'curated/20261019/fleet_vehicles_2025_20261019.csv' in uploaded


def test_dry_run_does_not_use_google_cloud(tmp_path, capsys):
    settings = make_settings(tmp_path)
    settings.GCS_BUCKET = None
    paths = OutputPaths(settings)
    paths.create_folders()
    paths.stock_activity.write_text('a,b')
    with mock.patch.dict('sys.modules', {'google': None, 'google.cloud': None}):
        upload.run_upload(settings, paths, dry_run=True)
    output = capsys.readouterr().out
    assert 'aggregated_fleet' in output and 'curated' not in output and 'vehicles' not in output


def test_bigquery_does_not_need_the_bucket(tmp_path):
    settings = make_settings(tmp_path)
    settings.GCS_BUCKET = None
    upload.check_cloud_settings(settings, bucket_needed=False)


def test_cloud_settings_are_required(tmp_path):
    settings = make_settings(tmp_path)
    settings.GCS_BUCKET = None
    with pytest.raises(ValueError):
        upload.check_cloud_settings(settings)


def test_copert_view_has_the_same_rules_as_the_copert_file():
    sql = schema.copert_view_sql('project', 'dataset')
    assert "LPG Bifuel" in sql and "'Off Road'" in sql and "IFNULL(segment, '-')" in sql
