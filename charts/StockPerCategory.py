from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from charts.Colors import COLOR_DISCRETE_MAP


def stock_per_category_pie_chart(stock_activity_df: pd.DataFrame, output_file, show: bool = False) -> go.Figure:
    """
    Pie Chart of the stock by Category

    :param stock_activity_df: aggregated table of the stock, with the columns Category and Stock
    :param output_file: path of the html file where to store the resulting chart
    :param show: if True, the figure is also opened in the browser (for local use)
    :return: the figure. It is also saved in an html file with the whole Stock distribution by Category
    """
    data = stock_activity_df.groupby(['Category'], as_index=False).agg(Stock=('Stock', 'sum'))
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
    pie_chart.write_html(Path(output_file))
    if show:
        pie_chart.show()
    return pie_chart
