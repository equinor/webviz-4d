import os
import io
import json
import pytest
import pandas as pd
from pathlib import Path

from webviz_4d.plugins._surface_viewer_4D._webvizstore import (
    read_csv,
    find_files,
    get_path,
)
from webviz_4d._datainput.common import (
    read_config,
    get_config_item,
)

from webviz_4d._datainput._polygons import (
    load_polygons,
    load_zone_polygons,
    make_new_polyline_layer,
    get_zone_layer,
)

config_file = "./tests/data/example_config.yaml"
config = read_config(config_file)
config_folder = os.path.dirname(config_file)

settings_file = get_config_item(config, "settings")
settings_file = os.path.join(config_folder, settings_file)
settings_folder = os.path.dirname(settings_file)
settings = read_config(settings_file)

polygon_folder = settings["polygon_data"]
polygon_folder = Path(os.path.join(settings_folder, polygon_folder))
polygon_colors = settings.get("polygon_colors")

fault_layer = {
    "name": "Faults",
    "checked": True,
    "base_layer": False,
}
owc_layer = {
    "name": "Initial OWC",
    "checked": True,
    "base_layer": False,
}
prm_layer = {
    "name": "PRM receivers",
    "checked": False,
    "base_layer": False,
}
zone_layer = {
    "name": "Faults",
    "checked": True,
    "base_layer": False,
}

fault_items = {"tooltip": "faults", "color": "gray"}
owc_items = {"tooltip": "Initial OWC", "color": "lightslategray"}
prm_items = {"tooltip": "2018-line 1", "color": "darkgray"}
zone_items = {"tooltip": "basevolantis", "color": "gray"}


def test_load_polygons():
    polygon_files = [
        get_path(Path(fn)) for fn in json.load(find_files(polygon_folder, ".csv"))
    ]
    polygon_layers = load_polygons(polygon_files, polygon_colors)

    # Fault layers
    layer = polygon_layers[0]

    for key, value in fault_layer.items():
        assert layer[key] == value

    data = layer["data"][0]

    for key, value in fault_items.items():
        assert data[key] == value

    # OWC layer
    layer = polygon_layers[1]

    for key, value in owc_layer.items():
        assert layer[key] == value

    data = layer["data"][0]

    for key, value in owc_items.items():
        assert data[key] == value

    # PRM layer
    layer = polygon_layers[2]

    for key, value in prm_layer.items():
        assert layer[key] == value

    data = layer["data"][0]

    for key, value in prm_items.items():
        assert data[key] == value


def test_load_zone_polygons():
    zone_polygon_folder = Path(os.path.join(polygon_folder, "rms"))
    polygon_files = [
        get_path(Path(fn)) for fn in json.load(find_files(zone_polygon_folder, ".csv"))
    ]

    polygon_layers = load_zone_polygons(polygon_files, polygon_colors)

    # Zone layer
    layer = polygon_layers[0]

    for key, value in zone_layer.items():
        assert layer[key] == value

    data = layer["data"][0]

    for key, value in zone_items.items():
        assert data[key] == value
