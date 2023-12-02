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
from queries.prs_query import prs_query as prq ## BNE : Using same query as pr_over_time.py
import io
from cache_manager.cache_manager import CacheManager as cm
from pages.utils.job_utils import nodata_graph
import time

"""
NOTE: VARIABLES TO CHANGE:

(1) PAGE
(2) VIZ_ID
(3) gc_VISUALIZATION
(4) TITLE OF VISUALIZATION
(5) CONTEXT OF GRAPH
(6) IDs of Dash components
(6) NAME_OF_VISUALIZATION_graph
(7) COLUMN_WITH_DATETIME
(8) COLUMN_WITH_DATETIME
(9) COLUMN_TO_SORT_BY
(10) Comments before callbacks
(11) QUERY_USED, QUERY_NAME, QUERY_INITIALS

NOTE: IMPORTING A VISUALIZATION INTO A PAGE
(1) Include the visualization file in the visualization folder for the respective page
(2) Import the visualization into the page_name.py file using "from .visualizations.visualization_file_name import gc_visualization_name"
(3) Add the card into a column in a row on the page

NOTE: ADDITIONAL DASH COMPONENTS FOR USER GRAPH CUSTOMIZATIONS

If you add Dash components (ie dbc.Input, dbc.RadioItems, dcc.DatePickerRange...) the ids, html_for, and targets should be in the
following format: f"component-identifier-{PAGE}-{VIZ_ID}"

NOTE: If you change or add a new query, you need to do "docker system prune -af" before building again

For more information, check out the new_vis_guidance.md
"""


# TODO: Remove unused imports and edit strings and variables in all CAPS
# TODO: Remove comments specific for the template

PAGE = "health"  # EDIT FOR CURRENT PAGE
VIZ_ID = "change_request_closure_ratio"  # UNIQUE IDENTIFIER FOR VIZUALIZATION

