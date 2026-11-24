# andorra-fleet-activity
Aquest mòdul permet tractar l’Excel del Registre de vehicles i les seves dades respecte a les revisions ITV per tal de:
* Classificar els vehicles segons la seva categoria, utilitzant les classificacions de COPERT (és el estàndard de la Unió Europea pel càlcul d’emissions dels vehicles).
* Obtenció de l'estoc a una data de referència (31/12 de l'any d'estudi) i dels patrons d’activitat (km/any) segons la tipologia de vehicle (permet el càlcul del consum dels vehicles amb COPERT).
* Generació de gràfics per l’anàlisi de les dades.
* Generació de fitxers `.log` amb detalls de les operacions de neteja de dades i càlculs realitzats.
* Preparació de les dades per a COPERT i LEAP, i càrrega a Google Cloud (Cloud Storage i BigQuery).

## Entorn
```
pip install -r requirements.txt          # pandas, openpyxl, plotly, pyarrow i llibreries de Google Cloud
pip install -r requirements-dev.txt      # només per executar les proves
python -m pytest tests
```

## Execució
Copiar l’Excel del registre de vehicles a la carpeta ``_data`` del repositori (o a l'arrel) i executar:

```
python main.py --settings settings_2026                    # càlcul + gràfics (estudi de l'any 2025)
python main.py --settings settings_2026 --stage calculate  # només el càlcul
python main.py --settings settings_2026 --stage charts     # només els gràfics, a partir de les taules ja calculades
python main.py --settings settings_2026 --stage export --copert-results consum_total_copert_2026.xlsx   # fitxer per a LEAP, a partir de l'exportació de COPERT
python main.py --settings settings_2026 --stage upload     # Cloud Storage i BigQuery (veure docs/cloud.md)
python main.py --settings settings_2023                    # estudi de validació de l'any 2023 (Excel del 2024)
```

Les etapes són `calculate` → `charts` → `export` → `upload`. Els gràfics només llegeixen les taules agregades, així un canvi d'estètica no obliga a repetir el càlcul.

## Configuració
Cada estudi té un fitxer de configuració (``settings_2026.py``, ``settings_2023.py``) amb només els valors que canvien:

* RAW_FILENAME: nom de l'Excel del registre de vehicles (es busca a ``_data`` i a l'arrel del repositori).
* SNAPSHOT_DATE: data d'extracció del registre. Surt als noms dels fitxers i a la columna `snapshot_date`.
* STUDY_YEAR: any de l'estudi. L'estoc és el de la data de referència REFERENCE_DATE (per defecte *31/12* de STUDY_YEAR, com a l'informe de transport elèctric 2023) i els vehicles són dels últims 30 anys (MIN_YEAR = STUDY_YEAR - 29).
* COVID_MILEAGE_ACTIVE: `True` per calcular l'activitat només amb revisions ITV anteriors a COVID_START_DATE (l'estoc continua tenint tots els vehicles). Defecte: *False*.

La resta de paràmetres tenen un valor per defecte a ``pipeline/settings_loader.py`` (``DEFAULTS``) i es poden redefinir a cada fitxer:

