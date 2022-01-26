import json

import webviz_core_components as wcc
from dash import html
from dash import dcc

from webviz_subsurface_components import LayeredMap


def set_grid_layout(columns):
    return {
        "display": "grid",
        "alignContent": "space-around",
        "justifyContent": "space-between",
        "gridTemplateColumns": f"{columns}",
    }


def ensemble_layout(
    parent,
    map_number,
    ensemble_id,
    ens_prev_id,
    ens_next_id,
    real_id,
    real_prev_id,
    real_next_id,
):
    return wcc.FlexBox(
        children=[
            html.Div(
                [
                    html.Label(
                        "Ensemble / Iteration",
                        style={"fontSize": 15, "fontWeight": "bold"},
                    ),
                    html.Div(
                        style=set_grid_layout("12fr 1fr 1fr"),
                        children=[
                            dcc.Dropdown(
                                options=[
                                    {"label": ens, "value": ens}
                                    for ens in parent.ensembles(map_number)
                                ],
                                value=parent.map_defaults[map_number]["ensemble"],
                                id=ensemble_id,
                                clearable=False,
                                persistence=True,
                                persistence_type="session",
                                style={
                                    "fontSize": 15,
                                    "fontWeight": "normal",
                                },
                            ),
                            html.Button(
                                style={
                                    "fontSize": "2rem",
                                    "paddingLeft": "5px",
                                    "paddingRight": "5px",
                                },
                                id=ens_prev_id,
                                children="⬅",
                            ),
                            html.Button(
                                style={
                                    "fontSize": "2rem",
                                    "paddingLeft": "5px",
                                    "paddingRight": "5px",
                                },
                                id=ens_next_id,
                                children="➡",
                            ),
                        ],
                    ),
                ]
            ),
            html.Div(
                children=[
                    html.Label(
                        "Realization / Statistic",
                        style={"fontSize": 15, "fontWeight": "bold"},
                    ),
                    html.Div(
                        style=set_grid_layout("12fr 1fr 1fr"),
                        children=[
                            dcc.Dropdown(
                                options=[
                                    {"label": real, "value": real}
                                    for real in parent.realizations(map_number)
                                ],
                                value=parent.map_defaults[map_number]["realization"],
                                id=real_id,
                                clearable=False,
                                persistence=True,
                                persistence_type="session",
                                style={"fontSize": 15, "fontWeight": "normal"},
                            ),
                            html.Button(
                                style={
                                    "fontSize": "2rem",
                                    "paddingLeft": "5px",
                                    "paddingRight": "5px",
                                },
                                id=real_prev_id,
                                children="⬅",
                            ),
                            html.Button(
                                style={
                                    "fontSize": "2rem",
                                    "paddingLeft": "5px",
                                    "paddingRight": "5px",
                                },
                                id=real_next_id,
                                children="➡",
                            ),
                        ],
                    ),
                ]
            ),
        ]
    )


