# homepage.py
import calendar
from datetime import datetime, timedelta, date
import dash_bootstrap_components as dbc
from dash import html, dcc, Input, Output, State, callback_context, no_update
from dash.exceptions import PreventUpdate
import plotly.graph_objects as go
from collections import defaultdict
from functools import wraps

# Security
from flask_login import current_user, login_required
# def authenticate_callback(func):
#     """Decorator to authenticate Dash callbacks"""
#     @wraps(func)
#     def wrapper(*args, **kwargs):
#         if not current_user.is_authenticated:
#             raise PreventUpdate
#         return func(*args, **kwargs)
#     return wrapper

# --- FRONTEND ---
def homepage_layout():
    
    # Only load data if authenticated
    if not current_user.is_authenticated:
        return dbc.Container(
            dbc.Alert("Please login to access this page", color="danger"),
            className="mt-5"
        )

    # --- APP LAYOUT ---
    return dbc.Container(
        [
            html.Div(
                id="filter-container",
                children=[
                    dbc.Button(
                        [html.I(className="fas fa-filter me-2"), "Filters"],
                        id="filter-toggle",
                        color="dark",
                        n_clicks=0,
                        className="mb-2",
                        size="sm",
                    ),
                    dbc.Collapse(
                        dbc.Card(
                            dbc.CardBody(
                                [
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                [
                                                    html.Label(
                                                        "Filter Type",
                                                        className="fw-bold small text-muted mb-2",
                                                    ),
                                                    dbc.RadioItems(
                                                        id="filter-type",
                                                        options=[
                                                            {
                                                                "label": "By Month",
                                                                "value": "month",
                                                            },
                                                            {
                                                                "label": "Last #days",
                                                                "value": "last",
                                                            },
                                                            {
                                                                "label": "Date range",
                                                                "value": "daterange",
                                                            },
                                                        ],
                                                        value="month",
                                                        className="dash-radio-group",
                                                    ),
                                                ],
                                                xs=12,
                                                sm=12,
                                                md=6,  # Full width on mobile, half on desktop
                                            ),
                                        ],
                                        className="mb-3",
                                    ),
                                    html.Hr(className="my-3"),
                                    html.Div(
                                        id="month-filter-options",
                                        children=[
                                            dbc.InputGroup(
                                                [
                                                    dbc.Button(
                                                        html.I(
                                                            className="fas fa-chevron-left"
                                                        ),
                                                        id="year-decrement",
                                                        n_clicks=0,
                                                        color="light",
                                                        outline=True,
                                                    ),
                                                    dbc.Input(
                                                        id="year-input",
                                                        type="number",
                                                        value=datetime.now().year,
                                                        min=2000,
                                                        className="text-center fw-bold",
                                                    ),
                                                    dbc.Button(
                                                        html.I(
                                                            className="fas fa-chevron-right"
                                                        ),
                                                        id="year-increment",
                                                        n_clicks=0,
                                                        color="light",
                                                        outline=True,
                                                    ),
                                                ],
                                                className="mb-3",
                                                size="sm",
                                            ),
                                            dcc.Slider(
                                                id="month-slider",
                                                min=1,
                                                max=12,
                                                step=1,
                                                value=datetime.now().month,
                                                marks={
                                                    i: calendar.month_abbr[i]
                                                    for i in range(1, 13)
                                                },
                                                className="px-2",
                                            ),
                                        ],
                                    ),
                                    html.Div(
                                        id="last-filter-options",
                                        children=[
                                            dcc.RadioItems(
                                                id="last-period-options",
                                                options=[
                                                    {"label": "Last 1 Day", "value": 1},
                                                    {
                                                        "label": "Last 1 Week",
                                                        "value": 7,
                                                    },
                                                    {
                                                        "label": "Last 2 Weeks",
                                                        "value": 14,
                                                    },
                                                    {
                                                        "label": "Last 1 Month",
                                                        "value": 30,
                                                    },
                                                    {
                                                        "label": "Custom",
                                                        "value": "custom",
                                                    },
                                                ],
                                                value=30,
                                                inline=True,
                                                className="dash-radio-group mb-3",
                                            ),
                                            html.Div(
                                                id="custom-days-container",
                                                children=[
                                                    dbc.Input(
                                                        id="custom-days-input",
                                                        type="number",
                                                        value=30,
                                                        min=1,
                                                        placeholder="Enter days",
                                                        size="sm",
                                                    )
                                                ],
                                                style={"display": "none"},
                                            ),
                                        ],
                                        style={"display": "none"},
                                    ),
                                    html.Div(
                                        id="daterange-filter-options",
                                        children=[
                                            dbc.Row(
                                                [
                                                    dbc.Col(
                                                        [
                                                            html.Label(
                                                                "Start Date:",
                                                                className="small fw-bold",
                                                            ),
                                                            dcc.DatePickerSingle(
                                                                id="start-date-picker",
                                                                min_date_allowed=date(
                                                                    2000, 1, 1
                                                                ),
                                                                max_date_allowed=date.today(),
                                                                initial_visible_month=date.today(),
                                                                date=date.today()
                                                                - timedelta(days=30),
                                                                display_format="MMM Do, YY",
                                                                className="d-block",
                                                                style={
                                                                    "width": "100%"
                                                                },  # Full width
                                                            ),
                                                        ],
                                                        xs=12,
                                                        sm=6,  # Stack on mobile
                                                    ),
                                                    dbc.Col(
                                                        [
                                                            html.Label(
                                                                "End Date:",
                                                                className="small fw-bold",
                                                            ),
                                                            dcc.DatePickerSingle(
                                                                id="end-date-picker",
                                                                min_date_allowed=date(
                                                                    2000, 1, 1
                                                                ),
                                                                max_date_allowed=date.today(),
                                                                initial_visible_month=date.today(),
                                                                date=date.today(),
                                                                display_format="MMM Do, YY",
                                                                className="d-block",
                                                                style={
                                                                    "width": "100%"
                                                                },  # Full width
                                                            ),
                                                        ],
                                                        xs=12,
                                                        sm=6,  # Stack on mobile
                                                    ),
                                                ]
                                            )
                                        ],
                                        style={"display": "none"},
                                    ),
                                ]
                            ),
                            className="border-0 shadow-sm",
                        ),
                        id="filter-collapse",
                        is_open=False,
                    ),
                ],
            ),
            # -- NET WORTH VIEWER --
            dbc.Row(
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(
                            [
                                html.H4("Net Worth Summary", className="section-header"),
                                dbc.Row(
                                    [
                                        # Left column - original cards
                                        dbc.Col(
                                            dbc.Row(
                                                [
                                                    # Assets and Liabilities row
                                                    dbc.Row(
                                                        [
                                                            dbc.Col(
                                                                dbc.Card(
                                                                    dbc.CardBody(
                                                                        [
                                                                            html.H5(
                                                                                "Total Assets",
                                                                                className="card-title",
                                                                            ),
                                                                            html.H3(
                                                                                id="total-assets-display-homepage",
                                                                                children="$0.00",
                                                                                className="text-success",
                                                                            ),
                                                                        ]
                                                                    ),
                                                                    className="text-center metric-card h-100",
                                                                ),
                                                                xs=12,
                                                                sm=6,  # Full width on mobile, half on desktop
                                                                className="mb-3",
                                                            ),
                                                            dbc.Col(
                                                                dbc.Card(
                                                                    dbc.CardBody(
                                                                        [
                                                                            html.H5(
                                                                                "Total Liabilities",
                                                                                className="card-title",
                                                                            ),
                                                                            html.H3(
                                                                                id="total-liabilities-display-homepage",
                                                                                children="$0.00",
                                                                                className="text-danger",
                                                                            ),
                                                                        ]
                                                                    ),
                                                                    className="text-center metric-card h-100",
                                                                ),
                                                                xs=12,
                                                                sm=6,  # Full width on mobile, half on desktop
                                                                className="mb-3",
                                                            ),
                                                        ]
                                                    ),
                                                    # Net Worth row
                                                    dbc.Row(
                                                        dbc.Col(
                                                            dbc.Card(
                                                                dbc.CardBody(
                                                                    [
                                                                        html.H5(
                                                                            "Net Worth",
                                                                            className="card-title",
                                                                        ),
                                                                        html.H3(
                                                                            id="net-worth-display-homepage",
                                                                            children="$0.00",
                                                                            className="text-primary fw-bold",
                                                                        ),
                                                                    ]
                                                                ),
                                                                className="text-center metric-card h-100",
                                                            ),
                                                            width=12,
                                                        )
                                                    ),
                                                ]
                                            ),
                                            xs=12,
                                            lg=10,  # Full width on mobile/tablet, 10 on large screens
                                        ),
                                        # Right column - spending/income cards
                                        dbc.Col(
                                            [
                                                dbc.Card(
                                                    dbc.CardBody(
                                                        [
                                                            html.H5(
                                                                "Spending",
                                                                className="card-title",
                                                            ),
                                                            html.H3(
                                                                id="spending-display-nw",
                                                                children="$0.00",
                                                                className="text-danger",
                                                            ),
                                                            html.Div(
                                                                [
                                                                    html.Span(
                                                                        id="spending-percent-nw",
                                                                        children="0.0%",
                                                                        className="metric-change me-1",
                                                                    ),
                                                                    html.I(
                                                                        className="fas fa-arrow-down"
                                                                    ),
                                                                ],
                                                                className="d-flex align-items-center justify-content-center text-danger",
                                                            ),
                                                        ]
                                                    ),
                                                    className="text-center compact-metric-card mb-3",
                                                ),
                                                dbc.Card(
                                                    dbc.CardBody(
                                                        [
                                                            html.H5(
                                                                "Income",
                                                                className="card-title",
                                                            ),
                                                            html.H3(
                                                                id="income-display-nw",
                                                                children="$0.00",
                                                                className="text-success",
                                                            ),
                                                            html.Div(
                                                                [
                                                                    html.Span(
                                                                        id="income-percent-nw",
                                                                        children="0.0%",
                                                                        className="metric-change me-1",
                                                                    ),
                                                                    html.I(
                                                                        className="fas fa-arrow-up"
                                                                    ),
                                                                ],
                                                                className="d-flex align-items-center justify-content-center text-success",
                                                            ),
                                                        ]
                                                    ),
                                                    className="text-center compact-metric-card",
                                                ),
                                            ],
                                            xs=12,
                                            lg=2,  # Full width on mobile/tablet, 2 on large screens
                                            className="mt-3 mt-lg-0",  # Add margin on mobile, remove on large
                                        ),
                                    ]
                                ),
                                # Collapsible details panel
                                dbc.Accordion(
                                    [
                                        dbc.AccordionItem(
                                            [
                                                # -- MOVEMENT VIEWER --
                                                dbc.Card(
                                                    dbc.CardBody(
                                                        [
                                                            dbc.Row(
                                                                [
                                                                    dbc.Col(
                                                                        html.Label(
                                                                            "Start Date:",
                                                                            id="start-date-label-movement",
                                                                            className="small fw-bold",
                                                                        ),
                                                                        width="auto",
                                                                        className="mb-2 mb-sm-0",
                                                                    ),
                                                                    dbc.Col(
                                                                        dcc.DatePickerSingle(
                                                                            id="start-date-picker-movement",
                                                                            min_date_allowed=date(
                                                                                2000,
                                                                                1,
                                                                                1,
                                                                            ),
                                                                            max_date_allowed=date.today(),
                                                                            initial_visible_month=date.today(),
                                                                            date=date.today()
                                                                            - timedelta(
                                                                                days=30
                                                                            ),
                                                                            display_format="MMM Do, YY",
                                                                        ),
                                                                        width="auto",
                                                                        className="mb-2 mb-sm-0",
                                                                    ),
                                                                    dbc.Col(
                                                                        html.Label(
                                                                            "End Date:",
                                                                            className="small fw-bold",
                                                                        ),
                                                                        width="auto",
                                                                        className="mb-2 mb-sm-0",
                                                                    ),
                                                                    dbc.Col(
                                                                        dcc.DatePickerSingle(
                                                                            id="end-date-picker-movement",
                                                                            min_date_allowed=date(
                                                                                2000,
                                                                                1,
                                                                                1,
                                                                            ),
                                                                            initial_visible_month=date.today(),
                                                                            date=date.today(),
                                                                            display_format="MMM Do, YY",
                                                                        ),
                                                                        width="auto",
                                                                        className="mb-2 mb-sm-0",
                                                                    ),
                                                                    dbc.Col(
                                                                        dbc.Checklist(
                                                                            id="show-net-worth-movement",
                                                                            options=[
                                                                                {
                                                                                    "label": "Net worth (last snapshot)",
                                                                                    "value": "enable",
                                                                                }
                                                                            ],
                                                                            value=[
                                                                                "enable"
                                                                            ],
                                                                            switch=True,
                                                                            className="dash-checklist-group",
                                                                        ),
                                                                        xs=12,
                                                                        sm="auto",
                                                                        className="ms-sm-auto mt-2 mt-sm-0",
                                                                    ),
                                                                ],
                                                                justify="start",
                                                                align="center",
                                                                className="mb-3 flex-wrap",  # Allow wrapping
                                                            ),
                                                            dcc.Graph(
                                                                id="trend-movement-graph",
                                                                figure=go.Figure(),
                                                                config={
                                                                    "displaylogo": False,
                                                                    "responsive": True,
                                                                },
                                                                className="mb-2",
                                                            ),
                                                            html.H5(
                                                                id="trend-title-movement",
                                                                className="text-muted text-center small",
                                                            ),
                                                        ]
                                                    ),
                                                    className="border-0 bg-light",
                                                ),
                                                dbc.Row(
                                                    [
                                                        dbc.Col(
                                                            [
                                                                html.H5(
                                                                    "Assets Breakdown",
                                                                    className="mb-3 fw-normal",
                                                                ),
                                                                html.Div(
                                                                    id="assets-breakdown-list",
                                                                    className="breakdown-container",
                                                                ),
                                                            ],
                                                            xs=12,
                                                            md=6,  # Stack on mobile
                                                            className="mb-3 mb-md-0",
                                                        ),
                                                        dbc.Col(
                                                            [
                                                                html.H5(
                                                                    "Liabilities Breakdown",
                                                                    className="mb-3 fw-normal",
                                                                ),
                                                                html.Div(
                                                                    id="liabilities-breakdown-list",
                                                                    className="breakdown-container",
                                                                ),
                                                            ],
                                                            xs=12,
                                                            md=6,  # Stack on mobile
                                                        ),
                                                    ],
                                                    className="mt-4",
                                                ),
                                            ],
                                            title="View Details",
                                            item_id="net-worth-details",
                                        )
                                    ],
                                    start_collapsed=True,
                                    className="mt-3",
                                ),
                                # Last updated info
                                html.Div(
                                    id="net-worth-last-updated",
                                    className="text-muted small text-end mt-3 last-updated",
                                ),
                            ]
                        ),
                        className="shadow-sm border-0",
                    ),
                    width=12,
                )
            ),
            # -- Sankey Diagram --
            dbc.Card(
                dbc.CardBody(
                    [
                        dbc.Row(
                            [
                                dbc.Col(
                                    dbc.InputGroup(
                                        [
                                            dbc.InputGroupText("Height:"),
                                            dbc.Input(
                                                id="sankey-height",
                                                type="number",
                                                min=100,
                                                step=200,
                                                style={"width": "100px"},
                                                size="sm",
                                            ),
                                        ],
                                        size="sm",
                                        style={"maxWidth": "200px"},
                                    ),
                                    xs=12,
                                    sm="auto",
                                    className="mb-2 mb-sm-0",
                                ),
                                dbc.Col(
                                    dbc.Checklist(
                                        id="trans-limiter",
                                        options=[
                                            {"label": "Transactions", "value": "enable"}
                                        ],
                                        value=["enable"],
                                        switch=True,
                                        className="dash-checklist-group",
                                    ),
                                    xs=6,
                                    sm="auto",
                                ),
                                dbc.Col(
                                    dbc.Checklist(
                                        id="lag-limiter",
                                        options=[
                                            {"label": "Lag limiter", "value": "enable"}
                                        ],
                                        value=["enable"],
                                        switch=True,
                                        className="dash-checklist-group",
                                    ),
                                    xs=6,
                                    sm="auto",
                                    className="ms-auto",
                                ),
                            ],
                            justify="start",
                            align="center",
                            className="mb-3 flex-wrap",
                        ),
                        dbc.Row(
                            dbc.Col(
                                dcc.Graph(
                                    id="sankey-diagram",
                                    figure=go.Figure(),
                                    config={"displaylogo": False, "responsive": True},
                                ),
                                className="graph-container px-0",  # remove horizontal padding
                            ),
                            className="g-0",  # remove gutters
                        ),
                        dbc.Row(
                            dbc.Col(
                                html.H5(
                                    id="sankey-title",
                                    className="text-muted text-center small",
                                )
                            )
                        ),
                    ]
                ),
                className="mt-4 shadow-sm border-0",
            ),
            # -- Bar Charts Row --
            dbc.Row(
                [
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(
                                [
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                [
                                                    dbc.Checklist(
                                                        id="data-display-options",
                                                        options=[
                                                            {
                                                                "label": "Show Budget",
                                                                "value": "budget",
                                                            }
                                                        ],
                                                        value=["budget"],
                                                        switch=True,
                                                        className="dash-checklist-group",
                                                    ),
                                                ],
                                                width=12,
                                            )
                                        ]
                                    ),
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                [
                                                    dcc.Graph(
                                                        id="bar-graph",
                                                        figure=go.Figure(),
                                                        config={
                                                            "displaylogo": False,
                                                            "responsive": True,
                                                        },
                                                    ),
                                                    html.H5(
                                                        id="bar-total-display",
                                                        className="text-muted text-end small",
                                                    ),
                                                ]
                                            )
                                        ]
                                    ),
                                ]
                            ),
                            className="shadow-sm border-0 h-100",
                        ),
                        xs=12,
                        md=6,  # Full width on mobile, half on desktop
                        className="mb-3 mb-md-0",
                    ),
                    dbc.Col(
                        dbc.Card(
                            dbc.CardBody(
                                [
                                    dcc.Graph(
                                        id="category-bar-graph",
                                        figure=go.Figure(),
                                        config={"displaylogo": False, "responsive": True},
                                    ),
                                    html.H5(
                                        id="category-total-display",
                                        className="text-muted text-end small",
                                    ),
                                ]
                            ),
                            className="shadow-sm border-0 h-100",
                        ),
                        xs=12,
                        md=6,  # Full width on mobile, half on desktop
                    ),
                ],
                className="mt-4",
            ),
            # -- Trend Graph --
            dbc.Card(
                dbc.CardBody(
                    [
                        dbc.Row(
                            dbc.Col(
                                dcc.Dropdown(
                                    id="trend-category-filter",
                                    placeholder="Filter by category",
                                    className="mb-3",
                                    multi=True,
                                    style={"borderColor": "#dee2e6"},
                                ),
                                width=12,
                            )
                        ),
                        html.Div(
                            dcc.Graph(
                                id="trend-graph",
                                figure=go.Figure(),
                                config={"displaylogo": False, "responsive": True},
                            ),
                            className="graph-container",
                        ),
                        html.H5(id="trend-title", className="text-muted text-center small"),
                    ]
                ),
                className="mt-4 shadow-sm border-0",
            ),
            # -- Income Trend Graph --
            dbc.Card(
                dbc.CardBody(
                    [
                        html.Div(
                            dcc.Graph(
                                id="trend-income-graph",
                                figure=go.Figure(),
                                config={"displaylogo": False, "responsive": True},
                            ),
                            className="graph-container",
                        ),
                        html.H5(
                            id="trend-title-inc",
                            className="text-muted text-center small",
                        ),
                    ]
                ),
                className="mt-4 shadow-sm border-0",
            ),
            # Hidden elements for storing data
            dcc.Store(id="net-worth-update-trigger", data={"initial_load": True}),
        ],
        id="main-container",
        fluid=True,
        style={
            "backgroundColor": "#f8f9fa",
            "minHeight": "100vh",
            "paddingTop": "2rem",
            "paddingBottom": "2rem",
        },
    )
