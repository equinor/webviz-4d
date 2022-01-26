import os
import pandas as pd
import math
import glob
import json
from pathlib import Path

from webviz_config.webviz_store import webvizstore
from webviz_config.common_cache import CACHE

import webviz_4d._datainput.common as common

from webviz_4d.plugins._surface_viewer_4D._webvizstore import (
    read_csv,
    read_csvs,
    find_files,
    get_path,
)


supported_polygons = {
    "owc_outline": "Initial OWC",
    "goc_outline": "Initial GOC",
    "faults": "Faults",
    "prm_receivers": "PRM receivers",
}
default_colors = {
    "owc_outline": "lightslategray",
    "goc_outline": "red",
    "faults": "gray",
    "prm_receivers": "darkgray",
}

checked = {
    "Initial OWC": True,
    "Initial GOC": True,
    "Faults": True,
    "PRM receivers": False,
}

key_list = list(supported_polygons.keys())
val_list = list(supported_polygons.values())


def get_position_data(polyline):
    """Return x- and y-values for a selected polygon"""
    positions_txt = polyline["coordinates"]
    positions = json.loads(positions_txt)

    return positions


def get_fault_polyline(fault, tooltip, color):
    """Create polyline data - fault polylines, color and tooltip"""
    if color is None:
        color = default_colors.get("faults")

    positions = get_position_data(fault)

    if positions:
        return {
            "type": "polyline",
            "color": color,
            "positions": positions,
            "tooltip": tooltip,
        }


def get_prm_polyline(prm, color):
    """Create polyline data - prm receiver polylines, color and tooltip"""
    if color is None:
        color = default_colors.get("prm_receivers")

    positions = get_position_data(prm)
    year = prm["year"]
    line = prm["line"]
    tooltip = str(year) + "-line " + str(line)

    if positions:
        return {
            "type": "polyline",
            "color": color,
            "positions": positions,
            "tooltip": tooltip,
        }


def get_contact_polyline(contact, key, color):
    """Create polyline data - owc polyline, color and tooltip"""
    data = []
    tooltip = supported_polygons[key]
    label = supported_polygons[key]

    coordinates_txt = contact["coordinates"][0]
    coordinates = json.loads(coordinates_txt)

    if color is None:
        position = val_list.index(label)
        key = key_list[position]
        color = default_colors.get(key)

    for i in range(0, len(coordinates)):
        positions = coordinates[i]

        if positions:
            polyline_data = {
                "type": "polyline",
                "color": color,
                "positions": positions,
                "tooltip": tooltip,
            }

            data.append(polyline_data)

    return data


def make_new_polyline_layer(dataframe, key, label, color):
    """Make layeredmap fault layer"""
    data = []
    name = supported_polygons.get(key)

    if "outline" in key:
        data = get_contact_polyline(dataframe, key, color)
    elif key == "prm_receivers":
        for _index, row in dataframe.iterrows():
            polyline_data = get_prm_polyline(row, color)

            if polyline_data:
                data.append(polyline_data)
    else:
        for _index, row in dataframe.iterrows():
            polyline_data = get_fault_polyline(row, label, color)

            if polyline_data:
                data.append(polyline_data)
    # else:
    #     print("WARNING: Unknown polygon type", key)

    if data:
        checked_state = checked.get(name)
        layer = {
            "name": name,
            "checked": checked_state,
            "base_layer": False,
            "data": data,
        }
    else:
        layer = None

    return layer


def load_polygons(csv_files, polygon_colors):
    polygon_layers = []

    for csv_file in csv_files:
        polygon_df = pd.read_csv(csv_file)
        name = polygon_df["name"].unique()[0]
        file_name = os.path.basename(csv_file)

        if name in supported_polygons.keys() or file_name in supported_polygons.keys():
            default_color = default_colors.get(name)

            if polygon_colors:
                color = polygon_colors.get(name, default_color)
            else:
                color = default_color

            polygon_layer = make_new_polyline_layer(polygon_df, name, name, color)
            polygon_layers.append(polygon_layer)

    return polygon_layers


def load_zone_polygons(csv_files, polygon_colors):
    polygon_layers = []

    for csv_file in csv_files:
        polygon_df = pd.read_csv(csv_file)
        label = os.path.basename(csv_file).replace(".csv", "")

        name = "faults"
        default_color = default_colors.get(name)

        if polygon_colors:
            color = polygon_colors.get(name, default_color)
        else:
            color = default_color

        polygon_layer = make_new_polyline_layer(polygon_df, name, label, color)
        polygon_layers.append(polygon_layer)

    return polygon_layers


def get_zone_layer(polygon_layers, zone_name):
    for layer in polygon_layers:
        data = layer["data"]
        tooltip = data[0]["tooltip"]

        if tooltip == zone_name:
            return layer

    return None