def set_layout(parent):
    update_txt = "Well data update: " + parent.well_update
    if parent.production_update != "":
        update_txt = (
            update_txt + "  Production data update: " + parent.production_update
        )
    return html.Div(
        id=parent.uuid("layout"),
        children=[
            html.H6("Webviz-4D " + parent.label),
            wcc.FlexBox(
                style={"fontSize": "1rem"},
                children=[
                    html.Div(
                        id=parent.uuid("settings-view1"),
                        style={"margin": "10px", "flex": 4},
                        children=[
                            parent.selector.layout,
                            ensemble_layout(
                                parent=parent,
                                map_number=0,
                                ensemble_id=parent.uuid("ensemble"),
                                ens_prev_id=parent.uuid("ensemble-prev"),
                                ens_next_id=parent.uuid("ensemble-next"),
                                real_id=parent.uuid("realization"),
                                real_prev_id=parent.uuid("realization-prev"),
                                real_next_id=parent.uuid("realization-next"),
                            ),
                        ],
                    ),
                    html.Div(
                        style={"margin": "10px", "flex": 4},
                        id=parent.uuid("settings-view2"),
                        children=[
                            parent.selector2.layout,
                            ensemble_layout(
                                parent=parent,
                                map_number=1,
                                ensemble_id=parent.uuid("ensemble2"),
                                ens_prev_id=parent.uuid("ensemble2-prev"),
                                ens_next_id=parent.uuid("ensemble2-next"),
                                real_id=parent.uuid("realization2"),
                                real_prev_id=parent.uuid("realization2-prev"),
                                real_next_id=parent.uuid("realization2-next"),
                            ),
                        ],
                    ),
                    html.Div(
                        style={"margin": "10px", "flex": 4},
                        id=parent.uuid("settings-view3"),
                        children=[
                            parent.selector3.layout,
                            ensemble_layout(
                                parent=parent,
                                map_number=2,
                                ensemble_id=parent.uuid("ensemble3"),
                                ens_prev_id=parent.uuid("ensemble3-prev"),
                                ens_next_id=parent.uuid("ensemble3-next"),
                                real_id=parent.uuid("realization3"),
                                real_prev_id=parent.uuid("realization3-prev"),
                                real_next_id=parent.uuid("realization3-next"),
                            ),
                        ],
                    ),
                ],
            ),
            wcc.FlexBox(
                style={"fontSize": "1rem"},
                children=[
                    html.Div(
                        style={"margin": "10px", "flex": 4},
                        children=[
                            html.Div(
                                id=parent.uuid("heading1"),
                                style={
                                    "textAlign": "center",
                                    "fontSize": 20,
                                    "fontWeight": "bold",
                                },
                            ),
                            html.Div(
                                id=parent.uuid("sim_info1"),
                                style={
                                    "textAlign": "center",
                                    "fontSize": 15,
                                    "fontWeight": "bold",
                                },
                            ),
                            LayeredMap(
                                sync_ids=[parent.uuid("map2"), parent.uuid("map3")],
                                id=parent.uuid("map"),
                                height=600,
                                layers=[],
                                hillShading=False,
                            ),
                            html.Div(
                                id=parent.uuid("interval-label1"),
                                style={
                                    "textAlign": "center",
                                    "fontSize": 20,
                                    "fontWeight": "bold",
                                },
                            ),
                        ],
                    ),
                    html.Div(
                        style={"margin": "10px", "flex": 4},
                        children=[
                            html.Div(
                                id=parent.uuid("heading2"),
                                style={
                                    "textAlign": "center",
                                    "fontSize": 20,
                                    "fontWeight": "bold",
                                },
                            ),
                            html.Div(
                                id=parent.uuid("sim_info2"),
                                style={
                                    "textAlign": "center",
                                    "fontSize": 15,
                                    "fontWeight": "bold",
                                },
                            ),
                            LayeredMap(
                                sync_ids=[parent.uuid("map"), parent.uuid("map3")],
                                id=parent.uuid("map2"),
                                height=600,
                                layers=[],
                                hillShading=False,
                            ),
                            html.Div(
                                id=parent.uuid("interval-label2"),
                                style={
                                    "textAlign": "center",
                                    "fontSize": 20,
                                    "fontWeight": "bold",
                                },
                            ),
                        ],
                    ),
                    html.Div(
                        style={"margin": "10px", "flex": 4},
                        children=[
                            html.Div(
                                id=parent.uuid("heading3"),
                                style={
                                    "textAlign": "center",
                                    "fontSize": 20,
                                    "fontWeight": "bold",
                                },
                            ),
                            html.Div(
                                id=parent.uuid("sim_info3"),
                                style={
                                    "textAlign": "center",
                                    "fontSize": 15,
                                    "fontWeight": "bold",
                                },
                            ),
                            LayeredMap(
                                sync_ids=[parent.uuid("map"), parent.uuid("map2")],
                                id=parent.uuid("map3"),
                                height=600,
                                layers=[],
                                hillShading=False,
                            ),
                            html.Div(
                                id=parent.uuid("interval-label3"),
                                style={
                                    "textAlign": "center",
                                    "fontSize": 20,
                                    "fontWeight": "bold",
                                },
                            ),
                        ],
                    ),
                    dcc.Store(
                        id=parent.uuid("attribute-settings"),
                        data=json.dumps(parent.attribute_settings),
                    ),
                ],
            ),
            html.H6(update_txt),
        ],
    )
