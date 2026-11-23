"""
Upload of the results to Google Cloud.

Cloud Storage (bucket in a European region):
    raw/<AAAAMMDD>/<excel file>                        original Excel, without modification
    curated/<AAAAMMDD>/fleet_vehicles_*.parquet|csv
    aggregated/<AAAAMMDD>/fleet_*.csv
BigQuery: datasets fuel_curated (vehicles) and fuel_aggregated (stock_activity, stock_by_manufacturing_year,
stock_by_registration_year and two views). The tables are partitioned by snapshot_date. The load is idempotent:
the rows of the same snapshot_date and study_year are deleted before loading them, so repeating a run does not
duplicate data.

The libraries google-cloud-storage and google-cloud-bigquery are only needed to run this stage.
"""
import logging
from pathlib import Path
from types import SimpleNamespace

import pandas as pd

from cloud.schema import (
    AGGREGATED_SCHEMAS, curated_schema, snake_case_schema, copert_view_sql, leap_view_sql
)
from pipeline.paths import OutputPaths

logger = logging.getLogger('logger' + '.cloud')


def check_cloud_settings(settings: SimpleNamespace):
    if not settings.GCP_PROJECT or not settings.GCS_BUCKET:
        raise ValueError('GCP_PROJECT and GCS_BUCKET must be defined in the settings to use Google Cloud')


def raw_blob_name(settings: SimpleNamespace) -> str:
    return f'raw/{settings.SNAPSHOT_DATE.strftime("%Y%m%d")}/{settings.RAW_FILENAME}'


def download_raw_file(settings: SimpleNamespace) -> Path:
    """Download the original Excel from the bucket (raw/<AAAAMMDD>/) if it is not in the local folders"""
    check_cloud_settings(settings)
    from google.cloud import storage
    path = Path(settings.path_registre_vehicles)
    path.parent.mkdir(parents=True, exist_ok=True)
    storage.Client(project=settings.GCP_PROJECT).bucket(settings.GCS_BUCKET).blob(raw_blob_name(settings)) \
        .download_to_filename(str(path))
    logger.info(f'Excel downloaded from gs://{settings.GCS_BUCKET}/{raw_blob_name(settings)}')
    return path


def upload_files(settings: SimpleNamespace, paths: OutputPaths, storage_client=None) -> list:
    """Upload the original Excel and the curated and aggregated files to Cloud Storage. Returns the blob names"""
    check_cloud_settings(settings)
    if storage_client is None:
        from google.cloud import storage
        storage_client = storage.Client(project=settings.GCP_PROJECT)
    bucket = storage_client.bucket(settings.GCS_BUCKET)

    files = [(raw_blob_name(settings), Path(settings.path_registre_vehicles))]
    for folder_name, folder in (('curated', paths.curated), ('aggregated', paths.aggregated)):
        for file in sorted(folder.glob('*')):
            files.append((f'{folder_name}/{paths.snapshot}/{file.name}', file))

    uploaded = []
    for blob_name, file in files:
        if not file.exists():
            logger.warning(f'File not uploaded, it does not exist: {file}')
            continue
        bucket.blob(blob_name).upload_from_filename(str(file))
        uploaded.append(blob_name)
        logger.info(f'Uploaded gs://{settings.GCS_BUCKET}/{blob_name}')
    return uploaded


def prepare_table(df: pd.DataFrame, schema: dict) -> pd.DataFrame:
    """Dataframe with the columns of the schema, with their types and the names in snake_case"""
    missing = [column for column in schema if column not in df.columns]
    if missing:
        raise ValueError(f'Columns missing in the table: {missing}')
    result = df[list(schema)].copy()
    for column, type_ in schema.items():
        if type_ == 'DATE':
            result[column] = pd.to_datetime(result[column]).dt.date
        elif type_ == 'INT64':
            result[column] = pd.to_numeric(result[column], errors='coerce').astype('Int64')
        elif type_ == 'FLOAT64':
            result[column] = pd.to_numeric(result[column], errors='coerce').astype('float64')
        else:
            result[column] = result[column].astype('string')
    result.columns = [column for column in snake_case_schema(schema)]
    return result


