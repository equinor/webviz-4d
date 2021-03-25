import pandas as pd
import math

from webviz_config.webviz_store import webvizstore
from webviz_config.common_cache import CACHE

import webviz_4d._datainput.common as common
from webviz_4d._datainput.well import get_well_polyline, load_all_wells


def get_production_type(selection):
    if "production" in selection:
        production_type = "production"
    elif "injection" in selection:
        production_type = "injection"
    else:
        production_type = None

    return production_type


def check_interval(interval):
    """ Flip start and end date if needed """
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
    dates = common.get_dates(interval_4d)

    interval_start = dates[1]
    interval_end = dates[0]

    prod_well_types = ["production", "injection"]

    data = []

    wellbores = wells_df["WELLBORE_NAME"].values
    list_set = set(wellbores)
    # convert the set to the list
    unique_wellbores = list(list_set)

    for wellbore in unique_wellbores:
        status = False
        short_name = None
        md_start = 0
        md_end = None
        top_completion = None
        base_completion = None
        well_fluid = None
        polyline_data = None
        start_date = None
        stop_date = None
        info = None

        well_dataframe = wells_df[wells_df["WELLBORE_NAME"] == wellbore]
        well_metadata = metadata_df[metadata_df["wellbore.true_name"] == wellbore]
        md_start = get_value(well_metadata, "wellbore.top_res_md", "min")
        short_name = get_value(well_metadata, "wellbore.short_name", 0)
        pdm_well_name = get_value(well_metadata, "wellbore.pdm_name", 0)
        top_completion = get_value(well_metadata, "top_completion_md", 0)
        base_completion = get_value(well_metadata, "base_completion_md", 0)
        well_type = get_value(well_metadata, "wellbore.type", 0)
        info = well_type

        if selection in ["reservoir_section", "planned"]:
            polyline_data = get_well_polyline(
                short_name,
                well_dataframe,
                well_type,
                well_fluid,
                info,
                md_start,
                md_end,
                selection,
                colors,
            )
        elif selection == "drilled_wells":
            md_start = 0
            polyline_data = get_well_polyline(
                short_name,
                well_dataframe,
                well_type,
                well_fluid,
                info,
                md_start,
                md_end,
                selection,
                colors,
            )
            status = True

        elif well_type in prod_well_types:  # Production and injection layers
            status = False
            interval = check_interval(interval_4d)

            production_type = get_production_type(selection)

            if "active" in selection:
                interval = ""

            start_dates = []
            stop_dates = []
            volumes = []
            infos = []

            if pdm_well_name:
                for fluid in fluids:
                    start_date, stop_date, volume = extract_production_info(
                        pdm_well_name, prod_data, interval, production_type, fluid
                    )

                    info = get_info(start_date, stop_date, fluid, volume)

                    if volume is not None and volume > 0:
                        start_dates.append(start_date)
                        stop_dates.append(stop_date)
                        volumes.append(volume)
                        infos.append(info)
                        well_fluid = fluid
                        status = True

            if len(start_dates) == 1:  # Single fluid
                start_date = start_dates[0]
                stop_date = stop_dates[0]
                info = infos[0]
            elif len(start_dates) > 1:  # WAG injection
                start_date = min(start_dates)
                stop_date = max(stop_dates)
                info = "WAG injection"
                well_type = "wag_injection"

            if "active" in selection and start_date is not None:
                if isinstance(stop_date, str) and stop_date == "---":
                    status = True
                elif stop_date is None:
                    status = True
                elif isinstance(stop_date, float) and math.isnan(stop_date):
                    status = True
                else:
                    status = False

            if start_date and (
                selection == "production_start" or selection == "injection_start"
            ):
                if start_date >= interval_start and start_date < interval_end:
                    status = True
                else:
                    status = False

            if status and (
                selection == "production_completed"
                or selection == "injection_completed"
            ):

                if top_completion and base_completion:
                    md_start = top_completion
                    md_end = base_completion
                    status = True
                else:
                    status = False

        if status:
            polyline_data = get_well_polyline(
                short_name,
                well_dataframe,
                well_type,
                well_fluid,
                info,
                md_start,
                md_end,
                selection,
                colors,
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

        if math.isnan(volume):
            volume = None
    return start_date, stop_date, volume


def get_info(start_date, stop_date, fluid, volume):
    units = {"oil": "[kSm3]", "water": "[kSm3]", "gas": "[MSm3]"}

    if volume is None or volume == 0:
        return None

    unit = None

    if fluid in units:
        unit = units[fluid]

    if stop_date is None or (not isinstance(stop_date, str) and math.isnan(stop_date)):
        stop_date = "---"

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