#-----------------------------------------------------------------

# --- BACKEND ---
# --- CALLBACKS ---
def home_callbacks(app):
    
    # Database
    from database import get_db
    db = get_db()

    # -- Populate layout --
    @app.callback(
        [Output("trend-category-filter", "options"),
        Output("trend-category-filter", "value")],
        Input("url", "pathname")  # Trigger on page load
    )
    def populate_trend_category_filter(_):
        # Fetch categories from database
        categories_data = db.get_categories(current_user.id)
        category_options = [{"label": name, "value": name} for _, name in categories_data]
        
        # Get all values for pre-selection
        all_values = [opt['value'] for opt in category_options] if category_options else []
        
        return category_options, all_values
    
    # -- Filter panel --
    # Toggle collapse
    @app.callback(
        Output("filter-collapse", "is_open"),
        Input("filter-toggle", "n_clicks"),
        State("filter-collapse", "is_open")
    )
    @login_required
    def toggle_collapse(n, is_open):
        
        if n:
            return not is_open
        return is_open

    # Toggle radio items based on filter type
    @app.callback(
        Output("month-filter-options", "style"),
        Output("last-filter-options", "style"),
        Output("daterange-filter-options", "style"),
        Input("filter-type", "value")
    )
    @login_required
    def toggle_filter_options(filter_type):
        if filter_type == "month":
            return {"display": "block"}, {"display": "none"}, {"display": "none"}
        elif filter_type == "last":
            return {"display": "none"}, {"display": "block"}, {"display": "none"}
        else:  # daterange
            return {"display": "none"}, {"display": "none"}, {"display": "block"}

    # Update the year input based on the arrow button clicks
    @app.callback(
        Output("year-input", "value"),
        Input("year-increment", "n_clicks"),
        Input("year-decrement", "n_clicks"),
        State("year-input", "value")
    )
    @login_required
    def update_year(increment_clicks, decrement_clicks, current_year):
        ctx = callback_context
        if not ctx.triggered:
            return current_year
        button_id = ctx.triggered[0]["prop_id"].split(".")[0]
        if button_id == "year-increment":
            return current_year + 1
        elif button_id == "year-decrement":
            return current_year - 1
        return current_year
    
