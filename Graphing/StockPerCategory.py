from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from Graphing.Colors import COLOR_DISCRETE_MAP


def stock_per_category_pie_chart(categorized_vehicles_df: pd.DataFrame, output_folder, show: bool = False) -> go.Figure:
    """
    Pie Chart of the stock by Category

    :param categorized_vehicles_df: Dataframe of the categorized vehicles registration list
    :param output_folder: output folder name where to store resulting chart
    :param show: if True, the figure is also opened in the browser (for local use)
    :return: the figure. It is also saved in an html file with the whole Stock distribution by Category
    """
    data = categorized_vehicles_df.groupby(['Category']).count()['Stock'].reset_index()
    pie_chart = px.pie(data, values='Stock', names='Category', color='Category',
                       title='Estoc segons tipologia de vehicle',
                       color_discrete_map=COLOR_DISCRETE_MAP)
    pie_chart.update_traces(
        textinfo='percent+value',
        texttemplate='%{value:.0f}<br>%{percent:.2%}'
    )

    pie_chart.update_layout(
        title_x=0.5
    )
    filename = Path(output_folder) / "Estoc segons tipologia de vehicle.html"
    pie_chart.write_html(filename)
    if show:
        pie_chart.show()
    return pie_chart
