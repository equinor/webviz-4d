import os
import io
import json
import pandas as pd
from pathlib import Path
import argparse

import webviz_4d._datainput._polygons
from webviz_4d.plugins._surface_viewer_4D._webvizstore import (
    read_csv,
    read_csvs,
    get_path,
)
from webviz_4d._datainput.common import (
    read_config,
)

from webviz_4d._datainput._polygons import (
    load_polygons,
    load_zone_polygons,
    make_new_polyline_layer,
    get_zone_layer,
)

from webviz_4d.plugins._surface_viewer_4D._webvizstore import (
    read_csv,
    read_csvs,
    find_files,
    get_path,
)


DESCRIPTION = "Check the polygon files"
parser = argparse.ArgumentParser(description=DESCRIPTION)
parser.add_argument("settings_file", help="Enter name of settings file")
args = parser.parse_args()

settings_file = args.settings_file
settings_file = os.path.abspath(settings_file)
settings_folder = os.path.dirname(settings_file)
settings = read_config(settings_file)

polygon_folder = settings["polygon_data"]
polygon_folder = Path(os.path.join(settings_folder, polygon_folder))

polygon_colors = settings.get("polygon_colors")

# Read polygon data
polygon_files = [
    get_path(Path(fn)) for fn in json.load(find_files(polygon_folder, ".csv"))
]
print("Reading polygons from:", polygon_folder)
polygon_layers = load_polygons(polygon_files, polygon_colors)

ind = 0
for layer in polygon_layers:
    print("Layer:", ind)
    data = layer["data"]

    index = 1
    for item in data:
        print(index, item["tooltip"], item["color"])
        index = index + 1

    ind = ind + 1
    print("")

# Read zone polygons if existing
zone_faults_folder = Path(os.path.join(polygon_folder, "rms"))

zone_faults_files = [
    get_path(Path(fn)) for fn in json.load(find_files(zone_faults_folder, ".csv"))
]

print("Reading polygons from:", zone_faults_folder)
polygon_layers = load_zone_polygons(zone_faults_files, polygon_colors)

zones = ["ile6_3", "tilje34_33", "dummy"]

for zone in zones:
    layer = get_zone_layer(polygon_layers, zone)

    if layer:
        print("Zone", zone, "found")
    else:
        print("Zone", zone, "not found")
