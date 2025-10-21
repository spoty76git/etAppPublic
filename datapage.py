from datetime import datetime, timedelta
import dash_bootstrap_components as dbc
import pandas as pd
from functools import wraps

from dash import html, dcc, Input, Output, State, callback_context, no_update, ALL
from dash.exceptions import PreventUpdate

# Code injector additional imports
import io
import base64

import sys

# Net Worth Manager unique id for buttons
import uuid
import json

# Security
from flask_login import current_user
def authenticate_callback(func):
    """Decorator to authenticate Dash callbacks"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated:
            raise PreventUpdate
        return func(*args, **kwargs)
    return wrapper

# --- FRONTEND ---
def data_page_layout():
    
    # Only load data if authenticated
    if not current_user.is_authenticated:
        return dbc.Container(
            dbc.Alert("Please login to access this page", color="danger"),
            className="mt-5"
        )

    return dbc.Container(
        [
            html.H2("Manage Data", className="mb-4"),
            dbc.Accordion(
                [
                    # -- TRANSACTION ADDER --
                    dbc.AccordionItem(
                        [
                            dbc.Form(
                                [
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                dcc.Dropdown(
                                                    id="tm-category",
                                                    placeholder="Select category",
                                                    className="mb-3",
                                                )
                                            )
                                        ]
                                    ),
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                dbc.Input(
                                                    id="tm-merchant",
                                                    placeholder="Merchant",
                                                    type="text",
                                                    className="mb-3",
                                                )
                                            )
                                        ]
                                    ),
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                dbc.Input(
                                                    id="tm-amount",
                                                    placeholder="Amount ($)",
                                                    type="number",
                                                    className="mb-3",
                                                )
                                            )
                                        ]
                                    ),
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                dbc.Input(
                                                    id="tm-note",
                                                    placeholder="Note",
                                                    type="text",
                                                    className="mb-3",
                                                )
                                            )
                                        ]
                                    ),

                                    # ------ TAGS SECTION ------
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                [
                                                    dbc.InputGroup(
                                                        [
                                                            dbc.Input(
                                                                id="tm-tag-input",
                                                                placeholder="Add tags (Enter to add)",
                                                                type="text",
                                                                className="mb-2",
                                                            ),
                                                            dbc.InputGroupText(
                                                                html.I(
                                                                    className="fas fa-tag"
                                                                ),
                                                                style={
                                                                    "background-color": "#f8f9fa"
                                                                },
                                                            ),
                                                        ]
                                                    ),
                                                    # Dropdown for tag suggestions
                                                    dbc.Collapse(
                                                        dbc.Card(
                                                            dbc.CardBody(
                                                                id="tag-suggestions",
                                                                children=[],
                                                                style={
                                                                    "max-height": "150px",
                                                                    "overflow-y": "auto",
                                                                    "padding": "5px",
                                                                },
                                                            ),
                                                            style={
                                                                "position": "absolute",
                                                                "z-index": "1000",
                                                                "width": "100%",
                                                            },
                                                        ),
                                                        id="tag-suggestions-collapse",
                                                        is_open=False,
                                                    ),
                                                    # Display selected tags
                                                    html.Div(
                                                        id="selected-tags-display",
                                                        children=[],
                                                        className="mb-3",
                                                        style={"min-height": "30px"},
                                                    ),
                                                    # Store for selected tags
                                                    dcc.Store(
                                                        id="selected-tags-store",
                                                        data=[],
                                                    ),
                                                ]
                                            )
                                        ]
                                    ),

                                    # ---------- DATE PICKER WITH INCREMENT/DECREMENT BUTTONS ----------
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                dbc.Button(
                                                    html.I(
                                                        className="fas fa-arrow-left"
                                                    ),
                                                    id="tm-date-decrement",
                                                    color="light",
                                                    className="p-2 border rounded",
                                                    style={"margin-right": "5px"},
                                                ),
                                                width="auto",
                                            ),
                                            dbc.Col(
                                                dcc.DatePickerSingle(
                                                    id="tm-date",
                                                    date=datetime.today().date(),
                                                    display_format="MMM Do, YY",
                                                    style={"margin-bottom": "5px"},
                                                ),
                                                width="auto",
                                            ),
                                            dbc.Col(
                                                dbc.Button(
                                                    html.I(
                                                        className="fas fa-arrow-right"
                                                    ),
                                                    id="tm-date-increment",
                                                    color="light",
                                                    className="p-2 border rounded",
                                                    style={"margin-left": "5px"},
                                                ),
                                                width="auto",
                                            ),
                                        ],
                                        align="center",
                                        justify="start",
                                        className="g-0",
                                    ),
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                dbc.Checkbox(
                                                    id="tm-recurring",
                                                    label="Recurring",
                                                    value=False,
                                                    className="mb-3",
                                                )
                                            )
                                        ]
                                    ),
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                dbc.Button(
                                                    "Add Transaction",
                                                    id="add-transaction-btn",
                                                    color="primary",
                                                    className="mt-2",
                                                ),
                                                id="button-container",
                                            ),
                                            dcc.Interval(
                                                id="button-reset-interval",
                                                disabled=True,
                                                interval=1000,
                                                n_intervals=0,
                                            ),
                                        ]
                                    ),
                                ]
                            )
                        ],
                        title="Transaction manager",
                        item_id="transaction_manager",
                    ),
                    # -- CATEGORY MANAGER --
                    dbc.AccordionItem(
                        [
                            dbc.Row(
                                [
                                    dbc.Col(
                                        dbc.Input(
                                            id="cm-category",
                                            placeholder="Category",
                                            type="text",
                                            className="mb-3",
                                        )
                                    ),
                                    dbc.Col(
                                        dbc.Input(
                                            id="cm-budget",
                                            placeholder="Budget",
                                            type="number",
                                            className="mb-3",
                                        )
                                    ),
                                    dbc.Col(
                                        dbc.Button(
                                            "Add Category",
                                            id="add-category-btn",
                                            color="primary",
                                            className="mt-2",
                                        ),
                                        id="button-container",
                                    ),
                                    dcc.Interval(
                                        id="button-reset-interval-cat",
                                        disabled=True,
                                        interval=1000,
                                        n_intervals=0,
                                    ),
                                ]
                            ),
                            dbc.Row(
                                [
                                    dbc.Col(
                                        dbc.Button(
                                            "Refresh",
                                            id="refresh-categories-btn",
                                            color="primary",
                                            className="mb-3",
                                        ),
                                        width=12,
                                    )
                                ]
                            ),
                            html.Div(id="categories-list", className="mt-3"),
                        ],
                        title="Category manager",
                        item_id="category_manager",
                    ),
                    # -- INCOME VIEWER
                    dbc.AccordionItem(
                        [
                            dbc.Row(
                                [
                                    dbc.Col(
                                        dbc.Input(
                                            id="im-source",
                                            placeholder="Source",
                                            type="text",
                                            className="mb-3",
                                        )
                                    ),
                                    dbc.Col(
                                        dbc.Input(
                                            id="im-amount",
                                            placeholder="Amount ($)",
                                            type="number",
                                            className="mb-3",
                                        )
                                    ),
                                    dbc.Col(
                                        dbc.Button(
                                            "Add income",
                                            id="add-income-btn",
                                            color="primary",
                                            className="mt-2",
                                        ),
                                        id="button-container",
                                    ),
                                    dcc.Interval(
                                        id="button-reset-interval-inc",
                                        disabled=True,
                                        interval=1000,
                                        n_intervals=0,
                                    ),
                                ]
                            ),
                            dbc.Row(
                                [
                                    dbc.Col(
                                        dbc.Button(
                                            html.I(className="fas fa-arrow-left"),
                                            id="im-date-decrement",
                                            color="light",
                                            className="p-2 border rounded",
                                            style={
                                                "margin-right": "5px",
                                                "margin-bottom": "40px",
                                            },
                                        ),
                                        width="auto",
                                    ),
                                    dbc.Col(
                                        dcc.DatePickerSingle(
                                            id="im-date",
                                            date=datetime.today().date(),
                                            display_format="MMM Do, YY",
                                            style={"margin-bottom": "40px"},
                                        ),
                                        width="auto",
                                    ),
                                    dbc.Col(
                                        dbc.Button(
                                            html.I(className="fas fa-arrow-right"),
                                            id="im-date-increment",
                                            color="light",
                                            className="p-2 border rounded",
                                            style={
                                                "margin-left": "5px",
                                                "margin-bottom": "40px",
                                            },
                                        ),
                                        width="auto",
                                    ),
                                ],
                                align="center",
                                justify="start",
                                className="g-0",
                            ),
                            dbc.Row(
                                [
                                    dbc.Col(
                                        dbc.Input(
                                            id="iv-search",
                                            placeholder="Search income...",
                                            type="text",
                                            className="mb-3",
                                        ),
                                        width=4,
                                    ),
                                    dbc.Col(
                                        dbc.InputGroup(
                                            [
                                                dbc.InputGroupText("Limit:"),
                                                dbc.Input(
                                                    id="iv-num-income-limit",
                                                    type="number",
                                                    value=40,
                                                    min=1,
                                                    step=1,
                                                    style={"width": "100px"},  # Fixed
                                                ),
                                            ],
                                            className="mb-3",
                                            style={"maxWidth": "200px"},  # Constraint
                                        ),
                                        width=4,
                                    ),
                                ]
                            ),
                            dbc.Row(
                                [
                                    dbc.Col(
                                        dcc.DatePickerSingle(
                                            id="iv-start-date",
                                            placeholder="Start Date",
                                            className="mb-3",
                                            display_format="MMM Do, YY",
                                            style={"width": "100%"},
                                        ),
                                        width="auto",
                                    ),
                                    dbc.Col(
                                        dcc.DatePickerSingle(
                                            id="iv-end-date",
                                            placeholder="End Date",
                                            className="mb-3",
                                            display_format="MMM Do, YY",
                                            style={"width": "100%"},
                                        ),
                                        width="auto",
                                    ),
                                    dbc.Col(
                                        dbc.Button(
                                            html.I(className="fas fa-times-circle"),
                                            id="iv-reset-date-filters",
                                            color="danger",
                                            outline=True,
                                            className="mb-3",
                                            style={"margin-left": "10px"},
                                        ),
                                        width="auto",
                                        className="d-flex align-items-center",
                                    ),
                                    dbc.Col(
                                        dbc.Select(
                                            id="iv-sort-order",
                                            options=[
                                                {
                                                    "label": "Default (order by added)",
                                                    "value": "default",
                                                },
                                                {
                                                    "label": "Oldest First",
                                                    "value": "asc",
                                                },
                                                {
                                                    "label": "Newest First",
                                                    "value": "desc",
                                                },
                                            ],
                                            value="default",  # Default sorting
                                            className="dash-select-group",
                                            style={
                                                "width": "200px",
                                                "margin-left": "100px",
                                            },
                                        ),
                                        width="auto",
                                        className="d-flex align-items-center",
                                    ),
                                ],
                                justify="start",
                                className="g-2",
                            ),
                            dbc.Row(
                                [
                                    dbc.Col(
                                        dbc.Button(
                                            "Refresh",
                                            id="refresh-income-btn",
                                            color="primary",
                                            className="mb-3",
                                        ),
                                        width=12,
                                    )
                                ]
                            ),
                            html.Div(id="iv-income-list", className="mt-3"),
                        ],
                        title="Income viewer",
                        item_id="income_viewer",
                    ),
                    # -- TRANSACTION VIEWER
                    dbc.AccordionItem(
                        [
                            dbc.Row(
                                [
                                    dbc.Col(
                                        dbc.Input(
                                            id="tv-search",
                                            placeholder="Search transactions...",
                                            type="text",
                                            className="mb-3",
                                        ),
                                        width=4,
                                    ),
                                    dbc.Col(
                                        dcc.Dropdown(
                                            id="tv-category-filter",
                                            placeholder="Filter by category",
                                            className="mb-3",
                                            multi=True,
                                        ),
                                        width=4,
                                    ),
                                    dbc.Col(
                                        dbc.InputGroup(
                                            [
                                                dbc.InputGroupText("Limit:"),
                                                dbc.Input(
                                                    id="num-trans-limit",
                                                    type="number",
                                                    value=40,
                                                    min=1,
                                                    step=1,
                                                    style={"width": "100px"},  # Fixed
                                                ),
                                            ],
                                            className="mb-3",
                                            style={"maxWidth": "200px"},  # Constraint
                                        ),
                                        width=4,
                                    ),
                                ]
                            ),
                            dbc.Row(
                                [
                                    dbc.Col(
                                        dcc.DatePickerSingle(
                                            id="tv-start-date",
                                            placeholder="Start Date",
                                            className="mb-3",
                                            display_format="MMM Do, YY",
                                            style={"width": "100%"},
                                        ),
                                        width="auto",
                                    ),
                                    dbc.Col(
                                        dcc.DatePickerSingle(
                                            id="tv-end-date",
                                            placeholder="End Date",
                                            className="mb-3",
                                            display_format="MMM Do, YY",
                                            style={"width": "100%"},
                                        ),
                                        width="auto",
                                    ),
                                    dbc.Col(
                                        dbc.Button(
                                            html.I(className="fas fa-times-circle"),
                                            id="tv-reset-date-filters",
                                            color="danger",
                                            outline=True,
                                            className="mb-3",
                                            style={"margin-left": "10px"},
                                        ),
                                        width="auto",
                                        className="d-flex align-items-center",
                                    ),
                                    dbc.Col(
                                        dbc.Checklist(
                                            id="tv-recurring-filter",
                                            options=[
                                                {
                                                    "label": "Subscriptions only",
                                                    "value": "enable",
                                                }
                                            ],
                                            value=[],  # Disabled by default
                                            switch=True,
                                            className="dash-checklist-group",
                                            style={"margin-left": "100px"},
                                        ),
                                        width="auto",
                                        className="d-flex align-items-center",
                                    ),
                                    dbc.Col(
                                        dbc.Select(
                                            id="tv-sort-order",
                                            options=[
                                                {
                                                    "label": "Default (order by added)",
                                                    "value": "default",
                                                },
                                                {
                                                    "label": "Oldest First",
                                                    "value": "asc",
                                                },
                                                {
                                                    "label": "Newest First",
                                                    "value": "desc",
                                                },
                                            ],
                                            value="default",  # Default sorting
                                            className="dash-select-group",
                                            style={
                                                "width": "200px",
                                                "margin-left": "100px",
                                            },
                                        ),
                                        width="auto",
                                        className="d-flex align-items-center",
                                    ),
                                ],
                                justify="start",
                                className="g-2",
                            ),
                            dbc.Row(
                                [
                                    dbc.Col(
                                        dbc.Button(
                                            "Refresh",
                                            id="refresh-transactions-btn",
                                            color="primary",
                                            className="mb-3",
                                        ),
                                        width=12,
                                    )
                                ]
                            ),
                            html.Div(id="transactions-list", className="mt-3"),
                        ],
                        title="Transaction viewer",
                        item_id="transaction_viewer",
                    ),
                    # -- NET WORTH MANAGER --
                    dbc.AccordionItem(
                        [
                            dbc.Tabs(
                                [
                                    # Assets Tab
                                    dbc.Tab(
                                        dbc.Card(
                                            dbc.CardBody(
                                                [
                                                    dbc.Form(
                                                        [
                                                            dbc.Row(
                                                                [
                                                                    dbc.Col(
                                                                        dbc.Input(
                                                                            id="nw-asset-name",
                                                                            placeholder="Asset name",
                                                                            type="text",
                                                                            className="mb-3",
                                                                        ),
                                                                        width=12,
                                                                    )
                                                                ]
                                                            ),
                                                            dbc.Row(
                                                                [
                                                                    dbc.Col(
                                                                        dbc.Input(
                                                                            id="nw-asset-amount",
                                                                            placeholder="Amount ($)",
                                                                            type="number",
                                                                            min=0,
                                                                            step=0.01,
                                                                            className="mb-3",
                                                                        ),
                                                                        width=6,
                                                                    ),
                                                                    dbc.Col(
                                                                        dbc.Select(
                                                                            id="nw-asset-type",
                                                                            options=[
                                                                                {
                                                                                    "label": "Cash",
                                                                                    "value": "cash",
                                                                                },
                                                                                {
                                                                                    "label": "Investments",
                                                                                    "value": "investments",
                                                                                },
                                                                                {
                                                                                    "label": "Real Estate",
                                                                                    "value": "real estate",
                                                                                },
                                                                                {
                                                                                    "label": "Other Assets",
                                                                                    "value": "other",
                                                                                },
                                                                            ],
                                                                            value="cash",
                                                                            className="mb-3",
                                                                        ),
                                                                        width=6,
                                                                    ),
                                                                ]
                                                            ),
                                                            dbc.Row(
                                                                [
                                                                    dbc.Col(
                                                                        dbc.Input(
                                                                            id="nw-asset-note",
                                                                            placeholder="Note (optional)",
                                                                            type="text",
                                                                            className="mb-3",
                                                                        ),
                                                                        width=12,
                                                                    )
                                                                ]
                                                            ),
                                                            dbc.Row(
                                                                [
                                                                    dbc.Col(
                                                                        dbc.Button(
                                                                            "Add Asset",
                                                                            id="add-asset-btn",
                                                                            color="primary",
                                                                            className="me-2",
                                                                        ),
                                                                        width="auto",
                                                                    ),
                                                                    dbc.Col(
                                                                        dbc.Button(
                                                                            "Clear All Assets",
                                                                            id="clear-assets-btn",
                                                                            color="secondary",
                                                                            outline=True,
                                                                            className="me-2",
                                                                        ),
                                                                        width="auto",
                                                                    ),
                                                                ],
                                                                justify="start",
                                                                className="mb-4",
                                                            ),
                                                            # Added Assets List
                                                            html.Div(
                                                                id="added-assets-list",
                                                                className="mb-4",
                                                            ),
                                                            # Summary
                                                            dbc.Card(
                                                                [
                                                                    html.H5(
                                                                        "Assets Summary",
                                                                        className="card-title",
                                                                    ),
                                                                    html.Div(
                                                                        id="assets-summary"
                                                                    ),
                                                                ],
                                                                className="mb-4",
                                                            ),
                                                        ]
                                                    )
                                                ]
                                            )
                                        ),
                                        label="Assets",
                                        tab_id="assets-tab",
                                    ),
                                    # Liabilities Tab
                                    dbc.Tab(
                                        dbc.Card(
                                            dbc.CardBody(
                                                [
                                                    dbc.Form(
                                                        [
                                                            dbc.Row(
                                                                [
                                                                    dbc.Col(
                                                                        dbc.Input(
                                                                            id="nw-liability-name",
                                                                            placeholder="Liability name",
                                                                            type="text",
                                                                            className="mb-3",
                                                                        ),
                                                                        width=12,
                                                                    )
                                                                ]
                                                            ),
                                                            dbc.Row(
                                                                [
                                                                    dbc.Col(
                                                                        dbc.Input(
                                                                            id="nw-liability-amount",
                                                                            placeholder="Amount ($)",
                                                                            type="number",
                                                                            min=0,
                                                                            step=0.01,
                                                                            className="mb-3",
                                                                        ),
                                                                        width=6,
                                                                    ),
                                                                    dbc.Col(
                                                                        dbc.Select(
                                                                            id="nw-liability-type",
                                                                            options=[
                                                                                {
                                                                                    "label": "Credit Card",
                                                                                    "value": "credit card",
                                                                                },
                                                                                {
                                                                                    "label": "Loan",
                                                                                    "value": "loan",
                                                                                },
                                                                                {
                                                                                    "label": "Mortgage",
                                                                                    "value": "mortgage",
                                                                                },
                                                                                {
                                                                                    "label": "Other Liabilities",
                                                                                    "value": "other",
                                                                                },
                                                                            ],
                                                                            value="credit card",
                                                                            className="mb-3",
                                                                        ),
                                                                        width=6,
                                                                    ),
                                                                ]
                                                            ),
                                                            dbc.Row(
                                                                [
                                                                    dbc.Col(
                                                                        dbc.Input(
                                                                            id="nw-liability-note",
                                                                            placeholder="Note (optional)",
                                                                            type="text",
                                                                            className="mb-3",
                                                                        ),
                                                                        width=12,
                                                                    )
                                                                ]
                                                            ),
                                                            dbc.Row(
                                                                [
                                                                    dbc.Col(
                                                                        dbc.Button(
                                                                            "Add liability",
                                                                            id="add-liability-btn",
                                                                            color="primary",
                                                                            className="me-2",
                                                                        ),
                                                                        width="auto",
                                                                    ),
                                                                    dbc.Col(
                                                                        dbc.Button(
                                                                            "Clear All liabilites",
                                                                            id="clear-liabilities-btn",
                                                                            color="secondary",
                                                                            outline=True,
                                                                            className="me-2",
                                                                        ),
                                                                        width="auto",
                                                                    ),
                                                                ],
                                                                justify="start",
                                                                className="mb-4",
                                                            ),
                                                            # Added liabilities List
                                                            html.Div(
                                                                id="added-liabilities-list",
                                                                className="mb-4",
                                                            ),
                                                            # Summary
                                                            dbc.Card(
                                                                [
                                                                    html.H5(
                                                                        "Liabilities Summary",
                                                                        className="card-title",
                                                                    ),
                                                                    html.Div(
                                                                        id="liabilities-summary"
                                                                    ),
                                                                ],
                                                                className="mb-4",
                                                            ),
                                                        ]
                                                    )
                                                ]
                                            )
                                        ),
                                        label="Liabilities",
                                        tab_id="liabilities-tab",
                                    ),
                                    # Review Tab
                                    dbc.Tab(
                                        dbc.Card(
                                            dbc.CardBody(
                                                [
                                                    html.H4(
                                                        "Net Worth Summary",
                                                        className="mb-4",
                                                    ),
                                                    dbc.Row(
                                                        [
                                                            dbc.Col(
                                                                dbc.Card(
                                                                    [
                                                                        html.H5(
                                                                            "Total Assets",
                                                                            className="card-title",
                                                                        ),
                                                                        html.H3(
                                                                            id="total-assets-display",
                                                                            children="$0.00",
                                                                            className="text-success",
                                                                        ),
                                                                    ],
                                                                    className="text-center p-3",
                                                                ),
                                                                width=6,
                                                            ),
                                                            dbc.Col(
                                                                dbc.Card(
                                                                    [
                                                                        html.H5(
                                                                            "Total Liabilities",
                                                                            className="card-title",
                                                                        ),
                                                                        html.H3(
                                                                            id="total-liabilities-display",
                                                                            children="$0.00",
                                                                            className="text-danger",
                                                                        ),
                                                                    ],
                                                                    className="text-center p-3",
                                                                ),
                                                                width=6,
                                                            ),
                                                        ],
                                                        className="mb-4",
                                                    ),
                                                    dbc.Card(
                                                        [
                                                            html.H5(
                                                                "Net Worth",
                                                                className="card-title",
                                                            ),
                                                            html.H3(
                                                                id="net-worth-display",
                                                                children="$0.00",
                                                                className="text-primary",
                                                            ),
                                                        ],
                                                        className="text-center p-3 mb-4",
                                                    ),
                                                    dbc.Input(
                                                        id="nw-snapshot-note",
                                                        placeholder="Add a note about this snapshot (optional)",
                                                        type="text",
                                                        className="mb-3",
                                                    ),
                                                    dbc.Button(
                                                        "Save Net Worth Snapshot",
                                                        id="save-networth-btn",
                                                        color="primary",
                                                        size="lg",
                                                        className="w-100",
                                                    ),
                                                    dbc.Alert(
                                                        "Snapshot saved successfully!",
                                                        id="save-success-alert",
                                                        color="success",
                                                        dismissable=True,
                                                        is_open=False,
                                                        className="mt-3",
                                                    ),
                                                ]
                                            )
                                        ),
                                        label="Review & Save",
                                        tab_id="review-tab",
                                    ),
                                ]
                            ),
                            # Hidden storage for the data
                            dcc.Store(id="stored-assets", data=[]),
                            dcc.Store(id="stored-liabilities", data=[]),
                            dcc.Store(id="net-worth-data"),
                        ],
                        title="Net Worth Manager",
                        item_id="nw-manager",
                    ),
                    # -- IMPORT CSV FILE --
                    # -- CSV IMPORT --
                    dbc.AccordionItem(
                        [
                            dbc.Form(
                                [
                                    dcc.Upload(
                                        id="upload-transactions",
                                        children=html.Div(
                                            [
                                                "Drag and Drop or ",
                                                html.A("Select CSV File"),
                                            ]
                                        ),
                                        style={
                                            "width": "100%",
                                            "height": "60px",
                                            "lineHeight": "60px",
                                            "borderWidth": "1px",
                                            "borderStyle": "dashed",
                                            "borderRadius": "5px",
                                            "textAlign": "center",
                                            "marginBottom": "20px",
                                        },
                                        multiple=False,
                                    ),
                                    dbc.Row(
                                        [
                                            dbc.Col(
                                                dbc.Button(
                                                    "Import Transactions",
                                                    id="import-csv-btn",
                                                    color="primary",
                                                    className="w-100",
                                                ),
                                                width=12,
                                            )
                                        ]
                                    ),
                                    html.Div(id="csv-import-output", className="mt-3"),
                                    dcc.Interval(
                                        id="csv-reset-interval",
                                        interval=2000,
                                        n_intervals=0,
                                        disabled=True,
                                    ),
                                ]
                            )
                        ],
                        title="Import CSV",
                    ),
                    # # -- CODE INJECTOR --
                    # dbc.AccordionItem(
                    #     [
                    #         dbc.Form([
                    #             dbc.Row([
                    #                 dbc.Col(
                    #                     dcc.Textarea(
                    #                         id="code-input",
                    #                         placeholder="Enter Python or SQL code here...",
                    #                         style={'height': '200px', 'width': '100%'},
                    #                         className="mb-3"
                    #                     ),
                    #                     width=12
                    #                 )
                    #             ]),
                    #             dbc.Row([
                    #                 dbc.Col(
                    #                     dbc.Button(
                    #                         "Execute Code (DANGER)",
                    #                         id="execute-code-btn",
                    #                         color="primary",
                    #                         className="w-100"
                    #                     ),
                    #                     width=12
                    #                 )
                    #             ]),
                    #             html.Div(id="code-output", className="mt-3"),
                    #             dcc.Interval(
                    #                 id="code-reset-interval",
                    #                 interval=2000,  # 2 seconds
                    #                 n_intervals=0,
                    #                 disabled=True
                    #             )
                    #         ])
                    #     ],
                    #     title="Code Executor"
                    # )
                ],
                active_item="transaction_manager",
                flush=True,
            ),
            dcc.Store(
                id="transaction-added", data=False
            ),  # Storage for custom event sent to script when transaction added
            dcc.Store(
                id="category-added", data=False
            ),  # Storage for custom event sent to script when category added
            dcc.Store(id="income-added", data=False),
            dcc.Store(id="checkbox-store"),
            html.Div(
                id="dummy-trans", style={"display": "none"}
            ),  # Dummy since dash always requires outputs for callbacks
            html.Div(
                id="dummy-cat", style={"display": "none"}
            ),  # Dummy since dash always requires outputs for callbacks
            html.Div(id="dummy-inc", style={"display": "none"}),
            # Transaction viewer modal
            dbc.Modal(
                [
                    dbc.ModalHeader("Edit Transaction"),
                    dbc.ModalBody(
                        [
                            dcc.Input(id="edit-trans-id", type="hidden"),
                            dbc.Input(
                                id="edit-trans-merchant",
                                placeholder="Merchant",
                                className="mb-2",
                            ),
                            dbc.Input(
                                id="edit-trans-amount",
                                type="number",
                                placeholder="Amount",
                                className="mb-2",
                            ),
                            dcc.DatePickerSingle(
                                id="edit-trans-date",
                                display_format="MMM Do, YY",
                                className="mb-2",
                            ),
                            dbc.Input(
                                id="edit-trans-note",
                                placeholder="Note",
                                className="mb-2",
                            ),
                            dbc.Checkbox(
                                id="edit-trans-recurring",
                                label="Recurring",
                                value=False,
                                className="mb-3",
                            ),
                            dbc.Select(
                                id="edit-trans-category", options=[], className="mb-2"
                            ),
                        ]
                    ),
                    dbc.ModalFooter(
                        [
                            dbc.Button(
                                "Save", id="edit-trans-submit-btn", color="primary"
                            ),
                            dbc.Button(
                                "Cancel", id="edit-trans-cancel-btn", color="secondary"
                            ),
                        ]
                    ),
                ],
                id="edit-transaction-modal",
                is_open=False,
            ),

            # Category viewer modal
            dbc.Modal(
                [
                    dbc.ModalHeader("Edit Category"),
                    dbc.ModalBody(
                        [
                            dcc.Input(id="edit-cat-id", type="hidden"),
                            dbc.Input(
                                id="edit-cat-name", placeholder="Name", className="mb-2"
                            ),
                            dbc.Input(
                                id="edit-cat-budget",
                                type="number",
                                placeholder="Budget",
                                className="mb-2",
                            ),
                        ]
                    ),
                    dbc.ModalFooter(
                        [
                            dbc.Button(
                                "Save", id="edit-cat-submit-btn", color="primary"
                            ),
                            dbc.Button(
                                "Cancel", id="edit-cat-cancel-btn", color="secondary"
                            ),
                        ]
                    ),
                ],
                id="edit-category-modal",
                is_open=False,
            ),
            # Income viewer modal
            dbc.Modal(
                [
                    dbc.ModalHeader("Edit Income"),
                    dbc.ModalBody(
                        [
                            dcc.Input(id="edit-income-id", type="hidden"),
                            dbc.Input(
                                id="edit-income-source",
                                placeholder="Income Source",
                                className="mb-2",
                            ),
                            dbc.Input(
                                id="edit-income-amount",
                                type="number",
                                placeholder="Amount",
                                className="mb-2",
                            ),
                            dcc.DatePickerSingle(
                                id="edit-income-date",
                                display_format="MMM Do, YY",
                                className="mb-2",
                            ),
                        ]
                    ),
                    dbc.ModalFooter(
                        [
                            dbc.Button(
                                "Save", id="edit-income-submit-btn", color="primary"
                            ),
                            dbc.Button(
                                "Cancel", id="edit-income-cancel-btn", color="secondary"
                            ),
                        ]
                    ),
                ],
                id="edit-income-modal",
                is_open=False,
            ),
        ],
        id="main-container-data-page",
        fluid=True,
        className="p-4",
    )

# --- BACKEND ---

# -- DATA PAGE CALLBACKS --
def data_page_callbacks(app):

    # Database
    from database import get_db
    db = get_db()

    # -- Populate layout --
    @app.callback(
        [Output("tm-category", "options"),
        Output("tv-category-filter", "options")],
        Input("url", "pathname")  # Using the URL as trigger for initial load
    )
    def populate_category_options(_):
        # Fetch categories from database when layout loads
        categories_data = db.get_categories(current_user.id)
        category_options = [{"label": name, "value": cat_id} for cat_id, name in categories_data]
        
        # Return the same options for both dropdowns
        return category_options, category_options

    # --- TRANSACTION ADDING CALLBACKS ---
    @app.callback(
        [
            Output("add-transaction-btn", "children", allow_duplicate=True),
            Output("add-transaction-btn", "style"),
            Output("tm-merchant", "value"),
            Output("tm-amount", "value"),
            Output("tm-note", "value"),
            Output("tm-date", "date"),
            Output("tm-recurring", "value"),
            Output("selected-tags-store", "data"),
            Output("transaction-added", "data"),
            Output("button-reset-interval", "disabled"),  # Interval reset output
        ],
        [
            Input("add-transaction-btn", "n_clicks"),
            Input("button-reset-interval", "n_intervals"),
        ],
        [
            State("tm-category", "value"),
            State("tm-merchant", "value"),
            State("tm-amount", "value"),
            State("tm-note", "value"),
            State("tm-date", "date"),
            State("tm-recurring", "value"),

            State("selected-tags-store", "data"),

            State("add-transaction-btn", "children"),
        ],
        prevent_initial_call=True,
    )
    @authenticate_callback
    def handle_transactions(n_clicks, n_intervals, category, merchant, amount, note, date, recurring, tags, current_text):
        ctx = callback_context
        
        if not ctx.triggered:
            raise PreventUpdate
            
        trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
        
        if trigger_id == "add-transaction-btn":
            try:
                
                # Handle bad input
                if not category:
                    return (
                        "Invalid category",
                        {
                            'backgroundColor': '#dc3545',  # Red background
                            'borderColor': '#dc3545',
                            'color': 'white'  # White text
                        },
                        no_update, no_update, no_update,
                        no_update, no_update, no_update, no_update, no_update
                    )
                    
                if not merchant:
                    return (
                        "Invalid merchant",
                        {
                            "backgroundColor": "#dc3545",  # Red background
                            "borderColor": "#dc3545",
                            "color": "white",  # White text
                        },
                        no_update,
                        no_update,
                        no_update,
                        no_update,
                        no_update,
                        no_update,
                        no_update,
                        no_update,
                    )
                    
                if not isinstance(amount, (int, float)) or amount < 0:
                    return (
                        "Invalid amount",
                        {
                            "backgroundColor": "#dc3545",  # Red background
                            "borderColor": "#dc3545",
                            "color": "white",  # White text
                        },
                        no_update,
                        no_update,
                        no_update,
                        no_update,
                        no_update,
                        no_update,
                        no_update,
                        no_update,
                    )
                
                # If all passed then add transaction
                with db._get_cursor() as cursor:
                    cursor.execute(
                        "INSERT INTO transactions VALUES (NULL, ?, ?, ?, ?, ?, ?, ?)",
                        (
                            category,
                            merchant,
                            amount,
                            date,
                            note,
                            int(recurring),
                            current_user.id,
                        ),
                    )

                    # Get the auto-generated ID
                    trans_id = cursor.lastrowid

                    # If recurring, add to recurringTransactions with the transaction_id
                    if int(recurring):
                        cursor.execute(
                            "INSERT INTO recurringTransactions VALUES (NULL, ?, ?, ?, ?, ?, ?, ?, ?)",
                            (
                                trans_id,
                                category,
                                merchant,
                                amount,
                                date,
                                note,
                                int(recurring),
                                current_user.id,
                            ),
                        )

                # If tags provided, insert into tags table
                if tags:
                    
                    for tag in tags:
                        db.add_tag_to_transaction(trans_id, tag["name"], tag["color"], current_user.id)
                
                return (
                    "Transaction Added!",
                    {
                        "backgroundColor": "#28a745",  # Green background
                        "borderColor": "#28a745",
                        "color": "white",  # White text
                    },  # Updated button text
                    "",
                    None,
                    "",
                    date,
                    False,
                    [],  # clear tags storage
                    True,  
                    False,  # Enable the interval
                )
                
            except Exception as e:
                return (
                    f"Error: {str(e)}",
                    {
                            'backgroundColor': '#dc3545',  # Red background
                            'borderColor': '#dc3545',
                            'color': 'white'  # White text
                    },
                    merchant, amount, date, note, recurring, tags, False, True  # Keep interval disabled
                )
        
        elif trigger_id == "button-reset-interval":
            if current_text == "Transaction Added!":
                return (
                    "Add Transaction",  
                    {
                        # 'backgroundColor': '#007bff',  # Default blue
                        # 'borderColor': '#007bff',
                        # 'color': 'white'  # White text
                    },
                    # Reset text
                    no_update, no_update, no_update,
                    no_update, no_update, no_update, no_update, True  # Disable the interval again
                )
        
        raise PreventUpdate

    # # Extra callback to sync frontend java update with backend for checkmark
    # @app.callback(
    #     Output("checkbox-store", "data"),
    #     Input("tm-recurring", "value"),
    #     State("tm-recurring", "id"),
    # )
    # def store_checkbox_value(value, _):
    #     return {"value": value}

    # --- TAG MANAGEMENT ON ADD CALLBACKS ---
    
    # -- Tag suggestions dynamic update --
    @app.callback(
        Output("tag-suggestions", "children"),
        Output("tag-suggestions-collapse", "is_open"),
        Input("tm-tag-input", "value"),
        prevent_initial_call=True,
    )
    @authenticate_callback
    def update_tag_suggestions(search_text):
        if not search_text:
            return [], False

        # Perform tag search every input tick
        with db._get_cursor() as cursor:
            
            cursor.execute(
                """
                SELECT DISTINCT tg.tag_name, tg.tag_color
                FROM tags tg
                JOIN transactions t ON tg.transaction_id = t.id
                WHERE t.user_id = ? AND LOWER(tg.tag_name) LIKE LOWER(?)
                GROUP BY tg.tag_name
                ORDER BY COUNT(*) DESC
                LIMIT 5
            """,
                (current_user.id, f"%{search_text}%"),
            )

            existing_tags = cursor.fetchall()


        if existing_tags:
            suggestions = []
            for tag_name, tag_color in existing_tags:
                suggestions.append(
                    dbc.Button(
                        [
                            dbc.Badge(
                                tag_name,
                                color=tag_color,
                            )
                        ],
                        id={
                            "type": "tag-suggestion",
                            "tag": tag_name,
                            "color": tag_color,
                        },
                        color="link",
                        className="text-start w-100 p-1",
                        size="sm",
                    )
                )
            return suggestions, True

        # If no relevant tag found, offer to add new tag
        return [
            html.Div(
                f'Press Enter to add "{search_text}" as new tag', className="text-muted p-2"
            )
        ], True

    # -- Adding tag from suggestions --
    @app.callback(
        Output("selected-tags-store", "data", allow_duplicate=True),
        Output("tm-tag-input", "value", allow_duplicate=True),
        Output("tag-suggestions-collapse", "is_open", allow_duplicate=True),
        Input({"type": "tag-suggestion", "tag": ALL, "color": ALL}, "n_clicks"),
        State("selected-tags-store", "data"),
        prevent_initial_call=True,
    )
    def select_tag_from_suggestion(n_clicks_list, current_tags):
        if not any(n_clicks_list):
            raise PreventUpdate

        ctx = callback_context
        if not ctx.triggered:
            raise PreventUpdate

        # Tag metadata from clicked
        clicked_id = eval(ctx.triggered[0]["prop_id"].split(".")[0])
        tag_name = clicked_id["tag"]
        tag_color = clicked_id["color"]

        if current_tags is None:
            current_tags = []

        # Check if tag already exists
        if not any(tag["name"] == tag_name for tag in current_tags):
            current_tags.append({"name": tag_name, "color": tag_color})

        return current_tags, "", False

    # -- Add new tag on Enter to frontend store --
    @app.callback(
        Output("selected-tags-store", "data", allow_duplicate=True),
        Output("tm-tag-input", "value", allow_duplicate=True),
        Input("tm-tag-input", "n_submit"),
        State("tm-tag-input", "value"),
        State("selected-tags-store", "data"),
        prevent_initial_call=True,
    )
    def add_tag_on_enter(n_submit, tag_input, current_tags):
        if not tag_input or not tag_input.strip():
            raise PreventUpdate

        if current_tags is None:
            current_tags = []

        tag_name = tag_input.strip()

        # Check if tag already exists
        if not any(tag["name"] == tag_name for tag in current_tags):
            
            # Random color
            import random

            colors = [
                "#FF6B6B",
                "#4ECDC4",
                "#45B7D1",
                "#96CEB4",
                "#FFEAA7",
                "#DDA0DD",
                "#98D8C8",
                "#F7DC6F",
            ]
            tag_color = random.choice(colors)
            current_tags.append({"name": tag_name, "color": tag_color})

        return current_tags, ""
    
    # -- Display selected tags as badges into container --
    @app.callback(
        Output("selected-tags-display", "children"),
        Input("selected-tags-store", "data"),
        prevent_initial_call=True,
    )
    def display_selected_tags(tags):
        if not tags:
            return []

        tag_badges = []
        for i, tag in enumerate(tags):
            
            tag_badges.append(
                dbc.Badge(
                    [
                        tag["name"],
                        dbc.Button(
                            "×",
                            id={"type": "remove-tag", "index": i},
                            color="link",
                            size="sm",
                            className="ms-1 p-0 text-white",
                            style={"border": "none", "background": "transparent"},
                        ),
                    ],
                    color=tag["color"],
                    className="me-1",
                    style={"cursor": "default"},
                )
            )

        return tag_badges

    # -- Remove tags from storage container --
    @app.callback(
        Output("selected-tags-store", "data", allow_duplicate=True),
        Input({"type": "remove-tag", "index": ALL}, "n_clicks"),
        State("selected-tags-store", "data"),
        prevent_initial_call=True
    )
    def remove_tag(n_clicks_list, current_tags):
        if not any(n_clicks_list):
            raise PreventUpdate
        
        ctx = callback_context
        if not ctx.triggered:
            raise PreventUpdate
        
        # Extract the index of the tag to remove
        clicked_id = eval(ctx.triggered[0]['prop_id'].split('.')[0])
        index_to_remove = clicked_id['index']
        
        if current_tags and 0 <= index_to_remove < len(current_tags):
            current_tags.pop(index_to_remove)
        
        return current_tags

    # --------------------------------------------------------------------------------------

    # CHANGE DATE TRANSACTION
    @app.callback(
        Output("tm-date", "date", allow_duplicate=True),
        Input("tm-date-increment", "n_clicks"),
        Input("tm-date-decrement", "n_clicks"),
        State("tm-date", "date"),
        prevent_initial_call=True
    )
    @authenticate_callback
    def update_date_from_arrows(increment_clicks, decrement_clicks, current_date):
        """Callback to handle date increment/decrement from arrow buttons"""
        ctx = callback_context
        
        if not ctx.triggered:
            return no_update
        
        # Get which button was clicked
        button_id = ctx.triggered[0]["prop_id"].split(".")[0]
        
        # Parse current date
        current_date = datetime.strptime(current_date[:10], "%Y-%m-%d").date()
        
        # Calculate new date
        if button_id == "tm-date-increment":
            new_date = current_date + timedelta(days=1)
        elif button_id == "tm-date-decrement":
            new_date = current_date - timedelta(days=1)
        else:
            return no_update
        
        return new_date
    
    # -- ADD CATEGORY --
    @app.callback(
    [
        Output("add-category-btn", "children", allow_duplicate=True),
        Output("add-category-btn", "style"),
        
        Output("cm-category", "value"),
        Output("cm-budget", "value"),
   
        Output("button-reset-interval-cat", "disabled"),  # Interval reset output
        
        Output("category-added", "data")
    ],
    [
        Input("add-category-btn", "n_clicks"),
        Input("button-reset-interval-cat", "n_intervals"),
    ],
    [
        State("cm-category", "value"),
        State("cm-budget", "value"),

        State("add-category-btn", "children"),
    ],
    prevent_initial_call=True
    )
    @authenticate_callback
    def handle_category_add(n_clicks, n_intervals, category, budget, current_text):
        ctx = callback_context
        
        if not ctx.triggered:
            raise PreventUpdate
            
        trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
        
        if trigger_id == "add-category-btn":
            try:
                
                # Handle bad input
                if not category:
                    return (
                        "Invalid category",
                        {
                            'backgroundColor': '#dc3545',  # Red background
                            'borderColor': '#dc3545',
                            'color': 'white'  # White text
                        },
                        no_update, no_update, no_update, no_update
                    )
                
                if not isinstance(budget, (int, float)) or budget < 0:
                    
                    if budget is not None:
                        return (
                            "Invalid budget",
                            {
                                'backgroundColor': '#dc3545',  # Red background
                                'borderColor': '#dc3545',
                                'color': 'white'  # White text
                            },
                            no_update, no_update, no_update, no_update
                        )
                
                # If all passed then add transaction
                with db._get_cursor() as cursor:
                    cursor.execute(
                        "INSERT INTO categories VALUES (NULL, ?, ?, ?)",
                        (category, budget, current_user.id),
                    )
                
                return (
                    "Category Added!",  
                    {
                        'backgroundColor': '#28a745',  # Green background
                        'borderColor': '#28a745',
                        'color': 'white'  # White text
                    }, # Updated button text
                    "", None, False, True
                )
                
            except Exception as e:
                return (
                    f"Error: {str(e)}",
                    {
                            'backgroundColor': '#dc3545',  # Red background
                            'borderColor': '#dc3545',
                            'color': 'white'  # White text
                    },
                    category, budget, no_update, no_update  # Keep interval disabled
                )
        
        elif trigger_id == "button-reset-interval-cat":
            if current_text == "Category Added!":
                return (
                    "Add Category",  
                    {

                    },
                    # Reset text
                    no_update, no_update, no_update, no_update
                )
        
        raise PreventUpdate
    
    # --- ADD INCOME ---
    @app.callback(
    [
        Output("add-income-btn", "children", allow_duplicate=True),
        Output("add-income-btn", "style"),
        
        Output("im-source", "value"),
        Output("im-amount", "value"),
        Output("im-date", "date"),

        Output("income-added", "data"),
        Output("button-reset-interval-inc", "disabled"),  # Interval reset output
    ],
    [
        Input("add-income-btn", "n_clicks"),
        Input("button-reset-interval-inc", "n_intervals"),
    ],
    [
        State("im-source", "value"),
        State("im-amount", "value"),
        State("im-date", "date"),
        State("add-income-btn", "children"),
    ],
    prevent_initial_call=True
    )
    @authenticate_callback
    def handle_income_add(n_clicks, n_intervals, source, amount, date, current_text):
        ctx = callback_context
        
        if not ctx.triggered:
            raise PreventUpdate
            
        trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
        
        if trigger_id == "add-income-btn":
            try:
                
                # Handle bad input
                if not source:
                    return (
                        "Invalid source",
                        {
                            'backgroundColor': '#dc3545',  # Red background
                            'borderColor': '#dc3545',
                            'color': 'white'  # White text
                        },
                        no_update, no_update, no_update,
                        no_update, no_update
                    )
                    
                if not isinstance(amount, (int, float)) or amount < 0:
                    return (
                        "Invalid amount",
                        {
                            'backgroundColor': '#dc3545',  # Red background
                            'borderColor': '#dc3545',
                            'color': 'white'  # White text
                        },
                        no_update, no_update, no_update,
                        no_update, no_update
                    )
                
                # If all passed then add transaction
                with db._get_cursor() as cursor:
                    cursor.execute(
                        "INSERT INTO income VALUES (NULL, ?, ?, ?, ?)",
                        (source, amount, date, current_user.id),
                    )
                
                return (
                    "Income Added!",  
                    {
                        'backgroundColor': '#28a745',  # Green background
                        'borderColor': '#28a745',
                        'color': 'white'  # White text
                    }, # Updated button text
                    "", None, date, True, False  # Enable the interval
                )
                
            except Exception as e:
                return (
                    f"Error: {str(e)}",
                    {
                            'backgroundColor': '#dc3545',  # Red background
                            'borderColor': '#dc3545',
                            'color': 'white'  # White text
                    },
                    source, amount, date, False, True  # Keep interval disabled
                )
        
        elif trigger_id == "button-reset-interval-inc":
            if current_text == "Income Added!":
                return (
                    "Add income",  
                    {

                    },
                    # Reset text
                    no_update, no_update, no_update,
                    no_update, no_update
                )
        
        raise PreventUpdate
    
    # CHANGE DATE INCOME
    @app.callback(
        Output("im-date", "date", allow_duplicate=True),
        Input("im-date-increment", "n_clicks"),
        Input("im-date-decrement", "n_clicks"),
        State("im-date", "date"),
        prevent_initial_call=True
    )
    @authenticate_callback
    def update_date_from_arrows(increment_clicks, decrement_clicks, current_date):
        """Callback to handle date increment/decrement from arrow buttons"""
        ctx = callback_context
        
        if not ctx.triggered:
            return no_update
        
        # Get which button was clicked
        button_id = ctx.triggered[0]["prop_id"].split(".")[0]
        
        # Parse current date
        current_date = datetime.strptime(current_date[:10], "%Y-%m-%d").date()
        
        # Calculate new date
        if button_id == "im-date-increment":
            new_date = current_date + timedelta(days=1)
        elif button_id == "im-date-decrement":
            new_date = current_date - timedelta(days=1)
        else:
            return no_update
        
        return new_date

    
    # -- Listener to put focus back on merchant once transaction added --
    app.clientside_callback(
        """
        function(trigger) {
            if (trigger) {
                const merchantInput = document.getElementById("tm-merchant");
                if (merchantInput) {
                    merchantInput.focus();
                }
            }
            return "";
        }
        """,
        Output("dummy-trans", "children"),  # dummy output
        Input("transaction-added", "data"),
    )
    
    # Focus on category
    # app.clientside_callback(
    #     """
    #     function(trigger) {
    #         if (trigger) {
    #             const categoryInput = document.getElementById("cm-category");
    #             if (categoryInput) {
    #                 categoryInput.focus();
    #             }
    #         }
    #         return "";
    #     }
    #     """,  
    #     Output("dummy-cat", "children"),  # dummy output
    #     Input("category-added", "data")
    # )
