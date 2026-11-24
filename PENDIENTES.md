# Pendientes (rama `update-2026`)

Hecho y comprobado: estudio 2025 con el Excel de 2026 (84.658 vehículos, 217 categorías), validación 2023 con el
Excel de 2024 (219 categorías, como el informe), clasificación validada contra `Stock_Configuration_Andorra.csv` de COPERT,
65 pruebas, pandas 2.2.2 y 3.0.5. Tabla 3 del informe 2023 reproducida con el exportador de LEAP (11,233 TJ).

## Decisiones tomadas (24/11/2026)

* **Años de cada Euro:** se mantiene el año de fabricación con el retraso actual del código (decisión de la usuaria). Con los
  años de la tabla 2-2 de la guía EMEP/EEA cambiaría la categoría Euro de muchos vehículos (p. ej. 1.063 de 2.185 furgonetas
  diésel N1-II/N1-III del stock 2023, y el 7,5 % de los turismos), pero casi no cambiaría el consumo: en los resultados de COPERT
  los MJ/km son iguales entre Euro 5, 6 a/b/c, d-temp y d/e en turismos de gasolina y furgonetas diésel (en turismos diésel
  suben solo en d-temp y d/e). Afectaría sobre todo a emisiones contaminantes. Las furgonetas N1-II/N1-III (a/b/c = 2017–2019) quedan como están: el solape de 2016–2020 era un error (I4).
* **Método** (como el informe 2023): stock a 31/12 del año de estudio, 150 días entre ITV (paso a la ITV anterior o descarte),
  sin ITV única (`USE_SINGLE_ITV` apagado), vehículos de los últimos 30 años, Off Road como categoría propia que no va a COPERT.
* **Diésel híbridos:** se clasifican como `Diesel Hybrid` (371 turismos en 2023; el informe tenía 368). COPERT no tiene esa
  categoría: en su fichero se suman a `Passenger Cars - Diesel` (mismo segmento y Euro), asumiendo emisiones similares al
  diésel comparable. El stock se suma y la actividad se pondera por el stock. En la vista de BigQuery `copert_stock_activity`
  pasa lo mismo (ya en el código; hay que volver a ejecutar `--stage upload` para actualizarla).
* **Motos eléctricas:** 16 MJ/100 km. Los 0,0736 TJ del Excel de LEAP eran 143 × 2.572 km × 20 MJ/100 km, un cálculo antiguo.

## Cerrado

* **Formato de los resultados de COPERT para LEAP:** `exports/leap.py` lee la hoja `EXPORT` (suma todos los tipos de emisión).
* **Diferencia con el informe 2023** (79.136 frente a 78.780): el código antiguo (`update-2024`) reproduce exactamente 78.780 y
  descarta cualquier vehículo con fecha de baja. El nuevo conserva los que se dieron de baja entre enero y abril de 2024 (356),
  que a 31/12/2023 seguían en el parque, y descarta 86 turismos con cilindrada fuera de 560–8.500 cm³ (el informe lo describe, pero
  el código antiguo no lo aplicaba al stock).
* **Covid:** solo el 2,3 % de los pares de ITV usados cruzan el confinamiento (14/03–21/06/2020; el 3,8 % si se toma hasta marzo
  de 2021). Comparando dentro de cada vehículo, esos pares dan ~15 % menos km/año (turismos 0,85; motos 0,81–0,84; furgonetas
  0,80); parte del efecto es de la edad del par, así que es un máximo. Efecto en la media por categoría: turismos –0,3 %,
  furgonetas –0,4 %, motos –0,9 %. Se deja `COVID_MILEAGE_ACTIVE` apagado.

## Necesito datos o confirmación de otros

1. **Plantilla de importación de COPERT.** El stock valida contra su configuración (0 categorías fuera). Se importa un CSV como
   `stock_activity_2023.csv` (11 columnas: índice, Category, Fuel, Segment, Euro Standard, Stock, Mileage, Mean/Min/Max/Std_Activity,
   Mean_Lifetime_Activity); nuestro `copert_stock_activity_*.csv` tiene 7 columnas y 206 categorías (sin Off Road ni las que COPERT
   no cubre). Hay que confirmar qué columnas lee COPERT. `Andorra_fleet_tier2.cop` es un zip con un binario propio de COPERT:
   no se puede leer sin el programa.
2. **Validación con COPERT:** cargar el CSV de 2023 recalculado y comparar con la Tabla 3 del informe (con el método nuevo de
   actividad, la electricidad de 2023 subiría de 11,23 a unos 12,2 TJ, estimación proporcional a los km).
3. **Área de Transportes:** borrador de consultas en catalán (fichero local `docs/consultes_area_transports.md`, sin versionar
   porque el repositorio es público): identificador de vehículo (`MATRICULA` tiene formato distinto en los dos Excel y no hay
   ninguna coincidencia), por qué el histórico cambia entre extracciones (stock 2023: 79.136 frente a 81.350), matrículas
   repetidas, fechas no válidas, bajas e ITV.

## Técnicos

4. **Google Cloud:** primera carga real hecha el 23/11/2026 (estudio 2025). Bucket `raw_fleet_activity` y dataset
   `aggregated_fleet` en `ari-datahub` (`europe-west9`), solo tablas agregadas. Repetir la carga no duplica filas. Tras el cambio
   de los diésel híbridos hay que repetir la carga del estudio 2025 (la tabla `stock_activity` gana filas y la vista de COPERT
   cambia). Pendiente: permisos de lectura para quien use las tablas, decidir si el Cloud Run Job (`Dockerfile`) se va a usar y
   si la tabla pasa a llamarse `vehicle_fleet_stock_activity`. Ensayo sin tocar nada: `--stage upload --dry-run`.
5. **Renombrar el repositorio a `vehicle_fleet_activity`** en GitHub: parece que ya está hecho (al subir la rama, GitHub avisó
   de que el repositorio se ha movido a `https://github.com/andorra-ri/vehicle_fleet_activity.git`). Falta actualizar el remoto
   local: `git remote set-url origin https://github.com/andorra-ri/vehicle_fleet_activity.git`. Dentro del código ya se llama
   así (README, Docker); el paquete Python sigue siendo un conjunto de carpetas, no `vehicle_fleet_activity`.
   Imagen y Cloud Run Job se llaman `vehicle-fleet-activity` (guiones, por las reglas de Artifact Registry y Cloud Run).
6. **Integrar la rama:** `update-2026` parte de `update-2024`; PR #2 en borrador. Falta decidir qué hacer con `main`.
7. **`Andorra_fleet_tier2.cop`** (29,6 MB, binario): decidir si se deja fuera del repositorio (`.gitignore`), se sube tal cual o con
   Git LFS. De momento no está versionado. El Excel del registro (matrículas) ya está en `.gitignore`.
8. **Cobertura de actividad:** solo el 1,7 % de los fabricados desde 2022 tiene actividad propia; el resto usa el Euro anterior
   (`Activity_Grouping` lo indica por categoría).