# ------------------------------------------------------------
# -- INDICATOR ELEMENTS --
# ------------------------------------------------------------

    # Callback to populate net worth viewer
    @app.callback(
        [Output('total-assets-display-homepage', 'children'),
        Output('total-liabilities-display-homepage', 'children'),
        Output('net-worth-display-homepage', 'children'),
        Output('assets-breakdown-list', 'children'),
        Output('liabilities-breakdown-list', 'children'),
        Output('net-worth-last-updated', 'children'),
        Output('spending-display-nw', 'children'),
        Output('income-display-nw', 'children'), 
        Output('spending-percent-nw', 'children'),
        Output('income-percent-nw', 'children')],
        [Input('net-worth-update-trigger', 'data'),
         Input('end-date-picker-movement', 'date')],
        prevent_initial_call=False
    )
    @login_required
    def populate_net_worth_viewer(trigger, end_date_input):
        
        # Format currency values
        def fmt(value):
            return f"${value:,.2f}"
        
        def fmtP(value):
            return f"{value:,.1f}%"
        
        snapshot = db.get_current_netWorth_snapshot(current_user.id)
        
        if not snapshot:
            return (
                "$0.00", "$0.00", "$0.00",
                html.P("No assets found", className="text-muted"),
                html.P("No liabilities found", className="text-muted"),
                "No snapshot available", "$0.00", "$0.00", "0.0%", "0.0%"
            )
        
        # Handle date formatting - snapshot_date might be string or date object
        snapshot_date = snapshot['snapshot_date']
        if isinstance(snapshot_date, str):
            last_updated_date = snapshot_date
        else:
            last_updated_date = snapshot_date.strftime('%Y-%m-%d')
        
        end_date = ""
        # Obtain running values
        if end_date_input:
            end_date = end_date_input
        else:
            # If no end date input, use today's date
            end_date=date.today().isoformat()

        total_spending_by_cat = db.get_total_spent_by_category_filtered(snapshot_date, end_date, current_user.id)
        total_spending = sum(amount for _, amount in total_spending_by_cat)

        total_income = db.get_total_income(snapshot_date, end_date, current_user.id)
        
        # Create asset breakdown list
        assets_list = dbc.ListGroup([
            dbc.ListGroupItem([
                dbc.Row([
                    dbc.Col(html.Strong(item['name']), width=6),
                    dbc.Col(fmt(item['amount']), width=4),
                    dbc.Col(item['type'].capitalize(), width=2)
                ]),
                html.Small(item['note'], className="text-muted") if item['note'] else None
            ], className="mb-2") 
            for item in snapshot['assets']
        ], flush=True) if snapshot['assets'] else html.P("No assets", className="text-muted")
        
        # Create liabilities breakdown list
        liabilities_list = dbc.ListGroup([
            dbc.ListGroupItem([
                dbc.Row([
                    dbc.Col(html.Strong(item['name']), width=6),
                    dbc.Col(fmt(item['amount']), width=4),
                    dbc.Col(item['type'].capitalize(), width=2)
                ]),
                html.Small(item['note'], className="text-muted") if item['note'] else None
            ], className="mb-2")
            for item in snapshot['liabilities']
        ], flush=True) if snapshot['liabilities'] else html.P("No liabilities", className="text-muted")

        # Handle created_at formatting - might be None, string, or datetime
        created_at = snapshot.get('created_at')
        if created_at:
            if isinstance(created_at, str):
                created_time = created_at.split(' ')[1][:5] if ' ' in created_at else ''
            else:
                created_time = created_at.strftime('%H:%M')
        else:
            created_time = ''
        
        last_updated = f"Last input: {last_updated_date}"

        spending_percent = (total_spending / snapshot['total_assets']) * 100 if snapshot['total_assets'] > 0 else 0.0
        income_percent = (total_income / snapshot['total_assets']) * 100 if snapshot['total_assets'] > 0 else 0.0

        return (
            fmt(snapshot['total_assets'] - total_spending + total_income),
            fmt(snapshot['total_liabilities']),
            fmt(snapshot['net_worth'] - total_spending + total_income),
            assets_list,
            liabilities_list,
            last_updated.strip(),
            fmt(total_spending), 
            fmt(total_income), 
            fmtP(spending_percent), 
            fmtP(income_percent)
        )