# -------------------------------------------------------------------------


# -- TRANSACTION VIEWER --
    @app.callback(
        Output("transactions-list", "children"),
        Input("refresh-transactions-btn", "n_clicks"),
        Input("transaction-added", "data"),
        Input("category-added", "data"),
        Input("num-trans-limit", "value"),
        State("tv-search", "value"),
        State("tv-category-filter", "value"),
        State("tv-start-date", "date"),
        State("tv-end-date", "date"),
        Input("tv-recurring-filter", "value"),
        Input("tv-sort-order", "value"),
        prevent_initial_call = True
    )
    @authenticate_callback
    def update_transactions_list(n_clicks, trans_added, cat_added, num_trans_limit, search_term, category_filter, start_date, end_date, recurring_filter, sort_order):
        
        if num_trans_limit is None:
            num_trans_limit = 40 # default
        
        # Fetch recent transactions
        tags_filter = None  # No tag filtering for now
        transactions = db.fetch_recent_transactions(search_term, category_filter, start_date, end_date, recurring_filter, tags_filter, num_trans_limit, sort_order, current_user.id)
        
        if not transactions:
            return dbc.Alert("No transactions found", color="info")
        
        # Create transaction cards
        transaction_cards = []
        for transaction in transactions:

            trans_id, category, merchant, amount, date, note, recurring = transaction

            card = dbc.Card(
                [
                    dbc.CardHeader(
                        html.Div([
                            html.Span(f"{category}", className="text-muted"),
                            html.Span(f"${amount:.2f}", className="ms-auto fw-bold"),
                        ], className="d-flex"),
                        className="py-2"
                    ),
                    dbc.CardBody(
                        [
                            html.H5(merchant, className="card-title"),
                            html.P(note, className="card-text") if note else None,
                            html.P(f"Date: {date}", className="card-text text-muted small"),
                            html.P("Recurring", className="badge bg-info") if recurring else None,
                        ]
                    ),
                    dbc.CardFooter(
                        dbc.Row([
                            dbc.Col(
                                dbc.Button("Edit", id={"type": "edit-trans-btn", "index": trans_id}, 
                                        color="primary", size="sm", className="me-2"),
                                width="auto"
                            ),
                            dbc.Col(
                                dbc.Button("Delete", id={"type": "delete-trans-btn", "index": trans_id}, 
                                        color="danger", size="sm"),
                                width="auto"
                            ),
                            dbc.Col(
                                dbc.Button("End", id={"type": "end-trans-btn", "index": trans_id}, 
                                        color="warning", size="sm"),
                                width="auto"
                            ) if recurring else None
                        ], justify="end"),
                        className="py-2"
                    )
                ],
                className="mb-3"
            )
            transaction_cards.append(card)
        
        return transaction_cards
    
    # Callback to reset date filter
    @app.callback(
        Output("tv-start-date", "date"),
        Output("tv-end-date", "date"),
        Input("tv-reset-date-filters", "n_clicks"),
        prevent_initial_call=True
    )
    @authenticate_callback
    def reset_date_filters(n_clicks):
        if n_clicks:
            return None, None  
        return no_update, no_update

    # Callback for delete transaction
    @app.callback(
        Output("refresh-transactions-btn", "n_clicks"),
        Output("refresh-transactions-btn", "children"),
        Output("refresh-transactions-btn", "style"),
        Input({"type": "delete-trans-btn", "index": ALL}, "n_clicks"),
        State({"type": "delete-trans-btn", "index": ALL}, "id"),
        prevent_initial_call=True
    )
    @authenticate_callback
    def delete_transaction(delete_clicks, delete_ids):
        ctx = callback_context
        if not ctx.triggered:
            raise PreventUpdate
        
        trans_id = None
        for index, value in enumerate(delete_clicks):
            
            if value:
                trans_id = delete_ids[index]['index']
                break
            
        if trans_id is None:
            raise PreventUpdate

        # Delete the transaction
        try:

            with db._get_cursor() as cursor:

                cursor.execute("DELETE FROM recurringTransactions WHERE trans_id = ? AND user_id = ?", (trans_id, current_user.id)) # if exists, delete from recurringTransactions
                cursor.execute("DELETE FROM transactions WHERE id = ? AND user_id = ?", (trans_id, current_user.id))
            
            # Return None to trigger the refresh via the other callback
            return None, no_update, no_update
        
        except Exception as e:
                return no_update, ["ERROR: ", str(e)], {
                            'backgroundColor': '#dc3545',  # Red background
                            'borderColor': '#dc3545',
                            'color': 'white'  # White text
                        }
                
    # Callback to end a recurring transaction
    @app.callback(
        Output("refresh-transactions-btn", "n_clicks", allow_duplicate=True),
        Output("refresh-transactions-btn", "children", allow_duplicate=True),
        Output("refresh-transactions-btn", "style", allow_duplicate=True),
        Input({"type": "end-trans-btn", "index": ALL}, "n_clicks"),
        State({"type": "end-trans-btn", "index": ALL}, "id"),
        prevent_initial_call=True
    )
    @authenticate_callback
    def end_recurring_transaction(end_clicks, end_ids):
        ctx = callback_context
        if not ctx.triggered:
            raise PreventUpdate
            
        trans_id = None
        for index, value in enumerate(end_clicks):
            if value:
                trans_id = end_ids[index]['index']
                break
                
        if trans_id is None:
            raise PreventUpdate

        try:
            with db._get_cursor() as cursor:
            
                # First get the recurring transaction details
                cursor.execute(
                    """
                    SELECT category_id, merchant, amount, date, note 
                    FROM recurringTransactions 
                    WHERE trans_id = ? AND user_id = ?
                """,
                    (trans_id, current_user.id),
                )
                recurring_data = cursor.fetchone()
            
                if not recurring_data:
                    return no_update, ["ERROR: ", "no recurring data"], {
                        'backgroundColor': '#dc3545',  # Red background
                        'borderColor': '#dc3545',
                        'color': 'white'  # White text
                    }
                
                category, merchant, amount, start_date, note = recurring_data
                
            with db._get_cursor() as cursor:
                # Delete the original transaction and its recurring version
                cursor.execute("DELETE FROM recurringTransactions WHERE trans_id = ? AND user_id = ?", (trans_id, current_user.id))
                cursor.execute("DELETE FROM transactions WHERE id = ? AND user_id = ?", (trans_id, current_user.id))
                
            # Generate monthly transactions from start date to today
            current_date = datetime.now().date()
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date() if isinstance(start_date, str) else start_date
            
            # Calculate all months between start date and today
            dates = []
            current = start_date

            while current <= current_date:
                dates.append(current)
                # Move to next month (handles year rollover)
                if current.month == 12:
                    current = current.replace(year=current.year + 1, month=1)
                else:
                    current = current.replace(month=current.month + 1)
            
            # Insert transactions for each month
            if note:
                insert_note = note + " (ended)"
            else:
                insert_note = "(ended)"

            with db._get_cursor() as cursor:
                for date in dates:
                    cursor.execute(
                        "INSERT INTO transactions VALUES (NULL, ?, ?, ?, ?, ?, ?, ?)",
                        (category, merchant, amount, date.strftime('%Y-%m-%d'), insert_note, 0, current_user.id)
                    )
            
            # Return None to trigger the refresh via the other callback
            return None, no_update, no_update
            
        except Exception as e:
            return no_update, ["ERROR: ", str(e)], {
                'backgroundColor': '#dc3545',  # Red background
                'borderColor': '#dc3545',
                'color': 'white'  # White text
            }
                
    
