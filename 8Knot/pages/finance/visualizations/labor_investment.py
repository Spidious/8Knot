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

## BNE : Using 3 Queries
from queries.prs_query import prs_query as prq 
from queries.commits_query import commits_query as cq
from queries.issues_query import issues_query as iq

import io
from cache_manager.cache_manager import CacheManager as cm
from pages.utils.job_utils import nodata_graph
import time

PAGE = "finance"  # EDIT FOR CURRENT PAGE
VIZ_ID = "labor_investment"  # UNIQUE IDENTIFIER FOR VIZUALIZATION

gc_labor_investment = dbc.Card(
    [
        dbc.CardBody(
            [
                html.H3(
                    "Labor Investment",
                    className="card-title",
                    style={"textAlign": "center"},
                ),
                dbc.Popover(
                    [
                        dbc.PopoverHeader("Graph Info:"),
                        dbc.PopoverBody("Context of graph"),
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
                                    "Date Interval:",
                                    html_for=f"date-radio-{PAGE}-{VIZ_ID}",
                                    width="auto",
                                ),
                                dbc.Col(
                                    [
                                        dbc.RadioItems(
                                            id=f"date-radio-{PAGE}-{VIZ_ID}",
                                            options=[
                                                {
                                                    "label": "Trend",
                                                    "value": "D",
                                                },  # TREND IF LINE, DAY IF NOT
                                                # {"label": "Week","value": "W",}, UNCOMMENT IF APPLICABLE
                                                {"label": "Month", "value": "M"},
                                                {"label": "Year", "value": "Y"},
                                            ],
                                            value="M",
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


# callback for VIZ TITLE graph
@callback(
    Output(f"{PAGE}-{VIZ_ID}", "figure"),
    # Output(f"check-alert-{PAGE}-{VIZ_ID}", "is_open"), USE WITH ADDITIONAL PARAMETERS
    # if additional output is added, change returns accordingly
    [
        Input("repo-choices", "data"),
        Input(f"date-radio-{PAGE}-{VIZ_ID}", "value"),
        # add additional inputs here
    ],
    background=True,
)

## Data Preprocessing?
def labor_investment_graph(repolist, interval):
    # wait for data to asynchronously download and become available.
    cache = cm()
    df = cache.grabm(func=prq, repos=repolist) # from queries.prs_query import prs_query as prq 
    df2 = cache.grabm(func=cq, repos=repolist) # from queries.commits_query import commits_query as cq
    df3 = cache.grabm(func=iq, repos=repolist) # from queries.issues_query import issues_query as iq
    while df is None:
        time.sleep(1.0)
        df = cache.grabm(func=prq, repos=repolist)
    while df2 is None:
        time.sleep(1.0)
        df2 = cache.grabm(func=cq, repos=repolist)
    while df3 is None:
        time.sleep(1.0)
        df3 = cache.grabm(func=iq, repos=repolist)

    start = time.perf_counter()
    logging.warning(f"{VIZ_ID}- START")

    # test if there is data
    if (df.empty):
        logging.warning(f"{VIZ_ID} - NO DATA AVAILABLE for df")
        return nodata_graph
    if (df2.empty):
        logging.warning(f"{VIZ_ID} - NO DATA AVAILABLE for df2")
        return nodata_graph
    if (df3.empty):
        logging.warning(f"{VIZ_ID} - NO DATA AVAILABLE for df3")
        return nodata_graph

    # function for all data pre processing, COULD HAVE ADDITIONAL INPUTS AND OUTPUTS
    # BNE: 
    # df  -> df_requested (Pull Request creation date)
    # df2 -> df_comitted (Commit Authorship Date)
    # df3 -> df_issued (Issue Creation date)
    df_requested, df_comitted, df_issued = process_data(df, df2, df3, interval)

    fig = create_figure(df_requested, df_comitted, df_issued, interval)

    logging.warning(f"{VIZ_ID} - END - {time.perf_counter() - start}")
    return fig

def process_data(
    df: pd.DataFrame,
    df2: pd.DataFrame,
    df3: pd.DataFrame,
    interval,
):
    """Implement your custom data-processing logic in this function.
    The output of this function is the data you intend to create a visualization with,
    requiring no further processing."""

    # convert to datetime objects rather than strings
    # ADD ANY OTHER COLUMNS WITH DATETIME
    df["created"] = pd.to_datetime(df["created"], utc=True)
    df2["date"] = pd.to_datetime(df2["date"], utc=True)
    df3["created"] = pd.to_datetime(df3["created"], utc=True)

    # order values chronologically by COLUMN_TO_SORT_BY date
    df = df.sort_values(by="created", axis=0, ascending=True)
    df2 = df2.sort_values(by="date", axis=0, ascending=True)
    df3 = df3.sort_values(by="created", axis=0, ascending=True)

    """LOOK AT OTHER VISUALIZATIONS TO SEE IF ANY HAVE A SIMILAR DATA PROCESS"""

    # variable to slice on to handle weekly period edge case
    period_slice = None
    if interval == "W":
        # this is to slice the extra period information that comes with the weekly case
        period_slice = 10

    # get the count of authorship dates in the desired interval in pandas period format, sort index to order entries
    requested_range = df["created"].dt.to_period(interval).value_counts().sort_index()
    comitted_range = df2["date"].dt.to_period(interval).value_counts().sort_index()
    issued_range = df3["created"].dt.to_period(interval).value_counts().sort_index()

    # converts to data frame object and created date column from period values
    df_requested = requested_range.to_frame().reset_index().rename(columns={"index": "Date"})
    df_comitted = comitted_range.to_frame().reset_index().rename(columns={"index": "Date"})
    df_issued = issued_range.to_frame().reset_index().rename(columns={"index": "Date"})

    # converts date column to a datetime object, converts to string first to handle period information
    # the period slice is to handle weekly corner case
    df_requested["Date"] = pd.to_datetime(df_requested["Date"].astype(str).str[:period_slice])
    df_comitted["Date"] = pd.to_datetime(df_comitted["Date"].astype(str).str[:period_slice])
    df_issued["Date"] = pd.to_datetime(df_issued["Date"].astype(str).str[:period_slice])

    # formatting for graph generation
    if interval == "M":
        df_requested["Date"] = df_requested["Date"].dt.strftime("%Y-%m-01")
        df_comitted["Date"] = df_comitted["Date"].dt.strftime("%Y-%m-01")
        df_issued["Date"] = df_issued["Date"].dt.strftime("%Y-%m-01")
    elif interval == "Y":
        df_requested["Date"] = df_requested["Date"].dt.strftime("%Y-01-01")
        df_comitted["Date"] = df_comitted["Date"].dt.strftime("%Y-01-01")
        df_issued["Date"] = df_issued["Date"].dt.strftime("%Y-01-01")
    return df_requested, df_comitted, df_issued


def create_figure(
    df_requested: pd.DataFrame,
    df_comitted: pd.DataFrame,
    df_issued: pd.DataFrame,
    interval,
):
    # time values for graph
    x_r, x_name, hover, period = get_graph_time_values(interval)

    # graph generation
    fig = go.Figure(data=[
        go.Bar  (
                    name = 'Requested',
                    x = df_requested["Date"],
                    y = df_requested["created"],
                    marker_color = 'Green'
                ),
        
        go.Bar  (
                    name = 'Comitted',
                    x = df_comitted["Date"],
                    y = df_comitted["date"]
                ),
        
        go.Bar  (
                    name = 'Issued',
                    x = df_issued["Date"],
                    y = df_issued["created"],
                    marker_color = 'Crimson'
                )
    ])

    fig.update_layout(
        xaxis_title = "Date",
        yaxis_title = "Authorships",
        legend_title = "Contributions",
        font=dict   (
                        size=18,
                    )
    )
    return fig