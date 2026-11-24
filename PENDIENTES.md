# Pendientes (rama `update-2026`)

Hecho y comprobado: estudio 2025 con el Excel de 2026 (84.658 vehículos, 208 categorías), validación 2023 con el Excel de 2024,
clasificación validada contra `Stock_Configuration_Andorra.csv` de COPERT, 64 pruebas, pandas 2.2.2 y 3.0.5.

## Decisiones tuyas

1. **Años de cada Euro.** El manual EMEP/EEA (tabla 2-2) da los años de *primera matriculación*; el código usa el año de
   *fabricación* con un año de retraso. Con el criterio del manual, 4.276 de 56.765 turismos de gasolina/diésel (7,5 %) cambian
   de nivel Euro, p. ej. 2.284 de 2014–2015 pasarían de Euro 5 a Euro 6 a/b/c. Hay que elegir: año de fabricación o de alta, y
   qué tabla. Cambia el stock por categoría y, por tanto, el consumo.
2. **Stock a 31/12 o medio anual.** Hoy es a 31/12/2025. 1.787 vehículos se dieron de baja durante 2025 y quedan fuera.
3. **150 días entre ITV para todas las categorías.** Lo fija el informe 2023; puede haber ITV semestrales.
4. **ITV única** (`USE_SINGLE_ITV`): apagada. Sube la cobertura del 60,9 % al 70,3 % pero sesga la media (+5 %).
5. **Off Road** no va a COPERT (no está en su configuración). Confirmar cómo se trata.

## Necesito datos o confirmación de otros

6. **Plantilla de importación de COPERT.** El stock ya valida contra su configuración (0 categorías fuera); falta el formato
   de entrada de la actividad por categoría (el fichero `Andorra_fleet_tier2.cop` ya está en la carpeta, pero es un zip con un binario propio de COPERT que no se
   puede leer sin el programa; la usuaria importa un CSV). El `stock_activity_2023.csv` del informe tiene 219 categorías, con Mileage, Min, Max y Std; el nuestro 206 para COPERT
   (sin Off Road ni las que COPERT no cubre) y 210 en `fleet_stock_activity`.
7. ~~**Formato de los resultados de COPERT**~~ Resuelto: `exports/leap.py` lee la hoja `EXPORT` de COPERT (suma todos los
   tipos de emisión). Con los ficheros de 2023 reproduce la Tabla 3 del informe (11,233 TJ).
8. **Motos eléctricas:** el 0,0736 TJ del Excel de LEAP son 143 × 2.572 km × **20** MJ/100 km; el informe y el código usan
   **16** MJ/100 km (0,0588). Además el Excel de LEAP es ~0,27 % mayor en todas las filas (otra pasada de COPERT).
   Confirmar el consumo vigente (16 o 20 MJ/100 km).
9. **Área de Transportes:** por qué el histórico cambia entre ficheros (stock 2023: 79.131 con el Excel de 2024, 81.348 con el
   de 2026), identificador de vehículo (`TIPUS + MATRICULA` no coincide entre ficheros), duplicados (1.422 y 1.583) y altas
   con fecha futura (hasta 2029 en el Excel de 2024).
10. **Diferencia con el informe 2023:** 79.136 frente a 78.780 (+0,4 %). Falta saber qué filtro del informe lo explica.

## Técnicos

11. **Google Cloud:** primera carga real hecha el 23/11/2026 (estudio 2025). Bucket `raw_fleet_activity` y dataset
    `aggregated_fleet` en `ari-datahub` (`europe-west9`), solo tablas agregadas. Repetir la carga no duplica filas
    (comprobado). Pendiente: permisos de lectura para quien use las tablas, y decidir si el Cloud Run Job (`Dockerfile`)
    se va a usar. Ensayo sin tocar nada: `--stage upload --dry-run`.
12. **Renombrar el repositorio a `vehicle_fleet_activity`** en GitHub: lo tiene que hacer un administrador de la organización
    (`gh repo rename vehicle_fleet_activity`). Dentro del código ya se llama así (README, Docker); el paquete Python sigue siendo
    un conjunto de carpetas, no `vehicle_fleet_activity`. Después del cambio: `git remote set-url origin <nueva URL>`.
    Imagen y Cloud Run Job se llaman `vehicle-fleet-activity` (guiones, por las reglas de Artifact Registry y Cloud Run).
13. **Integrar la rama:** `update-2026` parte de `update-2024`; falta abrir PR y decidir qué hacer con `main`.
14. **Cobertura de actividad:** solo el 1,7 % de los fabricados desde 2022 tiene actividad propia; el resto usa el Euro anterior
    (`Activity_Grouping` lo indica por categoría).
15. **Covid:** no se ha medido el efecto en los pares de ITV que cruzan 2020 (`COVID_MILEAGE_ACTIVE` está apagado).