# Callback to open edit transaction modal
    @app.callback(
        Output("edit-transaction-modal", "is_open"),
        Output("edit-trans-id", "value"),
        Output("edit-trans-merchant", "value"),
        Output("edit-trans-amount", "value"),
        Output("edit-trans-date", "date"),
        Output("edit-trans-note", "value"),
        Output("edit-trans-recurring", "value"),
        Output("edit-trans-category", "value"),
        Output("edit-trans-category", "options"), 
        Output({"type": "edit-trans-btn", "index": ALL}, "n_clicks"), # Reset clicks so they dont stack
        Input({"type": "edit-trans-btn", "index": ALL}, "n_clicks"),
        State({"type": "edit-trans-btn", "index": ALL}, "id"),
        prevent_initial_call=True
    )
    @authenticate_callback
    def open_edit_transaction_modal(edit_clicks, edit_ids):
        ctx = callback_context
        if not ctx.triggered:
            raise PreventUpdate
        
        trans_id = None
        for index, value in enumerate(edit_clicks):
            if value:
                trans_id = edit_ids[index]['index']
                break
        
        if trans_id is None:
            raise PreventUpdate
        
        # Reset all button clicks
        reset_clicks = [None] * len(edit_clicks)

        # Fetch the transaction data
        try:
            # Get categories to update selector
            with db._get_cursor() as cursor:
                cursor.execute("SELECT name FROM categories WHERE user_id = ?", (current_user.id,))
                categories = cursor.fetchall()
            category_options = [{'label': cat[0], 'value': cat[0]} for cat in categories]
            
            with db._get_cursor() as cursor:
                cursor.execute("""
                    SELECT t.id, t.merchant, t.amount, t.date, t.note, t.recurring, c.name 
                    FROM transactions t
                    JOIN categories c ON t.category_id = c.id
                    WHERE t.id = ? AND t.user_id = ?
                """, (trans_id, current_user.id))
                transaction = cursor.fetchone()
            
            if transaction:
                return (
                    True,  # Open modal
                    transaction[0],  # id
                    transaction[1],  # merchant
                    transaction[2],  # amount
                    transaction[3],  # date
                    transaction[4],  # note
                    transaction[5],  # recurring
                    transaction[6],   # category name
                    category_options,
                    reset_clicks
                )
            else:
                raise Exception("Transaction not found")
                
        except Exception as e:
            print(f"Error fetching transaction: {e}")
            raise PreventUpdate
        
    # Cancel click
    @app.callback(
        Output("edit-transaction-modal", "is_open", allow_duplicate=True),
        Input("edit-trans-cancel-btn", "n_clicks"),
        prevent_initial_call=True
    )
    @authenticate_callback
    def close_edit_modal(cancel_click):
        if cancel_click:
            return False
        raise PreventUpdate
    
    # Save change click
    @app.callback(
        Output("refresh-transactions-btn", "n_clicks", allow_duplicate=True),
        Output("edit-transaction-modal", "is_open", allow_duplicate=True),
        Output("edit-trans-submit-btn", "children", allow_duplicate=True),
        Output("edit-trans-submit-btn", "style", allow_duplicate=True),
        Input("edit-trans-submit-btn", "n_clicks"),
        State("edit-trans-id", "value"),
        State("edit-trans-merchant", "value"),
        State("edit-trans-amount", "value"),
        State("edit-trans-date", "date"),
        State("edit-trans-note", "value"),
        State("edit-trans-recurring", "value"),
        State("edit-trans-category", "value"),
        prevent_initial_call=True
    )
    @authenticate_callback
    def update_transaction(submit_click, trans_id, merchant, amount, date, note, recurring, category_name):
        if not submit_click:
            raise PreventUpdate
        
        try:
            
            default_style = {

            }
            
            if not merchant:
                    return (no_update, no_update, 
                        "Invalid merchant", 
                        {
                            'backgroundColor': '#dc3545',  # Red background
                            'borderColor': '#dc3545',
                            'color': 'white'  # White text
                        }
                    )
                
            if not isinstance(amount, (int, float)) or amount < 0:
                return (no_update, no_update, 
                        "Invalid amount", 
                        {
                            'backgroundColor': '#dc3545',  # Red background
                            'borderColor': '#dc3545',
                            'color': 'white'  # White text
                        }
                    )
                
            with db._get_cursor() as cursor:
            
                # Get cat id
                cursor.execute("SELECT id FROM categories WHERE name = ?", (category_name,))
                category_id = cursor.fetchone()[0]
                
                # Update the transaction
                # First update main transaction
                cursor.execute("""
                    UPDATE transactions 
                    SET merchant = ?, amount = ?, date = ?, note = ?, recurring = ?, category_id = ?
                    WHERE id = ? AND user_id = ?
                """, (merchant, amount, date, note, int(recurring), category_id, trans_id, current_user.id))

            # Handle recurring transactions
            with db._get_cursor() as cursor:
                if int(recurring):
                    # Check if this transaction already exists in recurringTransactions
                    cursor.execute("SELECT 1 FROM recurringTransactions WHERE trans_id = ? AND user_id = ?", (trans_id, current_user.id))
                    exists = cursor.fetchone()
                    
                    if exists:
                        # Update existing recurring transaction
                        cursor.execute("""
                            UPDATE recurringTransactions 
                            SET merchant = ?, amount = ?, date = ?, note = ?, recurring = ?, category_id = ?
                            WHERE trans_id = ? AND user_id = ?
                        """, (merchant, amount, date, note, int(recurring), category_id, trans_id, current_user.id))
                    else:
                        # Add new recurring transaction
                        cursor.execute("""
                            INSERT INTO recurringTransactions 
                            (trans_id, merchant, amount, date, note, recurring, category_id)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """, (trans_id, merchant, amount, date, note, int(recurring), category_id, current_user.id))
                else:
                    # Remove from recurringTransactions if it exists
                    cursor.execute("DELETE FROM recurringTransactions WHERE trans_id = ? AND user_id = ?", (trans_id, current_user.id))
            
            # Return to trigger refresh and close modal
            return None, False, "Save", default_style
        
        except Exception as e:
            return (
                no_update, 
                no_update, 
                ["ERROR: ", str(e)], 
                {
                    'backgroundColor': '#dc3545',
                    'borderColor': '#dc3545',
                    'color': 'white'
                }
            )
