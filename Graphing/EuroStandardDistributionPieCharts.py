from pathlib import Path

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

from Classification import CATEGORIES
from .Colors import NO_EURO_LABEL


def euro_distribution_pie_charts(stock_activity_df: pd.DataFrame, output_file, show: bool = False
                                 ) -> go.Figure:
    """
    Figure containing the Euro distribution pie chart for every Category. Vehicles with no Euro Standard
    (ex: electric vehicles) are shown with the label "Sin Euro"

    :param stock_activity_df: aggregated table of the stock, with the columns Category, Euro Standard and Stock
    :param output_file: path of the html file where to store the resulting chart
    :param show: if True, the figure is also opened in the browser (for local use)
    :return: the figure. It is also saved in an html file containing the EURO distribution pie charts per each Category
    """
    # Subplots definition
    specs = [[{'type': 'domain'}, {'type': 'domain'}], [{'type': 'domain'}, {'type': 'domain'}],
             [{'type': 'domain'}, {'type': 'domain'}]]
    pie_charts = make_subplots(rows=3, cols=2, specs=specs, horizontal_spacing=0.01, vertical_spacing=0.06,
                               subplot_titles=CATEGORIES)
    rows = [1, 1, 2, 2, 3, 3]

    # Creation of each subplot, one per category
    for i, category in enumerate(CATEGORIES):
        col = 2 if i % 2 == 1 else 1
        df = stock_activity_df[stock_activity_df['Category'] == category]
        data = df.groupby(['Euro Standard'], dropna=False, as_index=False).agg(Stock=('Stock', 'sum'))
        data['Euro Standard'] = data['Euro Standard'].fillna(NO_EURO_LABEL)
        legend_group = 'group2' if i == 2 or i == 3 else 'group1'
        pie_charts.add_trace(go.Pie(
            labels=data['Euro Standard'],
            values=data['Stock'],
            textinfo='percent+value',
            texttemplate='%{value:.0f}<br>%{percent:.2%}',
            legendgroup=legend_group
        ), rows[i], col)

    pie_charts.update_layout(
        title="Distribució de l'estoc de vehicles, per cada categoria segons categories EURO",
        title_x=0.5,
        height=1200,
        width=1000,
        legend={'traceorder': 'grouped'}
    )

    pie_charts.write_html(Path(output_file))
    if show:
        pie_charts.show()
    return pie_charts
