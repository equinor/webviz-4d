import os
import pandas as pd
import math
import glob
import json

from webviz_config.webviz_store import webvizstore
from webviz_config.common_cache import CACHE

import webviz_4d._datainput.common as common


def get_fault_position_data(polyline):
    """Return x- and y-values for a selected polygon"""

    positions_txt = polyline["coordinates"]
    positions = json.loads(positions_txt)

    return positions


def get_fault_polyline(fault):
    """Extract polyline data - fault polylines, color and tooltip"""
    color = "white"

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


def get_owc_polyline(contact):
    """Extract polyline data - owc polyline, color and tooltip"""
    color = "darkgray"
    data = []
    tooltip = "Initial OWC"

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


def make_new_polyline_layer(dataframe, label):
    """Make layeredmap fault layer"""
    data = []

    if label == "Faults":
        for _index, row in dataframe.iterrows():
            polyline_data = get_fault_polyline(row)

            if polyline_data:
                data.append(polyline_data)
    elif label == "OWC":
        data = get_owc_polyline(dataframe)

    if data:
        layer = {"name": label, "checked": True, "base_layer": False, "data": data}
    else:
        layer = None

    return layer


def load_polygons(csv_files):
    polygon_layers = []

    supported_polygons = {"owc_outline": "OWC", "faults": "Faults"}

    for csv_file in csv_files:
        polygon_df = pd.read_csv(csv_file)
        name = polygon_df["name"].unique()[0]
        if name in supported_polygons.keys():

            label = supported_polygons[name]

            polygon_layer = make_new_polyline_layer(polygon_df, label)
            polygon_layers.append(polygon_layer)

    return polygon_layers
