"""
Settings of the study of the stock and activity of the fleet of the year 2025, with the register of ITV extracted
on 19/10/2026. Run with:  python main.py --settings settings_2026

Only the values that change for each study are defined here. The rest of the parameters have a default value defined in
pipeline/settings_loader.py (DEFAULTS).
"""
from datetime import datetime

# ITV original data filename (searched in the folder _data and in the working directory)
RAW_FILENAME = '19OCT2026_Historic_vehicles_amb_ITVs.xlsx'

# Date of the extraction of the register: it is used in the names of the output files and folders (snapshot_date)
SNAPSHOT_DATE = datetime(2026, 10, 19)

# Year of the study. The stock is the one of the REFERENCE_DATE (default 31/12 of the study year), the same date used
# in the report of electric transport of 2023. Vehicles of the last 30 years (manufactured from STUDY_YEAR - 29)
STUDY_YEAR = 2025

# To keep the whole stock but calculate the activity before covid, set True
COVID_MILEAGE_ACTIVE = False
