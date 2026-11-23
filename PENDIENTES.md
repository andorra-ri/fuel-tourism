# Pendientes (rama `update-2026`)

Hecho y comprobado: estudio 2025 con el Excel de 2026 (84.658 vehículos, 208 categorías), validación 2023 con el Excel de 2024,
clasificación validada contra `Stock_Configuration_Andorra.csv` de COPERT, 60 pruebas, pandas 2.2.2 y 3.0.5.

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
   de entrada de la actividad por categoría.
7. **Formato de los resultados de COPERT** para generar el Excel de LEAP. Supuesto: CSV `Category, Fuel, Segment, Energy_TJ`.
8. **Motos eléctricas:** 0,0736 TJ (Excel de LEAP) frente a 0,0588 (informe y fórmula). Confirmar la vigente.
9. **Área de Transportes:** por qué el histórico cambia entre ficheros (stock 2023: 79.131 con el Excel de 2024, 81.348 con el
   de 2026), identificador de vehículo (`TIPUS + MATRICULA` no coincide entre ficheros), duplicados (1.422 y 1.583) y altas
   con fecha futura (hasta 2029 en el Excel de 2024).
10. **Diferencia con el informe 2023:** 79.136 frente a 78.780 (+0,4 %). Falta saber qué filtro del informe lo explica.

## Técnicos

11. **Google Cloud sin probar contra un proyecto real** (solo con clientes simulados). Proyecto `ari-datahub`, región
    `europe-west9`, solo tablas agregadas (dataset `aggregated_fleet`). **Falta decidir el bucket** (`GCS_BUCKET`); hasta
    entonces la etapa `upload` omite Cloud Storage. Ensayo sin tocar nada: `python main.py --settings settings_2026 --stage upload --dry-run`.
12. **Renombrar el repositorio a `andorra-fleet-activity`** en GitHub: lo tiene que hacer un administrador de la organización
    (`gh repo rename andorra-fleet-activity`). Dentro del código ya se llama así (README, Docker); el paquete Python sigue siendo
    un conjunto de carpetas, no `andorra_fleet_activity`.
13. **Integrar la rama:** `update-2026` parte de `update-2024`; falta abrir PR y decidir qué hacer con `main`.
14. **Cobertura de actividad:** solo el 1,7 % de los fabricados desde 2022 tiene actividad propia; el resto usa el Euro anterior
    (`Activity_Grouping` lo indica por categoría).
15. **Covid:** no se ha medido el efecto en los pares de ITV que cruzan 2020 (`COVID_MILEAGE_ACTIVE` está apagado).
