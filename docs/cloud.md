# Google Cloud: Cloud Storage, BigQuery i Cloud Run Job

Aquest codi **no s'ha provat contra un projecte real de Google Cloud**: la lògica de càrrega es comprova amb clients
simulats (`tests/test_outputs_and_cloud.py`). Abans de fer-lo servir en producció cal fer una primera execució amb un
projecte de proves.

## Configuració
Al fitxer de l'estudi (ex: `settings_2026.py`):

```python
GCP_PROJECT = 'el-meu-projecte'
GCS_BUCKET = 'el-meu-bucket'      # a la mateixa regió europea que els datasets
BQ_LOCATION = 'EU'                # (per defecte)
```

## Cloud Storage (capes)
```
gs://<bucket>/raw/<AAAAMMDD>/<excel original>          sense modificar, per data d'extracció
gs://<bucket>/curated/<AAAAMMDD>/fleet_vehicles_*      parquet i csv
gs://<bucket>/aggregated/<AAAAMMDD>/fleet_*            csv
```

## BigQuery
| Dataset | Taules i vistes |
|---|---|
| `fuel_curated` (privat) | `vehicles`: un registre per vehicle |
| `fuel_aggregated` | `stock_activity`, `stock_by_manufacturing_year`, `stock_by_registration_year`; vistes `copert_stock_activity` i `leap_stock_activity` |

* Les columnes estan en `snake_case` (`euro_standard`, `lifetime_activity`, `mean_activity`) i amb tipus explícit (`cloud/schema.py`). Els fitxers per a COPERT i LEAP mantenen els seus noms de columna: la vista `copert_stock_activity` els recupera.
* Totes les taules són particionades per `snapshot_date` i tenen `study_year`.
* **Càrrega idempotent**: abans de carregar, s'esborren les files amb el mateix `snapshot_date` i `study_year`; repetir una execució no duplica dades, i es poden carregar diversos anys d'estudi del mateix Excel.

## Accés a les dades per vehicle (B7)
`fuel_curated.vehicles` té una fila per vehicle (matrícula inclosa). Deixar-lo privat, amb permisos restringits, i
compartir només el dataset `fuel_aggregated`.

## Cloud Run Job
El `Dockerfile` executa `python main.py` amb els arguments del job. Els registres van a la sortida estàndard.

```bash
# Imatge
gcloud builds submit --tag europe-west1-docker.pkg.dev/<projecte>/<repo>/fleet-activity

# Compte de servei amb els rols: Storage Object Admin al bucket, BigQuery Data Editor i BigQuery Job User
gcloud iam service-accounts create fleet-activity-job

# Job (l'Excel s'ha de pujar abans a gs://<bucket>/raw/<AAAAMMDD>/)
gcloud run jobs create fleet-activity-2026 \
  --image europe-west1-docker.pkg.dev/<projecte>/<repo>/fleet-activity \
  --region europe-west1 --service-account fleet-activity-job@<projecte>.iam.gserviceaccount.com \
  --memory 4Gi --task-timeout 30m \
  --args="--settings,settings_2026,--stage,all"

gcloud run jobs execute fleet-activity-2026 --region europe-west1
```

Si l'Excel no és a la carpeta local, l'etapa `calculate` el descarrega de `raw/<AAAAMMDD>/`. Perquè el job també
carregui a BigQuery, executar-lo una segona vegada amb `--stage,upload` (o encadenar-lo amb Cloud Scheduler).

Els valors de memòria, regió i temps són orientatius: la prova local amb l'Excel de 2026 triga uns 2-3 minuts.