gc_change_request_closure_ratio = dbc.Card(
    [
        dbc.CardBody(
            [
                html.H3(
                    "Change Request Closure Ratio",
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
                        "line graph",
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


# callback for change request closure ratio graph
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
def change_request_closure_ratio_graph(repolist, interval): # 
    # wait for data to asynchronously download and become available.
    cache = cm()
    df = cache.grabm(func=prq, repos=repolist)
    while df is None:
        time.sleep(1.0)
        df = cache.grabm(func=prq, repos=repolist)  

    start = time.perf_counter()
    logging.warning(f"{VIZ_ID}- START")

    # test if there is data
    if df.empty:
        logging.warning(f"{VIZ_ID} - NO DATA AVAILABLE")
        return nodata_graph

    # function for all data pre processing, COULD HAVE ADDITIONAL INPUTS AND OUTPUTS
    df_created, df_closed_merged, df_open, df_ratio = process_data(df, interval)


    fig = create_figure(df_created, df_closed_merged, df_open, df_ratio, interval) # BNE : MAY CHANGE

    logging.warning(f"{VIZ_ID} - END - {time.perf_counter() - start}")
    return fig


def process_data(df: pd.DataFrame, interval):
    """Implement your custom data-processing logic in this function.
    The output of this function is the data you intend to create a visualization with,
    requiring no further processing."""
    
    # convert to datetime objects rather than strings
    # ADD ANY OTHER COLUMNS WITH DATETIME
    df["created"] = pd.to_datetime(df["created"], utc=True)
    df["merged"] = pd.to_datetime(df["merged"], utc=True)
    df["closed"] = pd.to_datetime(df["closed"], utc=True)

    # order values chronologically by COLUMN_TO_SORT_BY date
    df = df.sort_values(by="created", axis=0, ascending=True)

    """LOOK AT OTHER VISUALIZATIONS TO SEE IF ANY HAVE A SIMILAR DATA PROCESS"""
    """BNE : BASED OFF PR_OVER_TIME.PY"""

    # variable to slice on to handle weekly period edge case
    period_slice = None
    if interval == "W":
        # this is to slice the extra period information that comes with the weekly case
        period_slice = 10
    
    # --data frames for PR created, merged, or closed. Detailed description applies for all 3.--

    # get the count of created prs in the desired interval in pandas period format, sort index to order entries
    created_range = df["created"].dt.to_period(interval).value_counts().sort_index()

    # converts to data frame object and created date column from period values
    df_created = created_range.to_frame().reset_index().rename(columns={"index": "Date"})

    # converts date column to a datetime object, converts to string first to handle period information
    # the period slice is to handle weekly corner case
    df_created["Date"] = pd.to_datetime(df_created["Date"].astype(str).str[:period_slice])

    # df for merged prs in time interval
    merged_range = pd.to_datetime(df["merged"]).dt.to_period(interval).value_counts().sort_index()
    df_merged = merged_range.to_frame().reset_index().rename(columns={"index": "Date"})
    df_merged["Date"] = pd.to_datetime(df_merged["Date"].astype(str).str[:period_slice])

    # df for closed prs in time interval
    closed_range = pd.to_datetime(df["closed"]).dt.to_period(interval).value_counts().sort_index()
    df_closed = closed_range.to_frame().reset_index().rename(columns={"index": "Date"})
    df_closed["Date"] = pd.to_datetime(df_closed["Date"].astype(str).str[:period_slice])

    # A single df created for plotting merged and closed as stacked bar chart
    df_closed_merged = pd.merge(df_merged, df_closed, on="Date", how="outer")

    # formatting for graph generation
    if interval == "M":
        df_created["Date"] = df_created["Date"].dt.strftime("%Y-%m-01")
        df_closed_merged["Date"] = df_closed_merged["Date"].dt.strftime("%Y-%m-01")
    elif interval == "Y":
        df_created["Date"] = df_created["Date"].dt.strftime("%Y-01-01")
        df_closed_merged["Date"] = df_closed_merged["Date"].dt.strftime("%Y-01-01")

    df_closed_merged["closed"] = df_closed_merged["closed"] - df_closed_merged["merged"] # BNE : Closed PRs without Merged

    # ----- Open PR processinging starts here ----

    # first and last elements of the dataframe are the
    # earliest and latest events respectively
    earliest = df["created"].min()
    latest = max(df["created"].max(), df["closed"].max())

    # beginning to the end of time by the specified interval
    dates = pd.date_range(start=earliest, end=latest, freq="D", inclusive="both")

    # df for open prs from time interval
    df_open = dates.to_frame(index=False, name="Date")

    # aplies function to get the amount of open prs for each day
    df_open["Open"] = df_open.apply(lambda row: get_open(df, row.Date), axis=1)

    df_open["Date"] = df_open["Date"].dt.strftime("%Y-%m-%d")
    
    # ----- Ratio processinging starts here ----
    
    df_closed_merged["Date"] = pd.to_datetime(df_closed_merged["Date"].astype(str).str[:period_slice])
    df_open["Date"] = pd.to_datetime(df_open["Date"].astype(str).str[:period_slice])

    # BNE: A single df created for plotting "closed over open" ratio as a line graph
    # formatting ratio for graph generation
    # df_ratio["closed"] = df_ratio["closed"] - df_ratio["merged"]
    df_ratio = pd.merge(df_open, df_closed_merged, on="Date", how="outer")
    
    df_ratio["Ratio"] = df_ratio["closed"].div(df_ratio["Open"])

    return df_created, df_closed_merged, df_open, df_ratio


def create_figure(
    df_created: pd.DataFrame,
    df_closed_merged: pd.DataFrame,
    df_open: pd.DataFrame,
    df_ratio: pd.DataFrame,
    interval,
):
    # time values for graph
    x_r, x_name, hover, period = get_graph_time_values(interval)

    # graph generation
    # fig = fig

    """LOOK AT OTHER VISUALIZATIONS TO SEE IF ANY HAVE A SIMILAR GRAPH"""

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df_ratio["Date"],
            y=df_ratio["Ratio"],
            mode="lines",
            marker=dict(color=color_seq[5]),
            name="Open",
            hovertemplate="PRs Open: %{y}<br>%{x|%b %d, %Y} <extra></extra>",
        )
    )

    return fig

# for each day, this function calculates the amount of open prs
def get_open(df, date):
    # drop rows that are more recent than the date limit
    df_created = df[df["created"] <= date]

    # drops rows that have been closed after date
    df_open = df_created[df_created["closed"] > date]

    # include prs that have not been close yet
    df_open = pd.concat([df_open, df_created[df_created.closed.isnull()]])

    # generates number of columns ie open prs
    num_open = df_open.shape[0]
    return num_open
