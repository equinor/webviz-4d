import dash
from dash.exceptions import PreventUpdate
from dash.dependencies import Input, Output, State


def set_first_map(parent, app):
    # First map
    @app.callback(
        [
            Output(parent.uuid("heading1"), "children"),
            Output(parent.uuid("sim_info1"), "children"),
            Output(parent.uuid("map"), "layers"),
            Output(parent.uuid("interval-label1"), "children"),
        ],
        [
            Input(parent.selector.storage_id, "children"),
            Input(parent.uuid("ensemble"), "value"),
            Input(parent.uuid("realization"), "value"),
            Input(parent.uuid("attribute-settings"), "data"),
        ],
    )
    # pylint: disable=too-many-arguments, too-many-locals
    def _set_base_layer(
        data,
        ensemble,
        real,
        attribute_settings,
    ):
        return parent.make_map(data, ensemble, real, attribute_settings, 0)


def set_second_map(parent, app):
    # Second map
    @app.callback(
        [
            Output(parent.uuid("heading2"), "children"),
            Output(parent.uuid("sim_info2"), "children"),
            Output(parent.uuid("map2"), "layers"),
            Output(parent.uuid("interval-label2"), "children"),
        ],
        [
            Input(parent.selector2.storage_id, "children"),
            Input(parent.uuid("ensemble2"), "value"),
            Input(parent.uuid("realization2"), "value"),
            Input(parent.uuid("attribute-settings"), "data"),
        ],
    )
    # pylint: disable=too-many-arguments, too-many-locals
    def _set_base_layer(
        data,
        ensemble,
        real,
        attribute_settings,
    ):
        return parent.make_map(data, ensemble, real, attribute_settings, 1)


def set_third_map(parent, app):
    # Third map
    @app.callback(
        [
            Output(parent.uuid("heading3"), "children"),
            Output(parent.uuid("sim_info3"), "children"),
            Output(parent.uuid("map3"), "layers"),
            Output(parent.uuid("interval-label3"), "children"),
        ],
        [
            Input(parent.selector3.storage_id, "children"),
            Input(parent.uuid("ensemble3"), "value"),
            Input(parent.uuid("realization3"), "value"),
            Input(parent.uuid("attribute-settings"), "data"),
        ],
    )
    # pylint: disable=too-many-arguments, too-many-locals
    def _set_base_layer(
        data,
        ensemble,
        real,
        attribute_settings,
    ):
        return parent.make_map(data, ensemble, real, attribute_settings, 2)


def change_maps_from_button(parent, app):
    def _update_from_btn(_n_prev, _n_next, current_value, options):
        """Updates dropdown value if previous/next btn is clicked"""
        options = [opt["value"] for opt in options]
        ctx = dash.callback_context.triggered
        if not ctx or current_value is None:
            raise PreventUpdate
        if not ctx[0]["value"]:
            return current_value
        callback = ctx[0]["prop_id"]
        if "-prev" in callback:
            return prev_value(current_value, options)
        if "-next" in callback:
            return next_value(current_value, options)
        return current_value

    for btn_name in [
        "ensemble",
        "realization",
        "ensemble2",
        "realization2",
        "ensemble3",
        "realization3",
    ]:
        app.callback(
            Output(parent.uuid(f"{btn_name}"), "value"),
            [
                Input(parent.uuid(f"{btn_name}-prev"), "n_clicks"),
                Input(parent.uuid(f"{btn_name}-next"), "n_clicks"),
            ],
            [
                State(parent.uuid(f"{btn_name}"), "value"),
                State(parent.uuid(f"{btn_name}"), "options"),
            ],
        )(_update_from_btn)


def prev_value(current_value, options):
    try:
        index = options.index(current_value)
        return options[max(0, index - 1)]
    except ValueError:
        return current_value


def next_value(current_value, options):
    try:
        index = options.index(current_value)
        return options[min(len(options) - 1, index + 1)]

    except ValueError:
        return current_value