# --------------------------------------------------------------------------------------------------------    

# -- CATEGORY VIEWER
# -- AUXILLARY CATEGORY DELETE VIEWER
    @app.callback(
        Output("categories-list", "children"),
        Input("refresh-categories-btn", "n_clicks"),
        Input("transaction-added", "data"),
        Input("category-added", "data"),
        prevent_initial_call = True
    )
    @authenticate_callback
    def update_categories_list(click, trans_added, cat_added):
        # Fetch categories
        with db._get_cursor() as cursor:
        
            query = """
                SELECT c.id, c.name, c.budget
                FROM categories c
                WHERE c.user_id = ?
            """
            params = (current_user.id, ) # tupple

            cursor.execute(query, params)
            categories = cursor.fetchall()
        
        if not categories:
            return dbc.Alert("No categories found", color="info")
        
        # Create transaction cards
        category_cards = []
        for category in categories:

            cat_id, name, budget = category

            card = dbc.Card(
                [
                    dbc.CardBody(
                        dbc.Row(
                            [
                                # Left side - Category info
                                dbc.Col(
                                    html.Div(
                                        [
                                            html.H5(name, className="card-title mb-1"),
                                            html.P(
                                                f"Budget: ${budget:.2f}" if budget else "No budget set",
                                                className="card-text text-muted small mb-0"
                                            )
                                        ],
                                        className="d-flex flex-column"
                                    ),
                                    width=8,
                                    className="d-flex align-items-center"
                                ),
                                # Right side - Buttons
                                dbc.Col(
                                    dbc.ButtonGroup(
                                        [
                                            dbc.Button(
                                                "Edit",
                                                id={"type": "edit-category-btn", "index": cat_id},
                                                color="primary",
                                                size="sm",
                                                className="me-2"
                                            ),
                                            dbc.Button(
                                                "Delete",
                                                id={"type": "delete-category-btn", "index": cat_id},
                                                color="danger",
                                                size="sm"
                                            )
                                        ],
                                        className="float-end"
                                    ),
                                    width=4,
                                    className="d-flex justify-content-end"
                                )
                            ],
                            className="g-0"  # Remove gutter between columns
                        ),
                        className="py-2"
                    )
                ],
                className="mb-3 shadow-sm"
            )
            category_cards.append(card)
        
        return category_cards

    # Callback for delete category
    @app.callback(
        Output("refresh-categories-btn", "n_clicks"),
        Output("refresh-categories-btn", "children"),
        Output("refresh-categories-btn", "style"),
        Output("refresh-transactions-btn", "n_clicks", allow_duplicate=True),
        Input({"type": "delete-category-btn", "index": ALL}, "n_clicks"),
        State({"type": "delete-category-btn", "index": ALL}, "id"),
        prevent_initial_call=True
    )
    @authenticate_callback
    def delete_category(delete_clicks, delete_ids):
        ctx = callback_context
        if not ctx.triggered:
            raise PreventUpdate
        
        cat_id = None
        for index, value in enumerate(delete_clicks):
            
            if value:
                cat_id = delete_ids[index]['index']
                break
            
        if cat_id is None:
            raise PreventUpdate

        # Delete the category
        try:
            with db._get_cursor() as cursor:
            
                # Clear relevant transactions (keep NULL for future access)
                cursor.execute("UPDATE recurringTransactions SET category_id = NULL WHERE category_id = ? AND user_id = ?", (cat_id, current_user.id))
                cursor.execute("UPDATE transactions SET category_id = NULL WHERE category_id = ? AND user_id = ?", (cat_id, current_user.id))

                # Delete categories
                cursor.execute("DELETE FROM categories WHERE id = ? AND user_id = ?", (cat_id, current_user.id))
        
            # Return None to trigger the refresh via the other callback
            return None, no_update, no_update, None
        
        except Exception as e:
                return no_update, ["ERROR: ", str(e)], {
                            'backgroundColor': '#dc3545',  # Red background
                            'borderColor': '#dc3545',
                            'color': 'white'  # White text
                        }, no_update
                
    @app.callback(
        Output("tm-category", "options", allow_duplicate=True),
        Input("category-added", "data"),
        prevent_initial_call=True
    )
    @authenticate_callback
    def update_category_options(n_clicks):
        
        categories_data = db.get_categories(current_user.id)
        category_options = [{"label": name, "value": cat_id} for cat_id, name in categories_data]
        
        return category_options
    
       
