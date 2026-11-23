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


def check_cloud_settings(settings: SimpleNamespace, bucket_needed: bool = True):
    """GCP_PROJECT is always needed; GCS_BUCKET only to use Cloud Storage (BigQuery does not need it)"""
    if not settings.GCP_PROJECT or (bucket_needed and not settings.GCS_BUCKET):
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


def files_to_upload(settings: SimpleNamespace, paths: OutputPaths) -> list:
    """
    (blob name, local file) to upload. Only the aggregated tables, that have no data of individual vehicles, unless
    UPLOAD_CURATED (one row per vehicle) or UPLOAD_RAW (the original Excel, with the plate numbers) are True.
    """
    files = []
    for file in sorted(paths.aggregated.glob('*')):
        files.append((f'aggregated/{paths.snapshot}/{file.name}', file))
    if getattr(settings, 'UPLOAD_CURATED', False):
        for file in sorted(paths.curated.glob('*')):
            files.append((f'curated/{paths.snapshot}/{file.name}', file))
    if getattr(settings, 'UPLOAD_RAW', False):
        files.append((raw_blob_name(settings), Path(settings.path_registre_vehicles)))
    return files


def upload_files(settings: SimpleNamespace, paths: OutputPaths, storage_client=None) -> list:
    """Upload the files of files_to_upload to Cloud Storage. Returns the blob names"""
    check_cloud_settings(settings)
    if storage_client is None:
        from google.cloud import storage
        storage_client = storage.Client(project=settings.GCP_PROJECT)
    bucket = storage_client.bucket(settings.GCS_BUCKET)

    uploaded = []
    for blob_name, file in files_to_upload(settings, paths):
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
    check_cloud_settings(settings, bucket_needed=False)
    if bigquery_module is None:
        from google.cloud import bigquery as bigquery_module
    if bigquery_client is None:
        bigquery_client = bigquery_module.Client(project=settings.GCP_PROJECT)

    datasets = [settings.BQ_DATASET_AGGREGATED]
    if getattr(settings, 'UPLOAD_CURATED', False):
        datasets.append(settings.BQ_DATASET_CURATED)
    for dataset in datasets:
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

    if getattr(settings, 'UPLOAD_CURATED', False):
        # Vehicles: the types of the columns come from the parquet file, that keeps them
        vehicles = pd.read_parquet(paths.fleet_vehicles_parquet)
        schema = curated_schema(vehicles)
        load_table(bigquery_client, bigquery_module, settings.GCP_PROJECT, settings.BQ_DATASET_CURATED, 'vehicles',
                   prepare_table(vehicles, schema), schema, snapshot_date, settings.STUDY_YEAR, settings.BQ_LOCATION)

    for sql in (copert_view_sql(settings.GCP_PROJECT, settings.BQ_DATASET_AGGREGATED),
                leap_view_sql(settings.GCP_PROJECT, settings.BQ_DATASET_AGGREGATED)):
        bigquery_client.query(sql, location=settings.BQ_LOCATION).result()


def upload_plan(settings: SimpleNamespace, paths: OutputPaths) -> list:
    """Lines that describe what the stage upload would create and upload, without touching Google Cloud"""
    lines = [f'Project: {settings.GCP_PROJECT}  Location: {settings.BQ_LOCATION}']
    bucket = settings.GCS_BUCKET or '(no bucket defined: Cloud Storage is skipped)'
    lines.append(f'Bucket: {bucket}')
    for blob_name, file in files_to_upload(settings, paths):
        lines.append(f'  file   gs://{settings.GCS_BUCKET or "<bucket>"}/{blob_name}   <-  {file.name}')
    datasets = [settings.BQ_DATASET_AGGREGATED] + ([settings.BQ_DATASET_CURATED]
                                                    if getattr(settings, 'UPLOAD_CURATED', False) else [])
    for dataset in datasets:
        lines.append(f'  dataset {settings.GCP_PROJECT}.{dataset} (created if it does not exist)')
    for table in AGGREGATED_SCHEMAS:
        lines.append(f'  table   {settings.GCP_PROJECT}.{settings.BQ_DATASET_AGGREGATED}.{table}  '
                     f'(rows of snapshot {paths.snapshot}, study {settings.STUDY_YEAR} replaced)')
    lines.append(f'  views   copert_stock_activity, leap_stock_activity in {settings.BQ_DATASET_AGGREGATED}')
    return lines


def run_upload(settings: SimpleNamespace, paths: OutputPaths, dry_run: bool = False):
    """
    Run the stage upload: Cloud Storage (if there is a bucket defined) and BigQuery.
    With dry_run only the plan is shown, nothing is created or uploaded.
    """
    if dry_run:
        for line in upload_plan(settings, paths):
            print(line)
        return
    if settings.GCS_BUCKET:
        upload_files(settings, paths)
    else:
        logger.warning('GCS_BUCKET is not defined: the files are not uploaded to Cloud Storage')
    load_bigquery(settings, paths)
