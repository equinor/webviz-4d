import os
from pathlib import Path
import pandas as pd
import argparse
import numpy as np

from webviz_4d._datainput.common import read_config


def get_real_runpath(surface_metadata, data, ensemble, real, map_type, interval_mode):
    selected_interval = data["date"]
    name = data["name"]
    attribute = data["attr"]

    if interval_mode == "reverse":
        time2 = selected_interval[0:10]
        time1 = selected_interval[11:]
    else:
        time1 = selected_interval[0:10]
        time2 = selected_interval[11:]

    surface_metadata.replace(np.nan, "", inplace=True)

    try:
        selected_metadata = surface_metadata[
            (surface_metadata["fmu_id.realization"] == real)
            & (surface_metadata["fmu_id.ensemble"] == ensemble)
            & (surface_metadata["map_type"] == map_type)
            & (surface_metadata["data.time.t1"] == time1)
            & (surface_metadata["data.time.t2"] == time2)
            & (surface_metadata["data.name"] == name)
            & (surface_metadata["data.content"] == attribute)
        ]

        path = selected_metadata["filename"].values[0]

    except:
        path = ""

    return path


DESCRIPTION = "Check surface metadata"
parser = argparse.ArgumentParser(description=DESCRIPTION)
parser.add_argument("settings_file", help="Enter name of settings file")
args = parser.parse_args()

settings_file = args.settings_file
settings_file = os.path.abspath(settings_file)
settings_folder = os.path.dirname(settings_file)
settings = read_config(settings_file)
settings_folder = os.path.dirname(settings_file)

map_settings = settings.get("map_settings")
surface_metadata_file = map_settings.get("surface_metadata_file")
surface_metadata_file = os.path.join(settings_folder, surface_metadata_file)
surface_metadata = pd.read_csv(surface_metadata_file)

data = {
    "name": "draupne_fm_1",
    "attr": "4d_depth_max",
    "date": "2020-10-01-2019-10-01",
}
ensemble = ""
real = "p10"
map_type = "simulated"
interval_mode = "reverse"

filepath = get_real_runpath(
    surface_metadata, data, ensemble, real, map_type, interval_mode
)

print("Map file:", filepath)
