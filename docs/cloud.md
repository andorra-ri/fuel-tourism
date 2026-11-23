# Google Cloud: Cloud Storage i BigQuery (ari-datahub)

Aquest codi **no s'ha provat contra un projecte real de Google Cloud**: la lògica de càrrega es comprova amb clients
simulats (`tests/test_outputs_and_cloud.py`). L'ordre recomanat és assajar-ho primer sense tocar res:

```
python main.py --settings settings_2026 --stage upload --dry-run
```

Mostra el projecte, els fitxers, els datasets i les taules que es crearien. No utilitza Google Cloud.

## Què es puja
**Només les taules agregades** (estoc i activitat per categoria, estoc per any de fabricació i per any d'alta). No tenen
dades de vehicles individuals. L'Excel original (amb matrícules) i la taula per vehicle (`curated`) **no es pugen**,
tret que es posi `UPLOAD_RAW = True` o `UPLOAD_CURATED = True` al fitxer de l'estudi.

## Configuració
Valors per defecte a `pipeline/settings_loader.py`, es poden redefinir al fitxer de l'estudi (ex: `settings_2026.py`):

```python
GCP_PROJECT = 'ari-datahub'
GCS_BUCKET = None                      # pendent de decidir; sense bucket s'omet Cloud Storage
BQ_LOCATION = 'europe-west9'           # com els buckets del datahub
BQ_DATASET_AGGREGATED = 'aggregated_fleet'
```

## Cloud Storage
```
gs://<bucket>/aggregated/<AAAAMMDD>/fleet_*     csv
```
Els fitxers `raw/` i `curated/` només existeixen si s'activen els indicadors anteriors.

## BigQuery
| Dataset | Taules i vistes |
|---|---|
| `aggregated_fleet` | `stock_activity`, `stock_by_manufacturing_year`, `stock_by_registration_year`; vistes `copert_stock_activity` i `leap_stock_activity` |

* Les columnes estan en `snake_case` (`euro_standard`, `mean_activity`) i amb tipus explícit (`cloud/schema.py`). Els fitxers per a COPERT i LEAP mantenen els seus noms de columna: la vista `copert_stock_activity` els recupera.
* Taules particionades per `snapshot_date`, amb la columna `study_year`.
* **Càrrega idempotent**: abans de carregar, s'esborren les files amb el mateix `snapshot_date` i `study_year`; repetir una execució no duplica dades.
* Si `UPLOAD_CURATED = True`, la taula `vehicles` (un registre per vehicle, matrícula inclosa) va al dataset `curated_fleet`, que ha de quedar privat i amb permisos restringits.

## Execució
```
gcloud auth application-default login
python main.py --settings settings_2026 --stage upload
```

L'etapa crea el dataset si no existeix i carrega les taules. El bucket només es fa servir si `GCS_BUCKET` està definit.

## Cloud Run Job (opcional)
El `Dockerfile` executa `python main.py` amb els arguments del job. Els registres van a la sortida estàndard.

```bash
gcloud builds submit --tag europe-west9-docker.pkg.dev/ari-datahub/<repo>/andorra-fleet-activity
gcloud run jobs create andorra-fleet-activity-2026 \
  --image europe-west9-docker.pkg.dev/ari-datahub/<repo>/andorra-fleet-activity \
  --region europe-west9 --memory 4Gi --task-timeout 30m \
  --args="--settings,settings_2026,--stage,all"
```

Si l'Excel no és a la carpeta local i hi ha bucket, l'etapa `calculate` el descarrega de `raw/<AAAAMMDD>/`; això només té
sentit si l'Excel s'hi ha pujat abans (`UPLOAD_RAW`). El compte de servei necessita Storage Object Admin al bucket,
BigQuery Data Editor i BigQuery Job User.
