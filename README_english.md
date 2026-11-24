# vehicle_fleet_activity
Analysis of the ITV data of the vehicle register of Andorra (Excel format) to estimate the stock and the activity
(km/year) of the fleet per vehicle type, so the fuel consumption can be estimated with COPERT and LEAP.
The complete documentation (in Catalan) is in `README.md`.

## Dependencies
```
pip install -r requirements.txt
pip install -r requirements-dev.txt   # to run the tests: python -m pytest tests
```

## Run
```
python main.py --settings settings_2026                   # calculation + charts (study of the year 2025)
python main.py --settings settings_2026 --stage calculate
python main.py --settings settings_2026 --stage charts    # charts from the aggregated tables
python main.py --settings settings_2026 --stage export --copert-results consum_total_copert_2026.xlsx   # file for LEAP, from the export of COPERT
python main.py --settings settings_2026 --stage upload    # Cloud Storage and BigQuery (see docs/cloud.md)
python main.py --settings settings_2023                   # validation study of the year 2023
```
Each study has a settings file (``settings_2026.py``): Excel file name, extraction date of the register (SNAPSHOT_DATE) and
study year (STUDY_YEAR). The stock is the one at 31/12 of the study year, for the vehicles of the last 30 years. The other
parameters have a default value in ``pipeline/settings_loader.py``.

Results are saved in ``output/<AAAAMMDD of the extraction>/{curated, aggregated, qa, charts, exports}``, with names like
``fleet_stock_activity_2025_20261019.csv``.

## Activity
The activity of each vehicle (km/year) comes from its ITV revisions up to the end of the study year: close revisions
(less than 150 days) are merged, and the first pair of consecutive revisions with increasing mileage, starting from the most
recent one, is used. The method and the pair used are saved for each vehicle (``activity_method``, ``itv_pairs_used``).

The function ``activity_stats_calculator_by_grouping`` calculates the Mean Activity for the vehicle partition types:
Category, Fuel, Segment and Euro Standard that do not have enough units by itself (minimum number 50 by default),
by grouping by different partitions until one of them has enough vehicles in the grouping.
The assigment of Mean activity is done following the next order of groupings, and returns the Mean Activity if the minimum
COUNT is reached, otherwise returns nan. The grouping used is saved in the column ``Activity_Grouping``.
It takes the following data by order:
1. Same Category, Fuel, Segment and Euro Standard
2. Previous Euro Standards (for new vehicles with no ITV data)
3. Category, Fuel, Segment
4. Category, Fuel, Euro Standard
5. Category, Fuel
6. Category, Segment
7. Category