| Paràmetre | Defecte | Descripció |
|---|---|---|
| MAX_AGE_YEARS | 30 | Antiguitat màxima dels vehicles |
| REFERENCE_DATE | 31/12 de STUDY_YEAR | Data de l'estoc |
| ACTIVITY_MAX_DATE | REFERENCE_DATE | Només es tenen en compte les revisions ITV fins aquesta data |
| MIN_DAYS_BETWEEN_REVISIONS | 150 | Revisions més properes es fusionen (es queda la més recent) |
| MIN_STOCK_FOR_MEAN_ACTIVITY_CALCULATION | 50 | Mínim de vehicles d'una agrupació per donar per vàlida la mitjana |
| USE_SINGLE_ITV | False | Activitat dels vehicles amb una sola ITV (km / dies des de l'alta) |
| SEGMENT_RANDOM_SEED | 42 | Llavor de la redistribució de segments (resultats reproduïbles) |
| IQR_MAX_FACTOR / IQR_MIN_FACTOR / MIN_ACTIVITY_FLOOR | 5 / 1.5 / 250 | Valors atípics de l'activitat |
| PHEV_ELECTRICITY_SHARE | 0.40 | Part de l'energia dels PHEV que és electricitat (LEAP) |
| ELECTRIC_MOTORCYCLES_MJ_PER_100KM | 16 | Consum de les motos elèctriques (LEAP) |
| GCP_PROJECT, GCS_BUCKET, BQ_LOCATION, BQ_DATASET_* | — | Google Cloud (veure docs/cloud.md) |

El diccionari ``MAPPING_CATEGORY_LAST_EURO_STANDARD`` (últimes normatives Euro de cada categoria) és a ``classification/MappingConstants.py``:
``last_euro`` ha de coincidir amb l'últim Euro que assigna ``EuroStandard.py`` (per a turismes i furgonetes, *Euro 6 d/e*).

## Sortides
Tot es guarda a ``output/<AAAAMMDD de l'extracció>/``. Els noms són en minúscules, sense espais ni accents:
``<contingut>_<any d'estudi>_<AAAAMMDD>.<extensió>``

| Carpeta | Contingut |
|---|---|
| `curated/` | `fleet_vehicles_*` (csv i parquet): un registre per vehicle, classificat i amb la seva activitat, el mètode (`activity_method`) i els parells d'ITV usats (`itv_pairs_used`) |
| `aggregated/` | `fleet_stock_activity_*` (estoc i activitat per categoria, amb el nivell d'agrupació usat `Activity_Grouping`), `fleet_stock_by_manufacturing_year_*`, `fleet_stock_by_registration_year_*` |
| `qa/` | Vehicles amb dades errònies: cilindrada de turismes fora de 560-8500 cm³ (descartats de l'estoc), motos de menys de 40 cm³, activitat fora de rang, quilometratge decreixent entre ITV |
| `charts/` | Gràfics HTML i `index.html` amb els enllaços |
| `exports/copert/`, `exports/leap/` | Fitxers d'entrada de COPERT i d'importació a LEAP |
| arrel | `debug_<any>.log` i `info_<any>.log` |

Totes les taules tenen les columnes `snapshot_date` i `study_year`. La columna `Mileage_between_itv_km_sum` és la suma de km entre ITV de períodes diferents, **no** és un quilometratge anual i no s'envia a COPERT ni a LEAP.

## Ingesta
El mòdul `ingestion` carrega l'Excel. Si falta alguna de les columnes obligatòries s'atura amb un error (les columnes noves només es registren al log):

```
'TIPUS', 'ANY_FABRICACIO', 'DATA_ALTA', 'DATA_BAIXA', 'MARCA', 'MODEL', 'CARBURANT', 'KW', 'CV', 'CO2', 'UNITATS_CO2',
'CC_CM3', 'PES_BUIT', 'PES_TOTAL_MÀXIM', i 'DATA_DARRERA_ITV' / 'KM_DARRERA_ITV' (de l'1 al 5)
```

Les dates s'interpreten amb format `AAAAMMDD`; si una data no és vàlida només s'utilitza l'any (queda al log). Els anys de fabricació buits queden com a nuls i es registra quants n'hi ha.

## Neteja de dades
`data_cleaning/Filters.py` (`filter_fleet_stock_at_reference_date`) obté l'estoc a la data de referència:
* Any de fabricació entre MIN_YEAR i STUDY_YEAR.
* Alta (`DATA_ALTA`) fins a la data de referència.
* Sense baixa (`DATA_BAIXA` buida) o amb baixa posterior a la data de referència.
* Sense carburant "SENSE CARBURANT".

El log mostra el nombre de vehicles després de cada filtre. Si l'Excel té valors nous de `TIPUS` o `CARBURANT` que no són als diccionaris de `MappingConstants.py`, l'execució s'atura indicant quins són i quants vehicles hi ha.

## Classificació
`ClassificationWrapper.py` encapsula les funcions del mòdul. La tipologia es defineix amb 4 classificacions:
1. **Category**: segons el TIPUS de vehicle, les categories de COPERT (`Passenger Cars`, `Light Commercial Vehicles`, `Heavy Duty Trucks`, `Buses`, `L-Category`, `Off Road`). Detalls a `MappingConstants.py`.
2. **Fuel**: segons el carburant. Detalls a `MappingConstants.py`.
3. **Segment**: segons el pes en buit, la cilindrada o la potència. Detalls a `CopertSegmentIdentification.py`.
4. **Euro Standard**: segons l'any de fabricació i la categoria. Detalls a `EuroStandard.py`.

**Re-classificació** (`ReClassification.py`): les tipologies FURGONETES, CAMIONETES i CAMIONS es solapen amb Light Commercial Vehicles (menys de 3500 kg) i Heavy Duty Trucks (3500 kg o més); les motos amb "trial" al model passen a Off Road.

**Cilindrada**: els turismes no elèctrics amb cilindrada coneguda fora de 560-8500 cm³ es descarten (queden a `qa/`). Els que no tenen cilindrada es queden i el segment s'assigna com a continuació.

**Redistribució de segment** (`SegmentRedistribution.py`): els vehicles sense dades de pes o cilindrada reben un segment segons la freqüència dels segments **de la seva mateixa categoria**, amb una llavor fixa. Es fa abans de calcular l'Euro Standard, que en depèn en alguns casos.

## Activitat
Per cada tipologia resultant (al voltant de 200) es calcula l'activitat mitjana (km/any) a partir de l'activitat de cada vehicle (`activity/ActivityCalculator.py`):

1. Es llisten les revisions ITV (fins a 5) amb data i quilometratge, fins a ACTIVITY_MAX_DATE, de la més recent a la més antiga.
2. Les revisions separades per menys de MIN_DAYS_BETWEEN_REVISIONS dies es fusionen (ITV no passada repetida la setmana següent), quedant-se amb la més recent.
3. S'agafa el primer parell de revisions consecutives amb quilometratge creixent, començant pel més recent. Si un parell no és vàlid es prova l'anterior. L'activitat és km / dies × 365.
4. Si el vehicle només té una ITV i USE_SINGLE_ITV és `True`, es fa servir el quilometratge de la ITV entre els dies des de l'alta.
5. L'activitat acumulada (`Lifetime Activity`) és el quilometratge de l'última ITV vàlida.

A cada vehicle es guarda `activity_method` (`itv_pair`, `single_itv`, `no_activity`) i `itv_pairs_used` (posició del parell usat, 1 és el més recent).

L'activitat fora de rang (superior a Q3 + 5 × IQR o inferior al màxim entre Q1 − 1.5 × IQR i 250 km/any) no es té en compte en la mitjana i la desviació estàndard.

Hi ha tipologies que no compleixen l'estoc mínim. En aquests casos es fa una agrupació menys restrictiva fins a arribar-hi, i es guarda a `Activity_Grouping` quina s'ha usat. Ordre de prioritat:

1. Mateixa tipologia (Category, Fuel, Segment, Euro Standard)
2. Euro Standard anterior o anteriors (per als vehicles nous, sense revisions ITV)
3. Category, Fuel, Segment
4. Category, Fuel, Euro Standard
5. Category, Fuel
6. Category, Segment
7. Category

Els híbrids (dièsel o gasolina) es consideren dièsel o gasolina. Per als vehicles elèctrics es fa servir la categoria.

## Gràfics
Es generen els següents gràfics (carpeta `charts/`, amb `index.html`):
* Gràfic circular de l’estoc de vehicles en funció de la categoria
* Gràfics de barres de l’estoc per any de fabricació i tipologia (colors i ordre a `charts/Colors.py`, `CHART_CONFIG`)
* Gràfics circulars de l’estoc de cada categoria segons la classificació Euro (els vehicles sense Euro surten com a "Sin Euro")
* Gràfic de barres horitzontal de l’activitat mitjana en km/any per tipologia

Totes les funcions retornen la figura; amb `--show` s'obren al navegador.

## COPERT i LEAP
* `exports/copert/copert_stock_activity_*.csv`: `Category, Fuel, Segment, Euro Standard, Stock, Mean_Activity, Mean_Lifetime_Activity`. **Pendent de confirmar la plantilla d'importació de COPERT**; mentrestant es mantenen aquests noms de columna.
* `exports/leap/`: a partir dels resultats d'energia de COPERT, tal com els exporta (Excel amb el full `EXPORT`, columnes `Emission, Category, Fuel, Segment, Euro Standard, EC [TJ], …, Total`; també val un CSV `Category, Fuel, Segment, Energy_TJ`), es genera l'Excel de demanda final d'electricitat amb el format de `energy_demand_electric_transport_2023.xlsx`: vehicles elèctrics, el 40 % dels PHEV i les motos elèctriques (que COPERT no cobreix) calculades amb l'estoc, l'activitat mitjana i el consum (16 MJ/100 km, com a l'informe 2023). Se sumen tots els tipus d'emissió (Hot, Cold, A/C, Evaporation) i les branques sense energia (p. ex. autobusos elèctrics) no hi surten. Amb el fitxer `consum_total_copert_2023_andorra.xlsx` i `stock_activity_2023.csv` es reprodueix la Taula 3 de l'informe 2023 (11,233 TJ).

## Google Cloud
Veure `docs/cloud.md` (estructura del bucket, taules de BigQuery, càrrega idempotent, permisos i Cloud Run Job).

## Estructura del codi
```
main.py            executa les etapes
settings_*.py      configuració de cada estudi
pipeline/          càlcul, gràfics, noms de sortida i càrrega de la configuració
ingestion/  data_cleaning/  classification/  activity/  charts/  logger/
exports/           fitxers per a LEAP
cloud/             Cloud Storage i BigQuery
tests/             proves (pytest)
```
