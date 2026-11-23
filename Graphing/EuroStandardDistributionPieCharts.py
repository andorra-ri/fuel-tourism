from pathlib import Path

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

from Classification import CATEGORIES
from .Colors import NO_EURO_LABEL


def euro_distribution_pie_charts(categorized_vehicles_df: pd.DataFrame, output_folder, show: bool = False
                                 ) -> go.Figure:
    """
    Figure containing the Euro distribution pie chart for every Category. Vehicles with no Euro Standard
    (ex: electric vehicles) are shown with the label "Sin Euro"

    :param categorized_vehicles_df: Dataframe of the categorized vehicles registration list
    :param output_folder: output folder name where to store resulting chart
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
        df = categorized_vehicles_df[categorized_vehicles_df['Category'] == category]
        data = df.groupby(['Euro Standard'], dropna=False).size().reset_index(name='Stock')
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

    filename = Path(output_folder) / "Distribució Euro per categoria.html"
    pie_charts.write_html(filename)
    if show:
        pie_charts.show()
    return pie_charts
