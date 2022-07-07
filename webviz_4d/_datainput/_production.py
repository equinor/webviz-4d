import os
import math
import pandas as pd
from pathlib import Path

from webviz_4d._datainput import common
from webviz_4d._datainput.well import get_well_polyline

# from webviz_4d.plugins._surface_viewer_4D._webvizstore import get_path


def get_production_type(selection):
    """Get production type from a selection string"""
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
    """Extract a value from dataframe given the column name name and a mode option:
    - mode = "min" => minimum value in the column
    - mode = int => index of item in the column"""
    try:
        values = metadata_df[item].values

        if isinstance(mode, str) and mode == "min":
            value = min(values)
        elif isinstance(mode, int) and mode < len(values):
            value = values[mode]
        else:
            return None
    except:
        return None

    return value


def get_well_layer_filename(well_data_dir, selection, interval_4d):
    # Get the file name for the selected well well layer

    if "active" in selection or "planned" in selection:
        df_file = "well_layer_" + selection + ".csv"
    elif "prod" in selection or "inj" in selection:
        df_file = "well_layer_" + selection + "_" + interval_4d + ".csv"
    else:
        df_file = "well_layer_" + selection + ".csv"

    df_file = os.path.join(well_data_dir, "well_layers", df_file)

    return df_file


def make_new_well_layer(
    well_layer_file,
    wells_df,
    label="Drilled wells",
):
    """Make layeredmap wells layer"""
    # t0 = time.time()
    data = []

    df_file = well_layer_file

    if os.path.exists(df_file):
        layer_df = pd.read_csv(df_file)
    else:
        layer_df = pd.DataFrame()

    for _index, row in layer_df.iterrows():
        true_name = row["true_name"]
        well_dataframe = wells_df[wells_df["WELLBORE_NAME"] == true_name]

        polyline_data = get_well_polyline(
            well_dataframe,
            row["md_start"],
            row["md_end"],
            row["color"],
            row["tooltip"],
        )

        if polyline_data:
            data.append(polyline_data)

    layer = {"name": label, "checked": False, "base_layer": False, "data": data}

    return layer


def extract_production_info(pdm_well_name, prod_data, interval, production_type, fluid):
    """Return well and production information/status for a selected
    interval for production/injection wells"""

    start_date = None
    stop_date = None
    interval_volume = None
    total_volume = None

    headers = prod_data.columns
    first_date = common.get_dates(headers[5])[0]
    try:
        prod_info = prod_data.loc[
            (prod_data["PDM well name"] == pdm_well_name)
            & (prod_data["Production type"] == production_type)
            & (prod_data["Fluid"] == fluid)
        ]

        well_prod_info = prod_info.where(prod_info.notnull(), None)

        start_date = well_prod_info["Start date"].values[0]
        stop_date = well_prod_info["Last date"].values[0]
    except:
        well_prod_info = pd.DataFrame()

    if not well_prod_info.empty:
        total_volume = well_prod_info.iloc[:, -1:].values[0][0]

    if interval != "" and not well_prod_info.empty:
        dates = common.get_dates(interval)

        if dates[0] == first_date:
            column = interval
            interval_volume = well_prod_info[column].values[0]
        else:
            column1 = first_date + "-" + dates[0]
            column2 = first_date + "-" + dates[1]
            interval_volume = (
                well_prod_info[column2].values[0] - well_prod_info[column1].values[0]
            )

        if math.isnan(interval_volume) or interval_volume == 0:
            interval_volume = None

    return start_date, stop_date, interval_volume, total_volume


def get_info(start_date, stop_date, fluid, volume):
    """Create information string for production/injection wells"""
    units = {"oil": "[kSm3]", "water": "[km3]", "gas": "[MSm3]"}

    if volume is None or volume == 0:
        return None

    unit = units.get(fluid)

    if stop_date is None or (not isinstance(stop_date, str) and math.isnan(stop_date)):
        stop_date_txt = "---"
    else:
        stop_date_txt = stop_date[:4]

    if fluid == "wag":
        info = "(WAG) Start: " + str(start_date[:4]) + " Last: " + str(stop_date_txt)
    else:
        info = (
            fluid
            + " {:.0f} ".format(volume)
            + unit
            + " Start: "
            + str(start_date[:4])
            + " Last: "
            + str(stop_date_txt)
        )

    return info


def check_interval_date(interval, selected_date):
    """Check if a selected date is included in a 4D interval or not"""
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
