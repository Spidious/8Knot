from dash import html, dcc
import dash
import dash_bootstrap_components as dbc
from app import augur


navbar = dbc.Navbar(
    dbc.Container(
        [
            dbc.Row(
                [
                    dbc.Col(
                        [
                            html.Img(src=dash.get_asset_url("logo2.png"), height="40px"),
                            dbc.NavbarBrand(
                                "8Knot Community Data",
                                id="navbar-title",
                                className="ms-2",
                            ),
                        ],
                        width={"size": "auto"},
                    ),
                    dbc.Col(
                        [
                            dbc.Nav(
                                [
                                    dbc.NavLink(page["name"], href=page["path"], active="exact")
                                    for page in dash.page_registry.values()
                                    if page["module"] != "pages.not_found_404"
                                ],
                                navbar=True,
                            )
                        ],
                        width={"size": "auto"},
                    ),
                ],
                align="center",
                className="g-0",
                justify="start",
            ),
            dbc.Row(
                [
                    dbc.Col(
                        id="nav-login-container",
                        children=[],
                    )
                ],
                align="center",
            ),
        ],
        fluid=True,
    ),
    color="primary",
    dark=True,
    sticky="top",
)

navbar_bottom = dbc.NavbarSimple(
    children=[
        dbc.NavItem(
            dbc.NavLink(
                "Visualization request",
                href="https://github.com/sandiego-rh/explorer/issues/new?assignees=&labels=enhancement%2Cvisualization&template=visualizations.md",
                external_link="True",
                target="_blank",
            )
        ),
        dbc.NavItem(
            dbc.NavLink(
                "Bug",
                href="https://github.com/sandiego-rh/explorer/issues/new?assignees=&labels=bug&template=bug_report.md",
                external_link="True",
                target="_blank",
            )
        ),
        dbc.NavItem(
            dbc.NavLink(
                "Repo/Org Request",
                href="https://github.com/sandiego-rh/explorer/issues/new?assignees=&labels=augur&template=augur_load.md",
                external_link="True",
                target="_blank",
            )
        ),
    ],
    brand="",
    brand_href="#",
    color="primary",
    dark=True,
    fluid=True,
)

search_bar = html.Div(
    [
        html.Div(
            [
                dcc.Dropdown(
                    id="projects",
                    multi=True,
                    options=[augur.get_search_input()],
                    value=[augur.get_search_input()],
                    style={"font-size": 16},
                ),
                dbc.Alert(
                    children='Please ensure that your spelling is correct. \
                        If your selection definitely isn\'t present, please request that \
                        it be loaded using the help button "REPO/ORG Request" \
                        in the bottom right corner of the screen.',
                    id="help-alert",
                    dismissable=True,
                    fade=True,
                    is_open=False,
                    color="info",
                ),
            ],
            style={
                "width": "50%",
                "display": "table-cell",
                "verticalAlign": "middle",
                "padding-right": "10px",
            },
        ),
        dbc.Button(
            "Search",
            id="search",
            n_clicks=0,
            size="md",
        ),
        dbc.Button(
            "Help",
            id="search-help",
            n_clicks=0,
            size="md",
            style={
                "verticalAlign": "top",
                "display": "table-cell",
            },
        ),
    ],
    style={
        "align": "right",
        "display": "table",
        "width": "60%",
    },
)

layout = dbc.Container(
    [
        # componets to store data from queries
        dcc.Store(id="repo-choices", storage_type="session", data=[]),
        # components to store job-ids for the worker queue
        dcc.Store(id="job-ids", storage_type="session", data=[]),
        dcc.Store(id="users_augur_groups", storage_type="memory", data=[]),
        dcc.Store(id="user_bearer_token", storage_type="session", data=""),
        dcc.Store(id="augur_username", storage_type="session", data=""),
        dcc.Location(id="url"),
        navbar,
        dbc.Row(
            [
                dbc.Col(
                    [
                        dbc.Label(
                            "Select Github repos or orgs:",
                            html_for="projects",
                            width="auto",
                            size="lg",
                        ),
                        search_bar,
                        dcc.Loading(
                            children=[html.Div(id="results-output-container", className="mb-4")],
                            color="#119DFF",
                            type="dot",
                            fullscreen=True,
                        ),
                        dcc.Loading(
                            dbc.Badge(
                                children="Data Loaded",
                                id="data_badge",
                                color="#436755",
                                className="me-1",
                            ),
                            type="cube",
                            color="#436755",
                        ),
                        # where our page will be rendered
                        dash.page_container,
                    ],
                ),
            ],
            justify="start",
        ),
        navbar_bottom,
    ],
    fluid=True,
    className="dbc",
)