# ------------------------------------------------------------

# ------------------------------------------------------------
# -- DYNAMIC ELEMENTS --
# ------------------------------------------------------------

    # -- BAR GRAPH --
    @app.callback(
        Output("bar-graph", "figure"),
        Output("bar-total-display", "children"),
        Input("filter-type", "value"),
        Input("data-display-options", "value"),
        Input("year-input", "value"),
        Input("month-slider", "value"),
        Input("last-period-options", "value"),
        Input("custom-days-input", "value"),
        Input("start-date-picker", "date"),  # Add date range inputs
        Input("end-date-picker", "date")
    )
    @login_required
    def update_bar_graph(filter_type, data_display, year, month, last_period_value, custom_days, start_date_picker, end_date_picker):
        
        now = datetime.now()
        
        # Determine what data to display
        display_budget = "budget" in data_display
        
        # Handle different filter types
        if filter_type == "month":
            start_date = f"{year}-{month:02d}-01"
            last_day = calendar.monthrange(year, month)[1]
            end_date = f"{year}-{month:02d}-{last_day:02d}"
            title_suffix = f"{calendar.month_name[month]} {year}"
        elif filter_type == "last":
            # Validate inputs for "last period" mode
            if last_period_value == "custom":
                if custom_days is None or custom_days <= 0:
                    return go.Figure(), "Invalid custom days value"
                days = custom_days
            else:
                if last_period_value is None:
                    return go.Figure(), "No period selected"
                days = int(last_period_value)
        
            start_date = (now - timedelta(days=days)).strftime("%Y-%m-%d")
            end_date = now.strftime("%Y-%m-%d")
            title_suffix = f"Last {days} Days"
        else:  # Date range filter
            if not start_date_picker or not end_date_picker:
                return go.Figure(), "Please select both start and end dates"
                
            start_date = start_date_picker
            end_date = end_date_picker
            title_suffix = f"{start_date} to {end_date}"

        # Get spending data
        data = db.get_total_spent_by_category_filtered(start_date, end_date, current_user.id)
        if not data:
            return go.Figure(), f"Total: $0.00"

        categories, totals = zip(*data)
        categories = list(categories)  # list with fixed order
        totals = list(totals)
        total = sum(totals)

        # Create figure
        fig = go.Figure()
        
        # Determine colors based on budget comparison and display_budget setting
        if filter_type == "month" and display_budget:
            # Get budget data for color coding
            budget_data = db.get_budget_by_category(current_user.id)
            budget_dict = dict(budget_data)
            budget_values = [budget_dict.get(cat, None) for cat in categories]
            
            # Create colors based on budget comparison
            spending_colors = []
            for cat, spent, budget in zip(categories, totals, budget_values):
                if budget is None:
                    # No budget set - use neutral blue
                    spending_colors.append('#1f77b4')
                elif spent <= budget:
                    # Under budget - green
                    spending_colors.append('#2ca02c')
                else:
                    # Over budget - red
                    spending_colors.append('#d62728')
            
            # Add spending bars with budget-aware colors
            fig.add_trace(go.Bar(
                x=categories,
                y=totals,
                name='Spending',
                marker_color=spending_colors,
                customdata=categories,
                width=0.4,
                showlegend=False  # Don't show in legend since colors vary
            ))
            
            # Add budget bars if requested
            if any(b is not None for b in budget_values):
                fig.add_trace(go.Bar(
                    x=categories,
                    y=budget_values,
                    name='Budget',
                    marker_color='#add8e6',
                    customdata=categories,
                    opacity=0.3,
                    width=0.2
                ))
                
            # Add legend entries for color coding (invisible bars just for legend)
            fig.add_trace(go.Bar(
                x=[None], y=[None],
                name='Within Budget',
                marker_color='#2ca02c',
                showlegend=True
            ))
            fig.add_trace(go.Bar(
                x=[None], y=[None],
                name='Over Budget',
                marker_color='#d62728',
                showlegend=True
            ))
            fig.add_trace(go.Bar(
                x=[None], y=[None],
                name='No Budget Set',
                marker_color='#1f77b4',
                showlegend=True
            ))
            
        else:
            # No budget display or not month filter - use neutral blue for all
            fig.add_trace(go.Bar(
                x=categories,
                y=totals,
                name='Spending',
                marker_color='#1f77b4',
                customdata=categories,
                width=0.4
            ))

        fig.update_layout(
            title=f"<b>Total Spent per Category - {title_suffix}</b>",
            xaxis_title="Category",
            yaxis_title="Amount, $",
            template="gridon",
            bargap=0.4,
            yaxis=dict(
                automargin=True,
            ),
            xaxis=dict(
                tickangle = -25,
                automargin=True,
            ),
            margin=dict(t=60),
            barmode='overlay',
            autosize = True
        )

        return fig, f"Total: ${total:,.2f}"

    # SUPPLEMENT CATEGORY BAR GRAPH CALLBACK
    @app.callback(
        Output("category-bar-graph", "figure"),
        Output("category-total-display", "children"),
        Input("bar-graph", "clickData"),
        Input("filter-type", "value"),
        Input("year-input", "value"),
        Input("month-slider", "value"),
        Input("last-period-options", "value"),
        Input("custom-days-input", "value"),
        Input("start-date-picker", "date"),  # Add date range inputs
        Input("end-date-picker", "date")
    )
    @login_required
    def update_category_graph(click_data, filter_type, year, month, last_period_value, custom_days, start_date_picker, end_date_picker):
        if not click_data:
            return go.Figure(), ""

        # Extract clicked category name
        category = click_data['points'][0]['customdata']

        # Determine date range based on filter settings
        now = datetime.now()
        if filter_type == "month":
            start_date = f"{year}-{month:02d}-01"
            last_day = calendar.monthrange(year, month)[1]
            end_date = f"{year}-{month:02d}-{last_day:02d}"
        elif filter_type == "last":
            days = custom_days if last_period_value == "custom" else int(last_period_value)
            start_date = (now - timedelta(days=days)).strftime("%Y-%m-%d")
            end_date = now.strftime("%Y-%m-%d")
        else:  # Date range filter
            if not start_date_picker or not end_date_picker:
                return go.Figure(), "Please select both start and end dates"
            start_date = start_date_picker
            end_date = end_date_picker

        # Query data (your existing code here)
        data = db.get_transactions_for_category(category, start_date, end_date, current_user.id)
        if not data:
            return go.Figure(), ""

        merchants, amounts = zip(*data)
        total = sum(amounts)

        # Create truncated labels for display (max 20 chars)
        truncated_merchants = [m[:20] + '...' if len(m) > 20 else m for m in merchants]

        # Create a color sequence for duplicate merchants
        merchant_counts = {}
        colors = []
        color_palette = [
            '#1f77b4',  # Blue
            '#ff7f0e',  # Orange
            '#2ca02c',  # Green
            '#d62728',  # Red
            '#9467bd',  # Purple
            '#8c564b'   # Brown
        ]

        for merchant in merchants:
            if merchant not in merchant_counts:
                merchant_counts[merchant] = 0
            merchant_counts[merchant] += 1
            
            # Cycle through colors based on merchant count (1-6 then repeat)
            color_index = (merchant_counts[merchant] - 1) % len(color_palette)
            colors.append(color_palette[color_index])

        # Create figure with colored bars
        fig = go.Figure(
            data=[go.Bar(
                x=amounts, 
                y=truncated_merchants, 
                orientation="h",
                marker_color=colors,
                marker_line_color='rgba(0,0,0,0.5)',
                marker_line_width=1,
                opacity=0.8,
                customdata=list(zip(merchants, amounts)),  # Store full merchant names and amounts
                hovertemplate=(
                    "<b>%{customdata[0]}</b><br>" +  # Full merchant name
                    "Amount: $%{x:,.2f}<br>" +      # Formatted amount (same as x value)
                    "<extra></extra>"                # Remove secondary box
                )
            )],
            layout=go.Layout(
                title={
                    "text": f"<b>Transaction in {category}</b>",
                },
                template="gridon",
                yaxis=dict(
                    tickangle=-45,
                    automargin=True,
                ),
                xaxis=dict(
                    automargin=True,
                ),
                bargap=0.4,
                margin=dict(
                    pad = 15,
                    t=60),
                autosize=True
            )
        )

        return fig, f"Total: ${total:,.2f}"