# Callback to open edit category modal
    @app.callback(
        Output("edit-category-modal", "is_open"),
        Output("edit-cat-id", "value"),  # Hidden field to store category ID
        Output("edit-cat-name", "value"),
        Output("edit-cat-budget", "value"),
        Output({"type": "edit-category-btn", "index": ALL}, "n_clicks"),
        Input({"type": "edit-category-btn", "index": ALL}, "n_clicks"),
        State({"type": "edit-category-btn", "index": ALL}, "id"),
        prevent_initial_call=True
    )
    @authenticate_callback
    def open_edit_category_modal(edit_clicks, edit_ids):
        ctx = callback_context
        if not ctx.triggered:
            raise PreventUpdate
        
        cat_id = None
        for index, value in enumerate(edit_clicks):
            if value:
                cat_id = edit_ids[index]['index']
                break
        
        if cat_id is None:
            raise PreventUpdate
        
        # Reset all button clicks
        reset_clicks = [None] * len(edit_clicks)

        # Fetch the category data
        try:        
            with db._get_cursor() as cursor:
                cursor.execute("""
                    SELECT id, name, budget
                    FROM categories
                    WHERE id = ? AND user_id = ?
                """, (cat_id, current_user.id))
                category = cursor.fetchone()
            
            if category:
                return (
                    True,  # Open modal
                    category[0],  # id (hidden field)
                    category[1],  # name
                    category[2],  # budget
                    reset_clicks
                )
            else:
                raise Exception("Category not found")
                
        except Exception as e:
            print(f"Error fetching category: {e}")
            raise PreventUpdate

    # Save changes callback
    @app.callback(
        Output("refresh-categories-btn", "n_clicks", allow_duplicate=True),
        Output("edit-category-modal", "is_open", allow_duplicate=True),
        Output("edit-cat-submit-btn", "children", allow_duplicate=True),
        Output("edit-cat-submit-btn", "style", allow_duplicate=True),
        Input("edit-cat-submit-btn", "n_clicks"),
        State("edit-cat-id", "value"),  # Get the category ID from hidden field
        State("edit-cat-name", "value"),
        State("edit-cat-budget", "value"),
        prevent_initial_call=True
    )
    @authenticate_callback
    def update_category(submit_click, cat_id, name, budget):
        if not submit_click:
            raise PreventUpdate
        
        try:
            default_style = {

            }
            
            if not name:
                    return (no_update, no_update, 
                        "Invalid name", 
                        {
                            'backgroundColor': '#dc3545',  # Red background
                            'borderColor': '#dc3545',
                            'color': 'white'  # White text
                        }
                    )
                
            if not isinstance(budget, (int, float)) or budget < 0:
                return (no_update, no_update, 
                        "Invalid budget", 
                        {
                            'backgroundColor': '#dc3545',  # Red background
                            'borderColor': '#dc3545',
                            'color': 'white'  # White text
                        }
                    )
            
            with db._get_cursor() as cursor:
            
                # Update the category
                cursor.execute("""
                    UPDATE categories 
                    SET name = ?, budget = ?
                    WHERE id = ? AND user_id = ?
                """, (name, budget, cat_id, current_user.id))

            
            # Return to trigger refresh and close modal
            return None, False, "Save", default_style
        
        except Exception as e:
            return (
                no_update, 
                no_update, 
                ["ERROR: ", str(e)], 
                {
                    'backgroundColor': '#dc3545',
                    'borderColor': '#dc3545',
                    'color': 'white'
                }
            )
            
    # Cancel click
    @app.callback(
        Output("edit-category-modal", "is_open", allow_duplicate=True),
        Input("edit-cat-cancel-btn", "n_clicks"),
        prevent_initial_call=True
    )
    @authenticate_callback
    def close_edit_modal(cancel_click):
        if cancel_click:
            return False
        raise PreventUpdate
