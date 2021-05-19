import math
import pandas as pd

import webviz_4d._datainput.common as common
from webviz_4d._datainput.well import get_well_polyline


def get_production_type(selection):
    if "production" in selection:
        production_type = "production"
    elif "injection" in selection:
        production_type = "injection"
    else:
        production_type = None

    return production_type


def check_interval(interval):
    """Flip start and end date if needed"""
    dates = [interval[0:10], interval[11:21]]

    if dates[0] > dates[1]:
        selected_interval = dates[1] + "-" + dates[0]
    else:
        selected_interval = interval

    return selected_interval


def get_value(metadata_df, item, mode):
    try:
        values = metadata_df[item].values

        if isinstance(mode, str) and mode == "min":
            value = min(values)
        elif isinstance(mode, int) and mode < len(values):
            value = values[0]
        else:
            return None
    except:
        return None

    return value


def make_new_well_layer(
    interval_4d,
    wells_df,
    metadata_df,
    prod_data=None,
    colors=None,
    selection=None,
    fluids=[],
    label="Drilled wells",
):
    """Make layeredmap wells layer"""

    data = []

    wellbores = metadata_df["wellbore.name"].values
    list_set = set(wellbores)
    # convert the set to the list
    unique_wellbores = sorted(list(list_set))

    for wellbore in unique_wellbores:
        status = False
        md_start = 0
        md_end = None
        color = "black"

        well_metadata = metadata_df[metadata_df["wellbore.name"] == wellbore]
        md_top_res = get_value(well_metadata, "wellbore.top_res_md", "min")
        short_name = get_value(well_metadata, "wellbore.short_name", 0)
        true_name = get_value(well_metadata, "wellbore.true_name", 0)
        pdm_well_name = get_value(well_metadata, "wellbore.pdm_name", 0)
        top_completion = get_value(well_metadata, "top_completion_md", 0)
        base_completion = get_value(well_metadata, "base_completion_md", 0)
        well_type = get_value(well_metadata, "wellbore.type", 0)
        well_label = get_value(well_metadata, "layer_name", 0)
        well_dataframe = wells_df[wells_df["WELLBORE_NAME"] == true_name]

        fluids = get_value(well_metadata, "wellbore.fluids", 0)

        if not isinstance(fluids, str):
            fluids = ""

        tooltip = str(short_name) + ": " + well_type + " (" + str(fluids) + ")"

        if selection == "drilled_wells":
            color = "black"
            status = True
        elif selection == "planned" and well_type == selection and well_label == label:
            color = colors[selection]
            status = True
        elif selection == "reservoir_section":
            color = "black"
            if md_top_res:
                md_start = md_top_res
                status = True
        else:
            volume = 0
            interval = check_interval(interval_4d)

            if md_top_res:
                md_start = md_top_res

            if "production" in selection and md_top_res:
                fluid = "oil"
                prod_type = "production"
                fluid_code = fluid + "_production"
                start_date, stop_date, volume = extract_production_info(
                    pdm_well_name, prod_data, interval, "production", fluid
                )
                info = get_info(start_date, stop_date, fluid, volume)

            elif "injection" in selection and md_top_res:
                gi_start_date, gi_stop_date, gi_volume = extract_production_info(
                    pdm_well_name, prod_data, interval, "injection", "gas"
                )
                wi_start_date, wi_stop_date, wi_volume = extract_production_info(
                    pdm_well_name, prod_data, interval, "injection", "water"
                )

                if gi_start_date and wi_start_date:
                    start_date = min(gi_start_date, wi_start_date)
                    stop_date = max(gi_start_date, wi_start_date)
                    fluid = "wag"
                    fluid_code = fluid + "_injection"
                    volume = 1
                elif gi_start_date:
                    start_date = gi_start_date
                    stop_date = gi_stop_date
                    fluid = "gas"
                    fluid_code = fluid + "_injection"
                    volume = gi_volume
                elif wi_start_date:
                    start_date = wi_start_date
                    stop_date = wi_stop_date
                    fluid = "water"
                    fluid_code = fluid + "_injection"
                    volume = wi_volume

                prod_type = "injection"

            if volume and volume > 0:
                info = get_info(start_date, stop_date, fluid, volume)

                started = check_interval_date(interval, start_date)
                stopped = check_interval_date(interval, stop_date)

                if "active" in selection and start_date:
                    if stop_date is None or stop_date == "---":
                        color = "black"
                        info = get_info(start_date, stop_date, fluid, volume)
                        status = True
                elif "start" in selection and started == "inside":
                    color = colors[fluid_code]
                    info = get_info(start_date, stop_date, fluid, volume)
                    status = True
                else:
                    color = colors[fluid_code]
                    if started == "greater" or stopped == "less":
                        interval_status = False
                    else:
                        interval_status = True

                    if interval_status:
                        color = colors[fluid_code]
                        info = get_info(start_date, stop_date, fluid, volume)

                        if (
                            "completed" in selection
                            and top_completion
                            and base_completion
                        ):
                            md_start = top_completion
                            md_end = base_completion
                            status = True
                        elif selection == "production" or selection == "injection":
                            status = True
            if status:
                tooltip = short_name + ": " + prod_type + " (" + info + ")"

        polyline_data = False

        if status:
            polyline_data = get_well_polyline(
                well_dataframe,
                md_start,
                md_end,
                color,
                tooltip,
            )

        if polyline_data:
            data.append(polyline_data)

    if data:
        layer = {"name": label, "checked": False, "base_layer": False, "data": data}
    else:
        layer = {"name": label, "checked": False, "base_layer": False, "data": []}

    return layer