# -------------------------------------------------------------------------

# -- Time trace --
        
    # Category trend graph
    @app.callback(
        Output("trend-graph", "figure"),
        Output("trend-title", "children"),
        Input("year-input", "value"),
        Input("month-slider", "value"),
        Input("filter-type", "value"),
        Input("trend-category-filter", "value")
    )
    @login_required
    def update_trend_graph(year, month, filter_type, category_filter):
        # Only for month vew
        if filter_type != "month":
            return go.Figure(), ""
            
        # Get monthly data for all categories
        monthly_data = db.get_monthly_spending_by_category(year, month, current_user.id)
        
        if not monthly_data:
            return go.Figure(), f"No data for {year} until {calendar.month_name[month]}"
        
        # Organize data by category
        categories = {}
        for category, month_num, amount in monthly_data:
            # Skip categories not in the filter
            if not category_filter or category not in category_filter:
                continue
                
            if category not in categories:
                categories[category] = {}
            categories[category][int(month_num)] = amount

        fig = go.Figure()
        
        month_names = [calendar.month_abbr[m] for m in range(1, month+1)]
        
        for category in categories:
            # Fill in data for all months (zero if missing)
            amounts = []
            for m in range(1, month+1):
                amounts.append(categories[category].get(m, 0))
            
            fig.add_trace(go.Scatter(
                x=month_names,
                y=amounts,
                name=category,
                mode='lines+markers',
                marker=dict(size=8),
                line=dict(width=2)
            ))
        
        fig.update_layout(
            title=f"<b>Spending trend per Category</b>",
            yaxis_title="Amount, $",
            template="gridon",
            hovermode="x unified",
            legend=dict(
                orientation="h",
                yanchor="top",
                y=-0.1,  # Position below the plot area
                xanchor="center",
                x=0.5
            ),
            autosize=True
        )
        
        return fig, f"Trend from January to {calendar.month_name[month]} {year}"
    
    # Income net trend graph
    @app.callback(
        Output("trend-income-graph", "figure"),
        Output("trend-title-inc", "children"),
        Input("year-input", "value"),
        Input("month-slider", "value"),
        Input("filter-type", "value")
    )
    @login_required
    def update_net_income_graph(year, month, filter_type):
        
        # Only if month view
        if filter_type != "month":
            return go.Figure(), ""
            
        # Get data
        monthly_data = db.get_monthly_spending_by_category(year, month, current_user.id)
        income_data = db.get_monthly_income_till_date(year, month, current_user.id)

        if not monthly_data or not income_data:
            return go.Figure(), f"No data for {year} until {calendar.month_name[month]}"
        
        # Organize spending by category
        categories = {}
        for category, month_num, amount in monthly_data:
            if category not in categories:
                categories[category] = {}
            categories[category][int(month_num)] = amount
            
        # Organize income by month
        incomes = {}
        for month_num, income_amount in income_data:
            incomes[int(month_num)] = income_amount
        
        fig = go.Figure()
        month_names = [calendar.month_abbr[m] for m in range(1, month+1)]
        
        # Calculate net income
        net_incomes = []
        for m in range(1, month+1):
            total_spending = sum(
                categories[category].get(m, 0)
                for category in categories
            )
            net_income = incomes.get(m, 0) - total_spending
            net_incomes.append(net_income)
        
        # Plot
        fig.add_trace(go.Scatter(
            x=month_names,
            y=net_incomes,
            name="Net Income",
            mode='lines+markers',
            marker=dict(size=8),
            line=dict(width=2, color='green')  # Green for positive cash flow
        ))
        
        # Add zero reference line
        fig.add_hline(
            y=0,
            line_dash="dot",
            line_color="red",
            annotation_text="Break-even",
            annotation_position="bottom right"
        )
        
        fig.update_layout(
            title=f"<b>Net Income Trend</b>",
            xaxis_title="Month",
            yaxis_title="Net Income, $",
            template="gridon",
            hovermode="x unified",
            #margin=dict(t=100),
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            autosize = True
        )
        
        return fig, f"Trend from January to {calendar.month_name[month]} {year}"