# --------------------------------------------------------------------------------------------------------    
# --------------------------------------------------------------------------
###########
# -- INCOME VIEWER AND MANAGER
    # -- INCOME VIEWER --
    @app.callback(
        Output("iv-income-list", "children"),
        Input("refresh-income-btn", "n_clicks"),
        Input("income-added", "data"),
        Input("iv-num-income-limit", "value"),
        State("iv-search", "value"),
        State("iv-start-date", "date"),
        State("iv-end-date", "date"),
        Input("iv-sort-order", "value"),
        prevent_initial_call = True
    )
    @authenticate_callback
    def update_income_list(n_clicks, income_added, num_income_limit, search_term, start_date, end_date, sort_order):
        
        if num_income_limit is None:
            num_income_limit = 40 # default
        
        # Fetch recent income
        income = db.fetch_recent_income(search_term, start_date, end_date, num_income_limit, sort_order, current_user.id)
        
        if not income:
            return dbc.Alert("No income found", color="info")
        
        # Create transaction cards
        income_cards = []
        for income_source in income:

            inc_id, source, amount, date = income_source

            card = dbc.Card(
                [
                    dbc.CardBody(
                        dbc.Row(
                            [
                                # Left side
                                dbc.Col(
                                    html.Div(
                                        [
                                            html.H5(source, className="card-title mb-1"),
                                            html.P(
                                                f"Income: ${amount:.2f}",
                                                className="card-text text-muted small mb-0"
                                            ),
                                            html.P(f"Date: {date}", className="card-text text-muted small"),
                                        ],
                                        className="d-flex flex-column"
                                    ),
                                    width=8,
                                    className="d-flex align-items-center"
                                ),
                                # Right side - Buttons
                                dbc.Col(
                                    dbc.ButtonGroup(
                                        [
                                            dbc.Button(
                                                "Edit",
                                                id={"type": "edit-income-btn", "index": inc_id},
                                                color="primary",
                                                size="sm",
                                                className="me-2"
                                            ),
                                            dbc.Button(
                                                "Delete",
                                                id={"type": "delete-income-btn", "index": inc_id},
                                                color="danger",
                                                size="sm"
                                            )
                                        ],
                                        className="float-end"
                                    ),
                                    width=4,
                                    className="d-flex justify-content-end"
                                )
                            ],
                            className="g-0"  # Remove gutter between columns
                        ),
                        className="py-2"
                    )
                ],
                className="mb-3 shadow-sm"
            )
            income_cards.append(card)
        
        return income_cards

    
        # Callback to reset date filter
    
    # Reset date filter
    @app.callback(
        Output("iv-start-date", "date"),
        Output("iv-end-date", "date"),
        Input("iv-reset-date-filters", "n_clicks"),
        prevent_initial_call=True
    )
    @authenticate_callback
    def reset_date_filters(n_clicks):
        if n_clicks:
            return None, None  
        return no_update, no_update

    # Callback for delete income
    @app.callback(
        Output("refresh-income-btn", "n_clicks"),
        Output("refresh-income-btn", "children"),
        Output("refresh-income-btn", "style"),
        Input({"type": "delete-income-btn", "index": ALL}, "n_clicks"),
        State({"type": "delete-income-btn", "index": ALL}, "id"),
        prevent_initial_call=True
    )
    @authenticate_callback
    def delete_income(delete_clicks, delete_ids):
        ctx = callback_context
        if not ctx.triggered:
            raise PreventUpdate
        
        inc_id = None
        for index, value in enumerate(delete_clicks):
            
            if value:
                inc_id = delete_ids[index]['index']
                break
            
        if inc_id is None:
            raise PreventUpdate

        # Delete the income
        try:
            with db._get_cursor() as cursor:

                # Delete income
                cursor.execute("DELETE FROM income WHERE id = ? AND user_id = ?", (inc_id, current_user.id))
        
            # Return None to trigger the refresh via the other callback
            return None, no_update, no_update
        
        except Exception as e:
                return no_update, ["ERROR: ", str(e)], {
                            'backgroundColor': '#dc3545',  # Red background
                            'borderColor': '#dc3545',
                            'color': 'white'  # White text
                        }
                
    # Callback to open edit income modal
    @app.callback(
        Output("edit-income-modal", "is_open"),
        Output("edit-income-id", "value"),
        Output("edit-income-source", "value"),
        Output("edit-income-amount", "value"),
        Output("edit-income-date", "date"),
        Output({"type": "edit-income-btn", "index": ALL}, "n_clicks"),
        Input({"type": "edit-income-btn", "index": ALL}, "n_clicks"),
        State({"type": "edit-income-btn", "index": ALL}, "id"),
        prevent_initial_call=True
    )
    @authenticate_callback
    def open_edit_income_modal(edit_clicks, edit_ids):
        ctx = callback_context
        if not ctx.triggered:
            raise PreventUpdate
        
        income_id = None
        for index, value in enumerate(edit_clicks):
            if value:
                income_id = edit_ids[index]['index']
                break
        
        if income_id is None:
            raise PreventUpdate
        
        # Reset all button clicks
        reset_clicks = [None] * len(edit_clicks)

        # Fetch the income data
        try:
            with db._get_cursor() as cursor:
                cursor.execute("""
                    SELECT id, source, amount, date
                    FROM income
                    WHERE id = ? AND user_id = ?
                """, (income_id, current_user.id))
                income = cursor.fetchone()
            
            if income:
                return (
                    True,  # Open modal
                    income[0],  # id
                    income[1],  # source
                    income[2],  # amount
                    income[3],  # date
                    reset_clicks
                )
            else:
                raise Exception("Income record not found")
                
        except Exception as e:
            print(f"Error fetching income: {e}")
            raise PreventUpdate

    # Cancel click
    @app.callback(
        Output("edit-income-modal", "is_open", allow_duplicate=True),
        Input("edit-income-cancel-btn", "n_clicks"),
        prevent_initial_call=True
    )
    @authenticate_callback
    def close_edit_income_modal(cancel_click):
        if cancel_click:
            return False
        raise PreventUpdate

    # Save changes callback
    @app.callback(
        Output("refresh-income-btn", "n_clicks", allow_duplicate=True),
        Output("edit-income-modal", "is_open", allow_duplicate=True),
        Output("edit-income-submit-btn", "children", allow_duplicate=True),
        Output("edit-income-submit-btn", "style", allow_duplicate=True),
        Input("edit-income-submit-btn", "n_clicks"),
        State("edit-income-id", "value"),
        State("edit-income-source", "value"),
        State("edit-income-amount", "value"),
        State("edit-income-date", "date"),
        prevent_initial_call=True
    )
    @authenticate_callback
    def update_income(submit_click, income_id, source, amount, date):
        if not submit_click:
            raise PreventUpdate
        
        try:
            default_style = {

            }
            
            if not source:
                    return (no_update, no_update, 
                        "Invalid source", 
                        {
                            'backgroundColor': '#dc3545',  # Red background
                            'borderColor': '#dc3545',
                            'color': 'white'  # White text
                        }
                    )
                
            if not isinstance(amount, (int, float)) or amount < 0:
                return (no_update, no_update, 
                        "Invalid income", 
                        {
                            'backgroundColor': '#dc3545',  # Red background
                            'borderColor': '#dc3545',
                            'color': 'white'  # White text
                        }
                    )
            
            with db._get_cursor() as cursor:
            
                # Update the income record
                cursor.execute("""
                    UPDATE income 
                    SET source = ?, amount = ?, date = ?
                    WHERE id = ? AND user_id = ?
                """, (source, amount, date, income_id, current_user.id))
            
            # Return to trigger refresh and close modal
            return None, False, "Save", default_style
        
        except Exception as e:
            return (
                no_update, 
                no_update, 
                ["ERROR: ", str(e)], 
                {
                    'backgroundColor': '#dc3545',
                    'borderColor': '#dc3545',
                    'color': 'white'
                }
            )
