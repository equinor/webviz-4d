import os
import pandas as pd
import math
import glob
import json

from webviz_config.webviz_store import webvizstore
from webviz_config.common_cache import CACHE

import webviz_4d._datainput.common as common


supported_polygons = {"owc_outline": "OWC", "goc_outline": "GOC", "faults": "Faults"}
default_colors = {"owc_outline": "darkgray", "goc_outline": "red", "faults": "white"}
contact_tooltips = {"OWC": "Initial OWC", "GOC": "Initial GOC"}


def get_fault_position_data(polyline):
    """Return x- and y-values for a selected polygon"""

    positions_txt = polyline["coordinates"]
    positions = json.loads(positions_txt)

    return positions


def get_fault_polyline(fault, color):
    """Create polyline data - fault polylines, color and tooltip"""

    """ Extract polyline data - fault polyline, color and tooltip """

    tooltip = "SEG I.D. " + str(fault["SEG I.D."])

    positions = get_fault_position_data(fault)

    if positions:
        return {
            "type": "polyline",
            "color": color,
            "positions": positions,
            "tooltip": tooltip,
        }


def get_contact_polyline(contact, label, color):
    """Create polyline data - owc polyline, color and tooltip"""
    data = []
    tooltip = contact_tooltips[label]

    coordinates_txt = contact["coordinates"][0]
    coordinates = json.loads(coordinates_txt)

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


def make_new_polyline_layer(dataframe, label, color):
    """Make layeredmap fault layer"""
    data = []

    if label == "Faults":
        for _index, row in dataframe.iterrows():
            polyline_data = get_fault_polyline(row, color)

            if polyline_data:
                data.append(polyline_data)
    elif label in contact_tooltips.keys():
        data = get_contact_polyline(dataframe, label, color)

    if data:
        layer = {"name": label, "checked": True, "base_layer": False, "data": data}
    else:
        layer = None

    return layer


def load_polygons(csv_files, polygon_colors):
    polygon_layers = []

    for csv_file in csv_files:
        polygon_df = pd.read_csv(csv_file)
        name = polygon_df["name"].unique()[0]
        if name in supported_polygons.keys():

            label = supported_polygons.get(name)
            default_color = default_colors.get(name)

            if polygon_colors:
                color = polygon_colors.get(name, default_color)
            else:
                color = default_color

            polygon_layer = make_new_polyline_layer(polygon_df, label, color)
            polygon_layers.append(polygon_layer)

    return polygon_layers