# --------------------------------------------------------------------------------

# -- SANKEY DIAGRAM --
    @app.callback(
        Output("sankey-diagram", "figure"),
        Output("sankey-title", "children"),
        Output("sankey-height", "value"),
        Input("filter-type", "value"),
        Input("year-input", "value"),
        Input("month-slider", "value"),
        Input("last-period-options", "value"),
        Input("custom-days-input", "value"),
        Input("start-date-picker", "date"),  # New input
        Input("end-date-picker", "date"),     # New input
        Input("lag-limiter", "value"),
        Input("trans-limiter", "value")
    )
    @login_required
    def update_sankey_diagram(filter_type, year, month, last_period_value, custom_days, start_date_picker, end_date_picker, lag_limiter, trans_limiter):
        now = datetime.now()
        
        if filter_type == "month":
            start_date = f"{year}-{month:02d}-01"
            last_day = calendar.monthrange(year, month)[1]
            end_date = f"{year}-{month:02d}-{last_day:02d}"
            title_suffix = f"{calendar.month_name[month]} {year}"
        elif filter_type == "last":
            # Validate inputs for "last period" mode
            if last_period_value == "custom":
                if custom_days is None or custom_days <= 0:
                    return go.Figure(), "No period selected", no_update
                days = custom_days
            else:
                if last_period_value is None:
                    return go.Figure(), "No period selected", no_update
                days = int(last_period_value)
            
            start_date = (now - timedelta(days=days)).strftime("%Y-%m-%d")
            end_date = now.strftime("%Y-%m-%d")
            title_suffix = f"Last {days} Days"
        else:  # Date range filter
            if not start_date_picker or not end_date_picker:
                return go.Figure(), "Please select both start and end dates", no_update
            
            start_date = start_date_picker
            end_date = end_date_picker
            title_suffix = f"{start_date} to {end_date}"

        # OPTIMIZATION: Limit VISUALIZED transactions to top 10 per category if needed
        if lag_limiter and "enable" in lag_limiter:

            # Get data
            income_data, spending_data, all_transactions_data = db.get_all_transactions_flow(start_date, end_date, current_user.id)

            if not income_data and not spending_data and not all_transactions_data:
                    return go.Figure(), f"No data available for {title_suffix}", no_update

            if len(all_transactions_data) > 100:
                
                # Calculate accurate category totals using ALL transactions
                category_totals = {}
                for category, _, amount in all_transactions_data:
                    category_totals[category] = category_totals.get(category, 0) + amount
                
                # Update spending_data with accurate totals
                spending_data = [(category, category_totals[category]) for category in category_totals]
                    
                transactions_by_category = defaultdict(list)
                for category, merchant, amount in all_transactions_data:
                    transactions_by_category[category].append((amount, merchant))
                
                # Get top 10 transactions per category for visualization only
                viz_transactions = []
                for category in transactions_by_category:
                    # Take first 10 transactions without sorting
                    category_transactions = transactions_by_category[category][:10]
                    for amount, merchant in category_transactions:
                        viz_transactions.append((category, merchant, amount))
                
                transactions_data = viz_transactions
                title_suffix += " (Top 10 per category limit)"

            else:
                transactions_data = all_transactions_data

        else:

            # Get data no limits no nothing
            income_data, spending_data, transactions_data = db.get_all_transactions_flow(start_date, end_date, current_user.id)
            
            if not income_data and not spending_data and not transactions_data:
                return go.Figure(), f"No data available for {title_suffix}", no_update
        
        # Create nodes, links, and COLOR settings
        labels = []
        sources = []
        targets = []
        values = []
        colors = []
        
        opacityTarget = 0.6
        greenColor = 'rgba(34,139,34, 0.6)'
        redColor = 'rgba(255,0,0, 0.4)'
        
        # Create a dictionary to map labels to indices
        label_to_index = {}
        current_index = 0
        
        # Add income sources (first level)
        income_total = 0
        for source, amount in income_data:
            if source not in label_to_index:
                label_to_index[source] = current_index
                labels.append(source)
                colors.append(greenColor)  # Green for income
                current_index += 1
            income_total += amount
            
        # Add spending categories (second level)
        spending_total = 0
        for category, amount in spending_data:
            if category not in label_to_index:
                label_to_index[category] = current_index
                labels.append(category)
                colors.append(redColor)  # Red for spending
                current_index += 1
            spending_total += amount
            
        savings_amount = income_total - spending_total
        
        # Add a total income node
        if savings_amount >= 0:
            total_income_label = f"Income (${income_total:.2f})<br>Spent (${spending_total:.2f})"
        else:
            total_income_label = f"Income (${income_total:.2f})<br>Spent (${spending_total:.2f})<br>Net -(${abs(savings_amount):.2f})"
        
        label_to_index[total_income_label] = current_index
        labels.append(total_income_label)
        if savings_amount > 0:
            colors.append(greenColor)
        else:
            colors.append(redColor)
        current_index += 1
        
        # Link income sources to total income
        for source, amount in income_data:
            sources.append(label_to_index[source])
            targets.append(label_to_index[total_income_label])
            values.append(amount)
        
        # Link total income to spending categories
        for category, amount in spending_data:
            sources.append(label_to_index[total_income_label])
            targets.append(label_to_index[category])
            values.append(amount)
            
        # Add savings
        if savings_amount > 0:
            savings_label = f"Saved (${savings_amount:.2f})"
            label_to_index[savings_label] = current_index
            labels.append(savings_label)
            colors.append('rgba(160, 160, 160, 0.6)')
            current_index += 1
            
        # Link total income to savings
        if savings_amount > 0:
            sources.append(label_to_index[total_income_label])
            targets.append(label_to_index[savings_label])
            values.append(savings_amount)
        
        node_x = []
        node_y = []
        padding = 15
        transaction_threshhold = 30
        
        if trans_limiter and "enable" in trans_limiter:
            # Add individual transactions (third level)
            transaction_colors = [
                f'rgba(255, 127, 14, {opacityTarget})',    # Orange
                f'rgba(148, 103, 189, {opacityTarget})',   # Purple
                f'rgba(140, 86, 75, {opacityTarget})',     # Brown
                f'rgba(227, 119, 194, {opacityTarget})',   # Pink
                f'rgba(127, 127, 127, {opacityTarget})',   # Gray
                f'rgba(188, 189, 34, {opacityTarget})',    # Olive
                f'rgba(23, 190, 207, {opacityTarget})',    # Cyan
                f'rgba(44, 160, 44, {opacityTarget})',     # Green
                f'rgba(31, 119, 180, {opacityTarget})',    # Blue
                f'rgba(152, 223, 138, {opacityTarget})',   # Light Green
                f'rgba(174, 199, 232, {opacityTarget})',   # Light Blue
                f'rgba(197, 176, 213, {opacityTarget})',   # Light Purple
                f'rgba(196, 156, 148, {opacityTarget})',   # Light Brown
                f'rgba(247, 182, 210, {opacityTarget})',   # Light Pink
                f'rgba(219, 219, 141, {opacityTarget})',   # Light Yellow
                f'rgba(158, 218, 229, {opacityTarget})',   # Light Cyan
                f'rgba(255, 187, 120, {opacityTarget})',   # Light Orange
                f'rgba(199, 199, 199, {opacityTarget})'    # Light Gray
            ]
            
            num_transactions = 0
            transaction_labels = []
            color_idx = 0
            for category, merchant, amount in transactions_data:
                
                transaction_label = f"{merchant[:20] + '...' if len(merchant) > 20 else merchant} (${amount:.2f})"
                if transaction_label not in label_to_index:
                    label_to_index[transaction_label] = current_index
                    labels.append(transaction_label)
                    colors.append(transaction_colors[color_idx % len(transaction_colors)])
                    color_idx += 1
                    current_index += 1
                
                # Link category to transaction
                sources.append(label_to_index[category])
                targets.append(label_to_index[transaction_label])
                values.append(amount)

                num_transactions += 1
                transaction_labels.append(transaction_label)
        
            # Create the Sankey diagram
            # Calculate positions

            # Define vertical positions for each level
            LEVEL_POSITIONS = {
                'income': 0.1,        # Leftmost (sources)
                'total': 0.3,         # Center left
                'categories': 0.35,    # Center right
                'savings': 0.85,       # Above center
            }
            
            for label in labels:
                
                if label in [source for source, _ in income_data]:
                    # Income sources
                    node_x.append(0)
                    node_y.append(LEVEL_POSITIONS['income'])

                elif label == total_income_label:
                    # Total income
                    node_x.append(0.33)
                    node_y.append(LEVEL_POSITIONS['total'])

                # Spending categories (center right)
                elif label in [category for category, _ in spending_data]:
                    node_x.append(0.66)
                    node_y.append(LEVEL_POSITIONS['categories'])

                elif label in transaction_labels:
                    # Transactions
                    if num_transactions > transaction_threshhold:
                        # Transactions distribute positions so that no conflict with savings
                        index = transaction_labels.index(label)
                        if num_transactions == 1:
                            position = 0.5  # Center if only one transaction
                        else:
                            position = 0.0001 + (0.9999 * index / (num_transactions - 1))
                        node_x.append(1.0)
                        node_y.append(position)
                    else:
                        node_x.append(1.0)
                        node_y.append(0.35)
                    
                # Savings label
                elif savings_amount > 0 and label == savings_label:
                    if label == savings_label:
                        # Savings
                        node_x.append(0.5)
                        node_y.append(LEVEL_POSITIONS['savings'])
        else:
            # Define vertical positions for each level
            LEVEL_POSITIONS = {
                'income': 0.0,        # Leftmost (sources)
                'total': 0.0001,         # Center left
                'categories': 0.0005,    # Center right
                'savings': 0.95,       # Above center
            }
            
            for label in labels:
                
                if label in [source for source, _ in income_data]:
                    # Income sources
                    node_x.append(0)
                    node_y.append(LEVEL_POSITIONS['income'])

                elif label == total_income_label:
                    # Total income
                    node_x.append(0.4)
                    node_y.append(LEVEL_POSITIONS['total'])

                # Spending categories (center right)
                elif label in [category for category, _ in spending_data]:
                    node_x.append(0.8)
                    node_y.append(LEVEL_POSITIONS['categories'])
                    
                # Savings label
                elif savings_amount > 0 and label == savings_label:
                    if label == savings_label:
                        # Savings
                        node_x.append(0.6)
                        node_y.append(LEVEL_POSITIONS['savings'])

        fig = go.Figure(go.Sankey(    
            arrangement='snap',
            node=dict(
                pad=padding,
                thickness=15,
                line=dict(color="black", width=0.5),
                label=labels,
                color=colors,
                x = node_x,
                y = node_y
            ),
            link=dict(
                source=sources,
                target=targets,
                value=values,
                color=[redColor if labels[trg] in [category for category, _ in spending_data] 
                        else greenColor if labels[src] in [source for source, _ in income_data]
                        else colors[trg]
                        for trg, src in zip(targets, sources)]
            )
        ))
        
        if trans_limiter and "enable" in trans_limiter:
            auto_height = 300 + num_transactions * 20
            if auto_height > 700:
                auto_height = 700
            
            fig.update_layout(
                title = f"<b>Money Flow diagram</b>",
                font_size=15,
                autosize=True,
                #margin=dict(t=0, l=0, r=0, b=20),
                height=auto_height
            )
        else:
            auto_height = 550
        
        return fig, f"Flow for {title_suffix}", auto_height
    
    # Change height upon user input
    @app.callback(
        Output("sankey-diagram", "figure", allow_duplicate=True),
        Input("sankey-height", "value"),
        State("sankey-diagram", "figure"),
        prevent_initial_call=True
    )
    @login_required
    def update_height(user_height, current_figure):
        if current_figure is None:
            return no_update
            
        current_figure['layout']['height'] = user_height
        return current_figure
