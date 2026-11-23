"""Load the settings module of a study (ex: settings_2026) and complete it with the default values and derived values"""
import importlib
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace

DEFAULTS = {
    'MAX_AGE_YEARS': 30,                          # Vehicles of the last 30 years, counting the study year
    'MIN_DAYS_BETWEEN_REVISIONS': 150,            # Closer ITV revisions are merged (as in the report of 2023)
    'MIN_STOCK_FOR_MEAN_ACTIVITY_CALCULATION': 50,  # Min number of vehicles in a grouping to take its mean activity
    'USE_SINGLE_ITV': False,                      # Activity of vehicles with a single ITV (since registration)
    'COVID_MILEAGE_ACTIVE': False,
    'COVID_START_DATE': datetime(2019, 3, 1),
    'SEGMENT_RANDOM_SEED': 42,                    # Seed to assign Segment to vehicles with erroneous data
    # Outliers of the activity (IQR method)
    'IQR_MAX_FACTOR': 5,
    'IQR_MIN_FACTOR': 1.5,
    'MIN_ACTIVITY_FLOOR': 250,
    # Output folder (output/<AAAAMMDD of the extraction>/...) and folders where to look for the Excel file
    'OUTPUT_FOLDER': 'output',
    'DATA_FOLDERS': ['_data', '.'],
    # Parameters to calculate the electricity demand for LEAP (see exports/leap.py)
    'PHEV_ELECTRICITY_SHARE': 0.40,               # Share of the energy of the PHEV vehicles that is electricity
    'ELECTRIC_MOTORCYCLES_MJ_PER_100KM': 16,
    # Google Cloud (see cloud/). The upload is only done if the project and the bucket are defined
    'GCP_PROJECT': None,
    'GCS_BUCKET': None,
    'BQ_LOCATION': 'EU',
    'BQ_DATASET_CURATED': 'fuel_curated',
    'BQ_DATASET_AGGREGATED': 'fuel_aggregated',
}
REQUIRED = ['RAW_FILENAME', 'SNAPSHOT_DATE', 'STUDY_YEAR']


def find_input_file(filename: str, folders, base_folder: Path) -> Path:
    """Path of the file in the first of the folders that contains it. If it is not found, the one in the first folder"""
    candidates = [(base_folder / folder / filename) for folder in folders]
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def load_settings(module_name: str, base_folder: Path = None) -> SimpleNamespace:
    """
    :param module_name: name of the python module with the settings of the study, ex: 'settings_2026'
    :param base_folder: folder the relative paths refer to (default: the working directory)
    :return: namespace with the settings of the module, the default values and the derived values:
        MIN_YEAR, MAX_YEAR, REFERENCE_DATE, ACTIVITY_MAX_DATE, path_registre_vehicles
    """
    base_folder = Path(base_folder) if base_folder else Path.cwd()
    module = importlib.import_module(module_name)
    values = dict(DEFAULTS)
    values.update({name: getattr(module, name) for name in dir(module) if name.isupper()})

    missing = [name for name in REQUIRED if name not in values]
    if missing:
        raise ValueError(f'Settings {module_name} has no value for: {missing}')

    study_year = values['STUDY_YEAR']
    values.setdefault('MAX_YEAR', study_year)
    values.setdefault('MIN_YEAR', study_year - values['MAX_AGE_YEARS'] + 1)
    values.setdefault('REFERENCE_DATE', datetime(study_year, 12, 31))
    values.setdefault('ACTIVITY_MAX_DATE', values['REFERENCE_DATE'])
    values['SETTINGS_NAME'] = module_name
    values['BASE_FOLDER'] = base_folder
    values['path_registre_vehicles'] = find_input_file(values['RAW_FILENAME'], values['DATA_FOLDERS'], base_folder)
    return SimpleNamespace(**values)
