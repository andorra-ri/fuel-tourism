import logging
from pathlib import Path
from typing import List

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from Classification import HYBRID_PHEV_TYPES
from .Colors import CHART_CONFIG, FALLBACK_SEGMENTATION_COLORS, NO_SEGMENT_LABEL

logger = logging.getLogger('logger' + '.StockPerManufacturingYear')

CHART_TITLE = 'Parc de vehicles actius per any de fabricació i tipologia'


def figures_to_html(figs: List[go.Figure], filename="dashboard.html"):
    """Save all the figures to one html file. The Plotly library is included only once, from the CDN"""
    with open(filename, 'w', encoding='utf-8') as dashboard:
        dashboard.write('<html><head><meta charset="utf-8"></head><body>\n')
        for i, fig in enumerate(figs):
            dashboard.write(fig.to_html(full_html=False, include_plotlyjs='cdn' if i == 0 else False))
        dashboard.write("</body></html>\n")


def categories_grouping(row):
    """Group hybrid and PHEV type without segment associated to avoid too large segmentations when plotting"""
    if row['Fuel'] == 'Battery electric':
        return 'Battery electric'
    if row['Fuel'] in HYBRID_PHEV_TYPES:
        if 'Hybrid' in row['Fuel']:
            return 'Hybrid'
        else:
            return 'PHEV'
    else:
        result = row['Fuel'] + ' ' + row['Segment']
        return result


def update_chart_layout(figure, title: str = None):
    figure.update_layout(
        title=title,
        title_x=0.4,
        legend_title='',
        height=600,
        width=800,
        template='plotly_white',
        xaxis_title='Any de fabricació',
        yaxis_title='Estoc'
    )


def add_annotation_to_chart(figure, data: pd.DataFrame, category: str):
    figure.add_annotation(
        x=data['ANY_FABRICACIO'].min() + (data['ANY_FABRICACIO'].max() - data['ANY_FABRICACIO'].min()) / 2,
        y=data.groupby(['ANY_FABRICACIO'])['Stock'].sum().max() * 1.15,
        xanchor='center', yanchor='top',
        font={'size': 16}, text=category, showarrow=False)


def create_chart_with_segmentation_and_colors_configuration(data: pd.DataFrame, category: str) -> go.Figure:
    """
    Stacked bar chart of the stock per year of manufacturing. The order and the colors of the segmentation labels are
    taken from CHART_CONFIG. Labels that are not in the configuration are added at the end with a fallback color.
    """
    configuration = CHART_CONFIG.get(category, [])
    category_order = [label for label, _ in configuration]
    colors = dict(configuration)

    unconfigured_labels = [label for label in data['segmentation'].unique() if label not in colors]
    for i, label in enumerate(unconfigured_labels):
        logger.warning(f'Segmentation "{label}" of {category} is not in CHART_CONFIG, a fallback color is used')
        category_order.append(label)
        colors[label] = FALLBACK_SEGMENTATION_COLORS[i % len(FALLBACK_SEGMENTATION_COLORS)]

    fig = px.bar(data,
                 x='ANY_FABRICACIO', y='Stock', color="segmentation",
                 category_orders={"segmentation": category_order},
                 color_discrete_map=colors
                 )
    return fig


def stock_per_manufacturing_year_and_category_bar_charts(stock_by_manufacturing_year_df: pd.DataFrame, output_file,
                                                         show: bool = False) -> List[go.Figure]:
    """
    Save to and html file a bar chart representing the stock distribution per year of manufacturing, per segment and
    per fuel type. One chart for each vehicle category in CHART_CONFIG
    :param stock_by_manufacturing_year_df: aggregated table of the stock per year of manufacturing, with the columns
        Category, Fuel, Segment, ANY_FABRICACIO and Stock
    :param output_file: path of the html file where to store the resulting charts
    :param show: if True, the figures are also opened in the browser (for local use)
    :return: the list of figures, one for each vehicle Category. They are also saved in an html file
    """
    figs = []
    for category in CHART_CONFIG:
        category_df = stock_by_manufacturing_year_df[stock_by_manufacturing_year_df.Category == category]
        if category_df.empty:
            logger.warning(f'No vehicles of Category {category}, its chart is not created')
            continue

        data = category_df.groupby(['Fuel', 'Segment', 'ANY_FABRICACIO'], dropna=False).agg(
            Stock=('Stock', 'sum')).reset_index()
        data['Segment'] = data['Segment'].fillna(NO_SEGMENT_LABEL)
        data['segmentation'] = data.apply(lambda row: categories_grouping(row), axis=1)

        fig = create_chart_with_segmentation_and_colors_configuration(data, category)
        update_chart_layout(fig, CHART_TITLE if not figs else None)
        add_annotation_to_chart(fig, data, category)
        figs.append(fig)

    # Save figures to html file
    figures_to_html(figs, Path(output_file))

    if show:
        for fig in figs:
            fig.show()
    return figs