# --------------------------------------------------------------------------------

# -- MOVEMENT TREND GRAPH AND NET WORTH GRAPH HANDLER --

    @app.callback(
        Output('trend-movement-graph', 'figure'),
        Output('trend-title-movement', 'children'),
        Input('start-date-picker-movement', 'date'),
        Input('end-date-picker-movement', 'date'),
        Input('show-net-worth-movement', 'value')
    )
    @login_required
    def update_movement_graph(start_date, end_date, show_net_worth):
        
        title_text = ""
        graph_title = ""

        # Create the figure
        fig = go.Figure()
        
        if show_net_worth and "enable" in show_net_worth:
            # Get the most recent net worth snapshot before start date
            current_snapshot = db.get_current_netWorth_snapshot(current_user.id)
            
            if current_snapshot:

                # Convert date strings to date objects
                snapshot_date = current_snapshot['snapshot_date']

                start_date_obj = date.fromisoformat(snapshot_date)
                end_date_obj = date.fromisoformat(end_date) if end_date else date.today()
                
                # Get the movement data from your database
                movement_data = db.get_movement_trend(start_date_obj, end_date_obj, current_user.id)

                # Initialize running totals
                dates = [item['date'] for item in movement_data]
                net_worth_values = []
                asset_values = []
                
                # Start with snapshot values
                current_assets = current_snapshot['total_assets']
                start_net_worth = current_snapshot['net_worth']
                
                # Calculate daily net worth progression
                for day in movement_data:
                    current_assets += day['total_income'] - day['total_spent']
                    net_worth = current_assets - current_snapshot['total_liabilities']
                    net_worth_values.append(net_worth)
                    asset_values.append(current_assets)
                
                # Add net worth trace (blue)
                fig.add_trace(go.Scatter(
                    x=dates,
                    y=net_worth_values,
                    name='Projected Net Worth',
                    line=dict(color='blue', width=2),
                    mode='lines+markers',
                    hovertemplate='Date: %{x}<br>Net Worth: $%{y:,.2f}<extra></extra>'
                ))
                
                # Add starting net worth reference line
                fig.add_hline(
                    y=start_net_worth,
                    line_dash="dot",
                    line_color="red",
                    annotation_text=f"Starting Net Worth: ${start_net_worth:,.2f}",
                    annotation_position="bottom right"
                )
                
                title_text = (f"Starting: ${start_net_worth:,.2f} | "
                            f"Current: ${net_worth_values[-1]:,.2f} | "
                            f"Change: ${net_worth_values[-1] - start_net_worth:,.2f} "
                            f"({(net_worth_values[-1]/start_net_worth - 1)*100:.1f}%)")
                
                graph_title = "Net Worth porjection based on income/spending trend"

            else:
                title_text = "No net worth snapshot found - please create one first"
                graph_title = ""
        
        else:
            # Convert date strings to date objects
            start_date_obj = date.fromisoformat(start_date) if start_date else date.today() - timedelta(days=30)
            end_date_obj = date.fromisoformat(end_date) if end_date else date.today()
            
            # Get the movement data from your database
            movement_data = db.get_movement_trend(start_date_obj, end_date_obj, current_user.id)

            # Original spending/income graph logic
            dates = [item['date'] for item in movement_data]
            spending = [item['total_spent'] for item in movement_data]
            income = [item['total_income'] for item in movement_data]
            
            # Add spending trace (red)
            fig.add_trace(go.Scatter(
                x=dates,
                y=spending,
                name='Spending',
                line=dict(color='red'),
                mode='lines+markers',
                hovertemplate='Date: %{x}<br>Amount: $%{y:.2f}<extra></extra>'
            ))
            
            # Add income trace (green)
            fig.add_trace(go.Scatter(
                x=dates,
                y=income,
                name='Income',
                line=dict(color='green'),
                mode='lines+markers',
                hovertemplate='Date: %{x}<br>Amount: $%{y:.2f}<extra></extra>'
            ))

            # Calculate totals for the title
            total_spent = sum(spending)
            total_income = sum(income)
            net = total_income - total_spent
            
            title_text = f"Total Income: ${total_income:,.2f} | Total Spending: ${total_spent:,.2f} | Net: ${net:,.2f} from {start_date_obj} to {end_date_obj}"

            graph_title = "Daily Income and Spending Trend"
        
        # Update layout
        fig.update_layout(
            title=f"<b>{graph_title}</b>",
            xaxis_title='Date',
            yaxis_title='Amount ($)',
            hovermode='x unified',
            template ="gridon",
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            ),
            autosize = True
            #margin=dict(l=20, r=20, t=60, b=20)
        )
        
        return fig, title_text
    
    # Start date picker visibility toggle
    @app.callback(
        [Output('start-date-picker-movement', 'style'),
        Output('start-date-label-movement', 'style')],
        [Input('show-net-worth-movement', 'value')]
    )
    @login_required
    def toggle_date_picker_visibility(net_worth_switch):
        # If switch is enabled, hide start date
        if net_worth_switch and "enable" in net_worth_switch:
            return {'display': 'none'}, {'display': 'none'}
        # Otherwise show
        return {'margin-right': '10px'}, {'display': 'block'}
    
# --------------------------------------------------------------------------------