def extract_production_info(pdm_well_name, prod_data, interval, production_type, fluid):
    """Return well and production information/status for a selected
    interval for production/injection wells"""

    start_date = None
    stop_date = None
    volume = None

    headers = prod_data.columns
    first_date = common.get_dates(headers[6])[0]
    try:
        well_prod_info = prod_data.loc[
            (prod_data["PDM well name"] == pdm_well_name)
            & (prod_data["Production type"] == production_type)
            & (prod_data["Fluid"] == fluid)
        ]

        start_date = well_prod_info["Start date"].values[0]
        stop_date = well_prod_info["Last date"].values[0]
    except:
        well_prod_info = pd.DataFrame()

    if interval == "" and not well_prod_info.empty:
        volume = well_prod_info.iloc[:, -1:].values[0][0]
    elif not well_prod_info.empty:
        dates = common.get_dates(interval)

        if dates[0] == first_date:
            column = interval
            volume = well_prod_info[column].values[0]
        else:
            column1 = first_date + "-" + dates[0]
            column2 = first_date + "-" + dates[1]
            volume = (
                well_prod_info[column2].values[0] - well_prod_info[column1].values[0]
            )

        if math.isnan(volume) or volume == 0:
            volume = None

        if start_date != start_date:
            start_date = None

        if stop_date != stop_date:
            stop_date = None
    return start_date, stop_date, volume


def get_info(start_date, stop_date, fluid, volume):
    units = {"oil": "[kSm3]", "water": "[kSm3]", "gas": "[MSm3]"}

    if volume is None or volume == 0:
        return None

    unit = units.get(fluid)

    if stop_date is None or (not isinstance(stop_date, str) and math.isnan(stop_date)):
        stop_date = "---"

    if fluid == "wag":
        info = "(WAG) Start:" + str(start_date) + " Last: " + str(stop_date)
    else:
        info = (
            fluid
            + " {:.0f} ".format(volume)
            + unit
            + " Start: "
            + str(start_date)
            + " Last: "
            + str(stop_date)
        )

    return info


def check_interval_date(interval, selected_date):
    if selected_date is None or (
        not isinstance(selected_date, str) and math.isnan(selected_date)
    ):
        status = None
    elif selected_date >= interval[:10]:
        if selected_date < interval[11:]:
            status = "inside"
        else:
            status = "greater"
    else:
        status = "less"

    return status
