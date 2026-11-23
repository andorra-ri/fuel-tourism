"""
Stage 2: charts. Only reads the aggregated tables saved by the stage 1 (stock and activity per category, stock per year
of manufacturing), so a change in the aspect of a chart does not require to repeat the calculation.
"""
import html
import logging
from types import SimpleNamespace

import pandas as pd

from charts import (
    euro_distribution_pie_charts,
    stock_per_category_pie_chart,
    stock_per_manufacturing_year_and_category_bar_charts,
    activity_horizontal_bar_chart
)
from pipeline.paths import OutputPaths

logger = logging.getLogger('logger' + '.charts_stage')

CHART_TITLES = {
    'stock_by_category': 'Estoc segons tipologia de vehicle',
    'euro_distribution': "Distribució de l'estoc per categoria segons categories EURO",
    'stock_by_manufacturing_year': 'Parc de vehicles actius per any de fabricació i tipologia',
    'mean_activity': "Activitat mitjana anual segons classificació del parc de vehicles d'Andorra",
}


def write_index(paths: OutputPaths, settings: SimpleNamespace):
    """index.html with the links to the charts"""
    links = '\n'.join(
        f'<li><a href="{paths.chart(name).name}">{html.escape(title)}</a></li>' for name, title in CHART_TITLES.items())
    page = (f'<html><head><meta charset="utf-8"><title>Parc de vehicles {settings.STUDY_YEAR}</title></head><body>\n'
            f'<h1>Parc de vehicles d\'Andorra {settings.STUDY_YEAR}</h1>\n'
            f'<p>Registre d\'ITV extret el {settings.SNAPSHOT_DATE.date()}</p>\n<ul>\n{links}\n</ul>\n</body></html>\n')
    paths.charts_index.write_text(page, encoding='utf-8')


def run_charts(settings: SimpleNamespace, paths: OutputPaths, show: bool = False):
    """
    Run the stage 2.

    :param show: open the charts in the browser (for local use)
    """
    stock_activity = pd.read_csv(paths.stock_activity)
    stock_by_manufacturing_year = pd.read_csv(paths.stock_by_manufacturing_year)

    paths.charts.mkdir(parents=True, exist_ok=True)
    logger.info('Creating charts')
    stock_per_category_pie_chart(stock_activity, paths.chart('stock_by_category'), show=show)
    euro_distribution_pie_charts(stock_activity, paths.chart('euro_distribution'), show=show)
    stock_per_manufacturing_year_and_category_bar_charts(
        stock_by_manufacturing_year, paths.chart('stock_by_manufacturing_year'), show=show)
    activity_horizontal_bar_chart(stock_activity, paths.chart('mean_activity'), show=show)
    write_index(paths, settings)