# --------------------------------------------------------------------------

# IMPORT CSV PANEL
# --- IMPORT CSV ---
    @app.callback(
        [
            Output("import-csv-btn", "children"),
            Output("import-csv-btn", "style"),
            Output("csv-import-output", "children"),
            Output("csv-reset-interval", "disabled"),
        ],
        [
            Input("import-csv-btn", "n_clicks"),
            Input("csv-reset-interval", "n_intervals"),
        ],
        [
            State("upload-transactions", "contents"),
            State("upload-transactions", "filename"),
            State("import-csv-btn", "children"),
        ],
        prevent_initial_call=True
    )
    @authenticate_callback
    def import_csv(n_clicks, n_intervals, contents, filename, current_text):
        ctx = callback_context
        
        if not ctx.triggered:
            raise PreventUpdate
            
        trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
        
        if trigger_id == "import-csv-btn":
            if not contents:
                return (
                    "No file selected!",
                    {
                        'backgroundColor': '#dc3545',
                        'borderColor': '#dc3545',
                        'color': 'white'
                    },
                    "Please upload a CSV file first.",
                    False
                )
            
            try:
                # Parse CSV file
                content_type, content_string = contents.split(',')
                decoded = base64.b64decode(content_string)
                df = pd.read_csv(io.StringIO(decoded.decode('utf-8')))

                # Remove completely empty rows (where all values are NaN/empty)
                df.dropna(how='all', inplace=True)

                # Remove rows where all values are empty strings (if CSV has ,,,,)
                df = df[~df.apply(lambda row: row.str.strip().eq('').all(), axis=1)]

                # Validate required columns exist
                required_columns = {'category', 'merchant', 'amount', 'date'}
                if not required_columns.issubset(df.columns):
                    missing = required_columns - set(df.columns)
                    return (
                        "Missing columns!",
                        {
                            'backgroundColor': '#dc3545',
                            'borderColor': '#dc3545',
                            'color': 'white'
                        },
                        f"CSV is missing required columns: {', '.join(missing)}",
                        False
                    )

                # Validate each row
                errors = []

                # Merchant validation
                empty_merchants = df[df['merchant'].isna() | (df['merchant'].str.strip() == '')]
                if not empty_merchants.empty:
                    errors.append(f"Empty merchant in row(s): {', '.join(map(str, empty_merchants.index + 2))}")

                # Amount validation
                try:
                    # Convert to numeric, which will turn empty strings into NaN
                    df['amount'] = pd.to_numeric(df['amount'], errors='coerce')
                    
                    # Check for empty/NaN values
                    empty_amounts = df[df['amount'].isna()]
                    if not empty_amounts.empty:
                        errors.append(f"Empty amount in row(s): {', '.join(map(str, empty_amounts.index + 2))}")

                except Exception as e:
                    errors.append(f"Invalid amount values: {str(e)}")

                # Date validation
                try:
                    # Convert to datetime, coercing invalid dates to NaT
                    df['date'] = pd.to_datetime(df['date'], errors='coerce')
                    
                    # Check for empty/NaT values
                    empty_dates = df[df['date'].isna()]
                    if not empty_dates.empty:
                        errors.append(f"Empty/invalid date in row(s): {', '.join(map(str, empty_dates.index + 2))}")
                    
                    # Format valid dates
                    df['date'] = df['date'].dt.strftime('%Y-%m-%d')
                    
                except Exception as e:
                    errors.append(f"Date validation error: {str(e)}")

                # Recurring validation and default (unchanged)
                if 'recurring' in df.columns:
                    df['recurring'] = df['recurring'].fillna(0)
                    invalid_recurring = df[~df['recurring'].isin([0, 1])]
                    if not invalid_recurring.empty:
                        errors.append(f"Invalid recurring value (must be 0 or 1) in row(s): {', '.join(map(str, invalid_recurring.index + 2))}")
                else:
                    df['recurring'] = 0

                # Note default
                df['note'] = df['note'].fillna('') if 'note' in df.columns else ''

                # Category validation - only needed for spending (positive amounts)
                with db._get_cursor() as cursor:
                    cursor.execute("SELECT id, name FROM categories WHERE user_id = ?", (current_user.id,))
                    category_map = {name.lower(): id for id, name in cursor.fetchall()}

                invalid_categories = []
                df['category_id'] = None

                # Only validate categories for positive amounts (spending)
                for idx, row in df.iterrows():
                    if row['amount'] > 0:  # Only spending needs categories
                        category_name = str(row['category']).lower()
                        if category_name in category_map:
                            df.at[idx, 'category_id'] = category_map[category_name]
                        else:
                            invalid_categories.append(row['category'])

                if invalid_categories:
                    errors.append(f"Invalid categories for spending entries: {', '.join(set(invalid_categories))}")

                # Return all validation errors if any
                if errors:
                    return (
                        "Validation failed!",
                        {
                            'backgroundColor': '#dc3545',
                            'borderColor': '#dc3545',
                            'color': 'white'
                        },
                        html.Ul([html.Li(error) for error in errors]),
                        False
                    )

                # Split into spending (positive) and income (negative) transactions
                spending_df = df[df['amount'] > 0]
                income_df = df[df['amount'] < 0]

                # Import spending to transactions table
                if not spending_df.empty:
                    spending_transactions = spending_df[['category_id', 'merchant', 'amount', 'date', 'note', 'recurring']].to_records(index=False)

                    records_with_user = [
                        (*record, current_user.id) for record in spending_transactions
                    ]

                    with db._get_cursor() as cursor:
                        cursor.executemany(
                            "INSERT INTO transactions (category_id, merchant, amount, date, note, recurring) VALUES (?, ?, ?, ?, ?, ?, ?)",
                            records_with_user,
                        )

                # Handle recurring spending transactions
                recurring_spending = spending_df[spending_df['recurring'] == 1]
                if not recurring_spending.empty:
                    # Get the last inserted IDs (assuming SQLite)
                    last_row_id = cursor.lastrowid
                    start_id = last_row_id - len(spending_df) + 1
                    
                    # Insert into recurringTransactions table
                    recurring_records = []
                    for idx, row in recurring_spending.iterrows():
                        trans_id = start_id + idx
                        recurring_records.append((
                            trans_id, row['merchant'], row['amount'], row['date'], 
                            row['note'], 1, row['category_id']
                        ))
                    
                    records_with_user = [
                        (*record, current_user.id) for record in recurring_records
                    ]

                    with db._get_cursor() as cursor:
                        cursor.executemany(
                            """INSERT INTO recurringTransactions 
                            (trans_id, merchant, amount, date, note, recurring, category_id)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                            records_with_user,
                        )

                # Import income to income table
                if not income_df.empty:
                    # Convert negative amounts to positive for income table
                    income_df['amount'] = income_df['amount'].abs()
                    # Use merchant as source for income
                    income_records = income_df[['merchant', 'amount', 'date']].to_records(index=False)
                    with db._get_cursor() as cursor:
                        
                        records_with_user = [(*record, current_user.id) for record in income_records]
                        
                        cursor.executemany(
                            "INSERT INTO income (source, amount, date) VALUES (?, ?, ?, ?)",
                            records_with_user,
                        )

                total_imported = len(spending_df) + len(income_df)
                message = []
                if len(spending_df) > 0:
                    message.append(f"Imported {len(spending_df)} spending transactions")
                if len(income_df) > 0:
                    message.append(f"Imported {len(income_df)} income entries")

                return (
                    "Import Successful!",
                    {
                        'backgroundColor': '#28a745',
                        'borderColor': '#28a745',
                        'color': 'white'
                    },
                    f"Successfully imported {total_imported} records. {' '.join(message)}",
                    False
                )
                
            except Exception as e:
                return (
                    "Import Failed",
                    {
                        'backgroundColor': '#dc3545',
                        'borderColor': '#dc3545',
                        'color': 'white'
                    },
                    f"Error: {str(e)}",
                    False
                )
        
        elif trigger_id == "csv-reset-interval":
            if current_text in ["Import Successful!", "Import Failed", "No file selected!", "Missing columns!", "Validation failed!"]:
                return (
                    "Import Transactions",
                    {
                        'backgroundColor': '#007bff',
                        'borderColor': '#007bff',
                        'color': 'white'
                    },
                    no_update,
                    True
                )
        
        raise PreventUpdate

# --------------------------------------------------------------------------

# # CODE INJECTOR PANEL
# # --- EXECUTE CODE ---
#     @app.callback(
#         [
#             Output("execute-code-btn", "children"),
#             Output("execute-code-btn", "style"),
#             Output("code-output", "children"),
#             Output("code-reset-interval", "disabled"),
#         ],
#         [
#             Input("execute-code-btn", "n_clicks"),
#             Input("code-reset-interval", "n_intervals"),
#         ],
#         [
#             State("code-input", "value"),
#             State("execute-code-btn", "children"),
#         ],
#         prevent_initial_call=True
#     )
#     @authenticate_callback
#     def execute_code(n_clicks, n_intervals, code, current_text):
#         ctx = callback_context
        
#         if not ctx.triggered:
#             raise PreventUpdate
            
#         trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
        
#         if trigger_id == "execute-code-btn":
#             if not code:
#                 return (
#                     "Script missing!",
#                     {
#                         'backgroundColor': '#dc3545',
#                         'borderColor': '#dc3545',
#                         'color': 'white'
#                     },
#                     "Enter python or SQL script",
#                     False  # Enable interval to reset
#                 )
            
#             try:
#                 # Check if it looks like SQL
#                 if code.strip().lower().startswith(('select', 'insert', 'update', 'delete', 'create', 'alter', 'drop')):
#                     with db._get_cursor() as cursor:
#                         cursor.execute(code)
                        
#                         if code.strip().lower().startswith('select'):
#                             # For SELECT queries, show results
#                             results = cursor.fetchall()
#                             columns = [description[0] for description in cursor.description]
#                             df = pd.DataFrame(results, columns=columns)
#                             output = dbc.Table.from_dataframe(df, striped=True, bordered=True, hover=True)
#                         else:
#                             # For other SQL, commit and show success
#                             output = f"SQL executed successfully. Rows affected: {cursor.rowcount}"
#                 else:
#                     # Execute as Python code
#                     local_vars = {'db': db, 'pd': pd}
                    
#                     # Redirect stdout to capture prints
#                     old_stdout = sys.stdout
#                     sys.stdout = captured_output = io.StringIO()
                    
#                     try:
#                         exec(code, globals(), local_vars)
                        
#                         # Get printed output
#                         printed_output = captured_output.getvalue()
                        
#                         # Also capture the last expression's value (if any)
#                         if code.strip().split('\n')[-1].startswith((' ', '\t')) is False:
#                             last_line = code.strip().split('\n')[-1]
#                             if not last_line.startswith(('print', 'import', 'def', 'class', 'for', 'if', 'while')):
#                                 try:
#                                     last_expr_value = str(eval(last_line, globals(), local_vars))
#                                     printed_output += f"\nLast expression value: {last_expr_value}"
#                                 except:
#                                     pass
                        
#                         output = f"Execution successful!\n\n--- Output ---\n{printed_output}" if printed_output else "Code executed (no output)"
                        
#                     except Exception as e:
#                         output = f"Error: {str(e)}"
#                     finally:
#                         sys.stdout = old_stdout  # Restore stdout
                    
#                 return (
#                     "Code Executed!",
#                     {
#                         'backgroundColor': '#28a745',
#                         'borderColor': '#28a745',
#                         'color': 'white'
#                     },
#                     output,
#                     False  # Enable interval to reset
#                 )
                
#             except Exception as e:
#                 return (
#                     "Execution Error",
#                     {
#                         'backgroundColor': '#dc3545',
#                         'borderColor': '#dc3545',
#                         'color': 'white'
#                     },
#                     f"Error: {str(e)}",
#                     False  # Enable interval to reset
#                 )
        
#         elif trigger_id == "code-reset-interval":
#             if current_text in ["Code Executed!", "Execution Error", "No code entered!"]:
#                 return (
#                     "Execute Code",
#                     {
#                         'backgroundColor': '#007bff',
#                         'borderColor': '#007bff',
#                         'color': 'white'
#                     },
#                     no_update,
#                     True  # Disable interval again
#                 )
        
#         raise PreventUpdate
# --------------------------------------------------------------------------

#-----------------------------------------------------------------------------------
    # --- NET WORTH MANAGER CALLBACKS ---
# ------------------------------------------------------------------------------------

    # Add assets and manage the asset list
    @app.callback(
        [Output('stored-assets', 'data'),
        Output('added-assets-list', 'children'),
        Output('assets-summary', 'children'),
        Output('nw-asset-name', 'value'),
        Output('nw-asset-amount', 'value'),
        Output('nw-asset-note', 'value')],
        [Input('add-asset-btn', 'n_clicks'),
        Input('clear-assets-btn', 'n_clicks')],
        [State('nw-asset-name', 'value'),
        State('nw-asset-amount', 'value'),
        State('nw-asset-type', 'value'),
        State('nw-asset-note', 'value'),
        State('stored-assets', 'data')],
        prevent_initial_call=True
    )
    @authenticate_callback
    def manage_assets(add_clicks, clear_clicks, name, amount, asset_type, note, stored_assets):
        ctx = callback_context
        triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]

        if triggered_id == 'clear-assets-btn':
            return [], [], "No assets added", None, None, None

        if triggered_id == 'add-asset-btn':
            if not name or amount is None:
                raise PreventUpdate

            # Create new asset object
            new_asset = {
                'id': str(uuid.uuid4()),  # Generate unique ID
                'name': name,
                'amount': float(amount),
                'type': asset_type,
                'note': note if note else ''
            }

            # Add to stored assets
            updated_assets = stored_assets + [new_asset]

            # Generate assets list display
            assets_list = [
                dbc.ListGroupItem(
                    [
                        dbc.Row([
                            dbc.Col(html.Strong(asset['name']), width=4),
                            dbc.Col(f"${asset['amount']:,.2f}", width=3),
                            dbc.Col(asset['type'].capitalize(), width=3),
                            dbc.Col(
                                dbc.Button(
                                    "×",
                                    id={'type': 'remove-asset', 'index': asset['id']},
                                    color="danger",
                                    size="sm",
                                    className="p-1"
                                ),
                                width=2
                            )
                        ]),
                        dbc.Row(
                            dbc.Col(
                                html.Small(asset['note'], className="text-muted"),
                                width=12
                            ),
                            className="mt-1"
                        ) if asset['note'] else None
                    ],
                    className="mb-2"
                )
                for asset in updated_assets
            ]

            # Calculate summary
            total_assets = sum(asset['amount'] for asset in updated_assets)
            summary = [
                html.Div(f"Total Assets: ${total_assets:,.2f}", className="h5"),
                html.Div(f"{len(updated_assets)} items", className="text-muted")
            ]

            # Clear input fields
            return updated_assets, assets_list, summary, "", None, ""

        raise PreventUpdate

    # Callback to remove individual assets
    @app.callback(
        [Output('stored-assets', 'data', allow_duplicate=True),
        Output('added-assets-list', 'children', allow_duplicate=True),
        Output('assets-summary', 'children',  allow_duplicate=True)],
        [Input({'type': 'remove-asset', 'index': ALL}, 'n_clicks')],
        [State('stored-assets', 'data')],
        prevent_initial_call=True
    )
    @authenticate_callback
    def remove_asset(remove_clicks, stored_assets):
        if not any(remove_clicks):
            raise PreventUpdate

        # Find which asset was clicked
        ctx = callback_context
        triggered_id = ctx.triggered[0]['prop_id']
        asset_id = json.loads(triggered_id.split('.')[0])['index']

        # Remove the asset
        updated_assets = [asset for asset in stored_assets if asset['id'] != asset_id]

        # Generate assets list display
        assets_list = [
            dbc.ListGroupItem(
                [
                    dbc.Row([
                        dbc.Col(html.Strong(asset['name']), width=4),
                        dbc.Col(f"${asset['amount']:,.2f}", width=3),
                        dbc.Col(asset['type'].capitalize(), width=3),
                        dbc.Col(
                            dbc.Button(
                                "×",
                                id={'type': 'remove-asset', 'index': asset['id']},
                                color="danger",
                                size="sm",
                                className="p-1"
                            ),
                            width=2
                        )
                    ]),
                    dbc.Row(
                        dbc.Col(
                            html.Small(asset['note'], className="text-muted"),
                            width=12
                        ),
                        className="mt-1"
                    ) if asset['note'] else None
                ],
                className="mb-2"
            )
            for asset in updated_assets
        ]

        # Recalculate summary
        total_assets = sum(asset['amount'] for asset in updated_assets)
        summary = [
            html.Div(f"Total Assets: ${total_assets:,.2f}", className="h5"),
            html.Div(f"{len(updated_assets)} items", className="text-muted")
        ]

        return updated_assets, assets_list, summary
    
    # Add liabilities and manage the liability list
    @app.callback(
        [Output('stored-liabilities', 'data'),
        Output('added-liabilities-list', 'children'),
        Output('liabilities-summary', 'children'),
        Output('nw-liability-name', 'value'),
        Output('nw-liability-amount', 'value'),
        Output('nw-liability-note', 'value')],
        [Input('add-liability-btn', 'n_clicks'),
        Input('clear-liabilities-btn', 'n_clicks')],
        [State('nw-liability-name', 'value'),
        State('nw-liability-amount', 'value'),
        State('nw-liability-type', 'value'),
        State('nw-liability-note', 'value'),
        State('stored-liabilities', 'data')],
        prevent_initial_call=True
    )
    @authenticate_callback
    def manage_liabilities(add_clicks, clear_clicks, name, amount, liability_type, note, stored_liabilities):
        ctx = callback_context
        triggered_id = ctx.triggered[0]['prop_id'].split('.')[0]

        if triggered_id == 'clear-liabilities-btn':
            return [], [], "No liabilities added", None, None, None

        if triggered_id == 'add-liability-btn':
            if not name or amount is None:
                raise PreventUpdate

            # Create new liability object
            new_liability = {
                'id': str(uuid.uuid4()),  # Generate unique ID
                'name': name,
                'amount': float(amount),
                'type': liability_type,
                'note': note if note else ''
            }

            # Add to stored liabilities
            updated_liabilities = stored_liabilities + [new_liability]

            # Generate liabilities list display
            liabilities_list = [
                dbc.ListGroupItem(
                    [
                        dbc.Row([
                            dbc.Col(html.Strong(liability['name']), width=4),
                            dbc.Col(f"${liability['amount']:,.2f}", width=3),
                            dbc.Col(liability['type'].capitalize(), width=3),
                            dbc.Col(
                                dbc.Button(
                                    "×",
                                    id={'type': 'remove-liability', 'index': liability['id']},
                                    color="danger",
                                    size="sm",
                                    className="p-1"
                                ),
                                width=2
                            )
                        ]),
                        dbc.Row(
                            dbc.Col(
                                html.Small(liability['note'], className="text-muted"),
                                width=12
                            ),
                            className="mt-1"
                        ) if liability['note'] else None
                    ],
                    className="mb-2"
                )
                for liability in updated_liabilities
            ]

            # Calculate summary
            total_liabilities = sum(liability['amount'] for liability in updated_liabilities)
            summary = [
                html.Div(f"Total Liabilities: ${total_liabilities:,.2f}", className="h5"),
                html.Div(f"{len(updated_liabilities)} items", className="text-muted")
            ]

            # Clear input fields
            return updated_liabilities, liabilities_list, summary, "", None, ""

        raise PreventUpdate


    # Callback to remove individual liabilities
    @app.callback(
        [Output('stored-liabilities', 'data', allow_duplicate=True),
        Output('added-liabilities-list', 'children', allow_duplicate=True),
        Output('liabilities-summary', 'children',  allow_duplicate=True)],
        [Input({'type': 'remove-liability', 'index': ALL}, 'n_clicks')],
        [State('stored-liabilities', 'data')],
        prevent_initial_call=True
    )
    @authenticate_callback
    def remove_liability(remove_clicks, stored_liabilities):
        if not any(remove_clicks):
            raise PreventUpdate

        # Find which liability was clicked
        ctx = callback_context
        triggered_id = ctx.triggered[0]['prop_id']
        liability_id = json.loads(triggered_id.split('.')[0])['index']

        # Remove the liability
        updated_liabilities = [liability for liability in stored_liabilities if liability['id'] != liability_id]

        # Generate liabilities list display
        liabilities_list = [
            dbc.ListGroupItem(
                [
                    dbc.Row([
                        dbc.Col(html.Strong(liability['name']), width=4),
                        dbc.Col(f"${liability['amount']:,.2f}", width=3),
                        dbc.Col(liability['type'].capitalize(), width=3),
                        dbc.Col(
                            dbc.Button(
                                "×",
                                id={'type': 'remove-liability', 'index': liability['id']},
                                color="danger",
                                size="sm",
                                className="p-1"
                            ),
                            width=2
                        )
                    ]),
                    dbc.Row(
                        dbc.Col(
                            html.Small(liability['note'], className="text-muted"),
                            width=12
                        ),
                        className="mt-1"
                    ) if liability['note'] else None
                ],
                className="mb-2"
            )
            for liability in updated_liabilities
        ]

        # Recalculate summary
        total_liabilities = sum(liability['amount'] for liability in updated_liabilities)
        summary = [
            html.Div(f"Total Liabilities: ${total_liabilities:,.2f}", className="h5"),
            html.Div(f"{len(updated_liabilities)} items", className="text-muted")
        ]

        return updated_liabilities, liabilities_list, summary


    # Update the review tab totals
    @app.callback(
        [Output('total-assets-display', 'children'),
        Output('total-liabilities-display', 'children'),
        Output('net-worth-display', 'children')],
        [Input('stored-assets', 'data'),
        Input('stored-liabilities', 'data')]
    )
    @authenticate_callback
    def update_review_totals(assets, liabilities):
        total_assets = sum(asset['amount'] for asset in assets) if assets else 0
        total_liabilities = sum(liability['amount'] for liability in liabilities) if liabilities else 0
        net_worth = total_assets - total_liabilities
        
        return [
            f"${total_assets:,.2f}",
            f"${total_liabilities:,.2f}",
            f"${net_worth:,.2f}"
        ]
    
    # SAVE NET WORTH SNAPSHOT
    @app.callback(
        [Output('net-worth-data', 'data'),
        Output('save-success-alert', 'is_open'),
        Output('save-success-alert', 'children')],
        [Input('save-networth-btn', 'n_clicks')],
        [State('stored-assets', 'data'),
        State('stored-liabilities', 'data'),
        State('nw-snapshot-note', 'value'),
        State('net-worth-data', 'data')],
        prevent_initial_call=True
    )
    @authenticate_callback
    def save_networth_snapshot(n_clicks, assets, liabilities, note, existing_data):
        if not n_clicks:
            raise PreventUpdate
        
        try:
            # Calculate totals
            total_assets = sum(asset['amount'] for asset in assets) if assets else 0
            total_liabilities = sum(liability['amount'] for liability in liabilities) if liabilities else 0
            net_worth = total_assets - total_liabilities
            snapshot_date = datetime.now().strftime('%Y-%m-%d')
            
            # First mark all previous snapshots as not current
            with db._get_cursor() as cursor:
                cursor.execute(
                    "UPDATE net_worth_snapshots SET is_current = 0 WHERE user_id = ?",
                    (current_user.id, )
                )
                
                # Insert the new snapshot
                cursor.execute(
                    """
                    INSERT INTO net_worth_snapshots 
                    (snapshot_date, note, total_assets, total_liabilities, net_worth, is_current, user_id)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        snapshot_date,
                        note,
                        total_assets,
                        total_liabilities,
                        net_worth,
                        1,
                        current_user.id,
                    ),
                )
                
                # Get the newly created snapshot ID
                snapshot_id = cursor.lastrowid
                
                # Insert all assets
                for asset in assets:
                    cursor.execute(
                        """
                        INSERT INTO net_worth_items
                        (snapshot_id, name, type, category, amount, note)
                        VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (snapshot_id, asset['name'], 'asset', asset['type'], asset['amount'], asset.get('note', ''))
                    )
                
                # Insert all liabilities
                for liability in liabilities:
                    cursor.execute(
                        """
                        INSERT INTO net_worth_items
                        (snapshot_id, name, type, category, amount, note)
                        VALUES (?, ?, ?, ?, ?, ?)
                        """,
                        (snapshot_id, liability['name'], 'liability', liability['type'], liability['amount'], liability.get('note', ''))
                    )
            
            # Prepare success message
            success_message = f"Snapshot saved for {snapshot_date} with {len(assets)} assets and {len(liabilities)} liabilities"
            
            # Return updated data and show success alert
            return {
                'last_saved': snapshot_date,
                'assets_count': len(assets),
                'liabilities_count': len(liabilities),
                'net_worth': net_worth
            }, True, success_message
            
        except Exception as e:
            error_message = f"Error saving snapshot: {str(e)}"
            return no_update, True, error_message