def load_table(bigquery_client, bigquery_module, project: str, dataset: str, table: str, df: pd.DataFrame,
               schema: dict, snapshot_date, study_year: int, location: str):
    """
    Load the dataframe to the table partitioned by snapshot_date, replacing the rows of the same snapshot_date and
    study_year if they already exist.
    """
    table_id = f'{project}.{dataset}.{table}'
    bq_schema = [bigquery_module.SchemaField(column, type_) for column, type_ in snake_case_schema(schema).items()]
    try:
        bigquery_client.get_table(table_id)
        table_exists = True
    except Exception:  # google.api_core.exceptions.NotFound
        table_exists = False

    if table_exists:
        job = bigquery_client.query(
            f'DELETE FROM `{table_id}` WHERE snapshot_date = @snapshot_date AND study_year = @study_year',
            job_config=bigquery_module.QueryJobConfig(query_parameters=[
                bigquery_module.ScalarQueryParameter('snapshot_date', 'DATE', snapshot_date),
                bigquery_module.ScalarQueryParameter('study_year', 'INT64', study_year)]),
            location=location)
        job.result()

    job_config = bigquery_module.LoadJobConfig(
        schema=bq_schema,
        write_disposition=bigquery_module.WriteDisposition.WRITE_APPEND,
        time_partitioning=bigquery_module.TimePartitioning(
            type_=bigquery_module.TimePartitioningType.DAY, field='snapshot_date'),
        clustering_fields=['study_year'])
    bigquery_client.load_table_from_dataframe(df, table_id, job_config=job_config, location=location).result()
    logger.info(f'Loaded {df.shape[0]} rows to {table_id}')


def load_bigquery(settings: SimpleNamespace, paths: OutputPaths, bigquery_client=None, bigquery_module=None):
    """Create the datasets, load the tables and create the views"""
    check_cloud_settings(settings)
    if bigquery_module is None:
        from google.cloud import bigquery as bigquery_module
    if bigquery_client is None:
        bigquery_client = bigquery_module.Client(project=settings.GCP_PROJECT)

    for dataset in (settings.BQ_DATASET_CURATED, settings.BQ_DATASET_AGGREGATED):
        dataset_object = bigquery_module.Dataset(f'{settings.GCP_PROJECT}.{dataset}')
        dataset_object.location = settings.BQ_LOCATION
        bigquery_client.create_dataset(dataset_object, exists_ok=True)

    snapshot_date = settings.SNAPSHOT_DATE.date()
    aggregated_files = {'stock_activity': paths.stock_activity,
                        'stock_by_manufacturing_year': paths.stock_by_manufacturing_year,
                        'stock_by_registration_year': paths.stock_by_registration_year}
    for table, file in aggregated_files.items():
        schema = AGGREGATED_SCHEMAS[table]
        df = prepare_table(pd.read_csv(file), schema)
        load_table(bigquery_client, bigquery_module, settings.GCP_PROJECT, settings.BQ_DATASET_AGGREGATED, table, df,
                   schema, snapshot_date, settings.STUDY_YEAR, settings.BQ_LOCATION)

    # Vehicles: the types of the columns come from the parquet file, that keeps them
    vehicles = pd.read_parquet(paths.fleet_vehicles_parquet)
    schema = curated_schema(vehicles)
    load_table(bigquery_client, bigquery_module, settings.GCP_PROJECT, settings.BQ_DATASET_CURATED, 'vehicles',
               prepare_table(vehicles, schema), schema, snapshot_date, settings.STUDY_YEAR, settings.BQ_LOCATION)

    for sql in (copert_view_sql(settings.GCP_PROJECT, settings.BQ_DATASET_AGGREGATED),
                leap_view_sql(settings.GCP_PROJECT, settings.BQ_DATASET_AGGREGATED)):
        bigquery_client.query(sql, location=settings.BQ_LOCATION).result()


def run_upload(settings: SimpleNamespace, paths: OutputPaths):
    """Run the stage upload: Cloud Storage and BigQuery"""
    upload_files(settings, paths)
    load_bigquery(settings, paths)
