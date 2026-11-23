"""
Settings to reproduce the study of the year 2023 (report of electric transport 2023) with the register of ITV
extracted on 22/04/2024. Run with:  python main.py --settings settings_2023

Only the values that change for each study are defined here. The rest of the parameters have a default value defined in
pipeline/settings_loader.py (DEFAULTS).
"""
from datetime import datetime

# ITV original data filename (searched in the folder _data and in the working directory)
RAW_FILENAME = '22APR2024_Historic_vehicles_amb_ITVs.xlsx'

# Date of the extraction of the register: it is used in the names of the output files and folders (snapshot_date)
SNAPSHOT_DATE = datetime(2024, 4, 22)

# Year of the study (stock at 31/12/2023, vehicles manufactured from 1994, as the report of 2023)
STUDY_YEAR = 2023

# To keep the whole stock but calculate the activity before covid, set True
COVID_MILEAGE_ACTIVE = False
