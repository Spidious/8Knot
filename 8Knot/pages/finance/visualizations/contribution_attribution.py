from dash import html, dcc, callback
import dash
import dash_bootstrap_components as dbc
from dash.dependencies import Input, Output, State
import plotly.graph_objects as go
import pandas as pd
import logging
from dateutil.relativedelta import *  # type: ignore
import plotly.express as px
from pages.utils.graph_utils import get_graph_time_values, color_seq
from queries.cont_attrib import cont_attrib_query as caq
import io
from cache_manager.cache_manager import CacheManager as cm
from pages.utils.job_utils import nodata_graph
import time
import datetime as dt

PAGE = "funding"
VIZ_ID = "contr_attr"

gc_contr_attr = dbc.Card(
    [
        dbc.CardBody(
            [
                html.H3(
                    "Contribution Attribution",
                    className="card-title",
                    style={"textAlign": "center"},
                ),
                dbc.Popover(
                    [
                        dbc.PopoverHeader("Graph Info:"),
                        dbc.PopoverBody(
                            """
                            Visualizes number of pull request reviews assigned to each each contributor\n
                            in the specifed time bucket. The visualization only includes contributors\n
                            that meet the user inputed the assignment criteria.
                            """
                        ),
                    ],
                    id=f"popover-{PAGE}-{VIZ_ID}",
                    target=f"popover-target-{PAGE}-{VIZ_ID}",
                    placement="top",
                    is_open=False,
                ),
                dcc.Loading(
                    dcc.Graph(id=f"{PAGE}-{VIZ_ID}"),
                ),
                dbc.Form(
                    [
                        dbc.Row(
                            [
                                dbc.Label(
                                    "Total Assignments Required:",
                                    html_for=f"assignments-required-{PAGE}-{VIZ_ID}",
                                    width={"size": "auto"},
                                ),
                                dbc.Col(
                                    dbc.Input(
                                        id=f"assignments-required-{PAGE}-{VIZ_ID}",
                                        type="number",
                                        min=1,
                                        max=250,
                                        step=1,
                                        value=10,
                                        size="sm",
                                    ),
                                    className="me-2",
                                    width=1,
                                ),
                                dbc.Alert(
                                    children="No contributors meet assignment requirement",
                                    id=f"check-alert-{PAGE}-{VIZ_ID}",
                                    dismissable=True,
                                    fade=False,
                                    is_open=False,
                                    color="warning",
                                ),
                            ],
                            align="center",
                        ),
                        dbc.Row(
                            [
                                dbc.Label(
                                    "Date Interval:",
                                    html_for=f"date-radio-{PAGE}-{VIZ_ID}",
                                    width="auto",
                                ),
                                dbc.Col(
                                    [
                                        dbc.RadioItems(
                                            id=f"date-radio-{PAGE}-{VIZ_ID}",
                                            options=[
                                                {"label": "Trend", "value": "D"},
                                                {"label": "Week", "value": "W"},
                                                {"label": "Month", "value": "M"},
                                                {"label": "Year", "value": "Y"},
                                            ],
                                            value="W",
                                            inline=True,
                                        ),
                                    ]
                                ),
                                dbc.Col(
                                    dbc.Button(
                                        "About Graph",
                                        id=f"popover-target-{PAGE}-{VIZ_ID}",
                                        color="secondary",
                                        size="sm",
                                    ),
                                    width="auto",
                                    style={"paddingTop": ".5em"},
                                ),
                            ],
                            align="center",
                        ),
                    ]
                ),
            ]
        )
    ],
)


# callback for graph info popover
@callback(
    Output(f"popover-{PAGE}-{VIZ_ID}", "is_open"),
    [Input(f"popover-target-{PAGE}-{VIZ_ID}", "n_clicks")],
    [State(f"popover-{PAGE}-{VIZ_ID}", "is_open")],
)
def toggle_popover(n, is_open):
    if n:
        return not is_open
    return is_open


# callback for pull request review assignment graph
@callback(
    Output(f"{PAGE}-{VIZ_ID}", "figure"),
    Output(f"check-alert-{PAGE}-{VIZ_ID}", "is_open"),
    [
        Input("repo-choices", "data"),
        Input(f"date-radio-{PAGE}-{VIZ_ID}", "value"),
        Input(f"assignments-required-{PAGE}-{VIZ_ID}", "value"),
    ],
    background=True,
)
def cntrib_pr_assignment_graph(repolist, interval, assign_req):
    # wait for data to asynchronously download and become available.
    cache = cm()
    df = cache.grabm(func=caq, repos=repolist)
    while df is None:
        time.sleep(1.0)
        df = cache.grabm(func=caq, repos=repolist)

    start = time.perf_counter()
    logging.warning(f"{VIZ_ID}- START")

    # test if there is data
    if df.empty:
        logging.warning(f"{VIZ_ID} - NO DATA AVAILABLE")
        return nodata_graph, False

    df = process_data(df, interval, assign_req)

    fig = create_figure(df)

    logging.warning(f"{VIZ_ID} - END - {time.perf_counter() - start}")
    return fig, False


def process_data(df: pd.DataFrame, interval, assign_req):

    # convert to datetime objects rather than strings
    # df["created"] = pd.to_datetime(df["created"], utc=True)

    return df


def create_figure(df: pd.DataFrame):
    # time values for graph
    # x_r, x_name, hover, period = get_graph_time_values(interval)
# '''
#     # list of contributors for plot
#     contribs = df.columns.tolist()[2:]

#     # making a line graph if the bin-size is small enough.
#     if interval == "D":

#         # list of lines for plot
#         lines = []

#         # iterate through colors for lines
#         marker_val = 0

#         # loop to create lines for each contributors
#         for contrib in contribs:
#             line = go.Scatter(
#                 name=contrib,
#                 x=df["start_date"],
#                 y=df[contrib],
#                 mode="lines",
#                 showlegend=True,
#                 hovertemplate="PRs Assigned: %{y}<br>%{x|%b %d, %Y}",
#                 marker=dict(color=color_seq[marker_val]),
#             )
#             lines.append(line)
#             marker_val = (marker_val + 1) % 6
#         fig = go.Figure(lines)
#     else:
#         fig = px.bar(
#             df,
#             x="start_date",
#             y=contribs,
#             color_discrete_sequence=color_seq,
#         )

#         # edit hover values
#         fig.update_traces(hovertemplate=hover + "<br>Prs Assigned: %{y}<br>")

#         fig.update_xaxes(
#             showgrid=True,
#             ticklabelmode="period",
#             dtick=period,
#             rangeslider_yaxis_rangemode="match",
#             range=x_r,
#         )

#     # layout specifics for both styles of plots
#     fig.update_layout(
#         xaxis_title="Time",
#         yaxis_title="PR Review Assignments",
#         legend_title="Contributor ID",
#         font=dict(size=14),
#     )'''

    fig = px.pie(df, values="count",
                names="employment")
    fig.update_traces(
                textposition="inside",  
                textinfo="percent+label",
                hovertemplate="%{label} <br>Commits: %{value}<br><extra></extra>",
    )

    return fig