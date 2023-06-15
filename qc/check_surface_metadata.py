import os
from pathlib import Path
import pandas as pd
import argparse
import numpy as np

from webviz_4d._datainput.common import read_config


def get_real_runpath(surface_metadata, data, iteration, real, map_type, interval_mode):
    selected_interval = data["date"]
    name = data["name"]
    attribute = data["attr"]

    if interval_mode == "normal":
        time2 = selected_interval[0:10]
        time1 = selected_interval[11:]
    else:
        time1 = selected_interval[0:10]
        time2 = selected_interval[11:]

    surface_metadata.replace(np.nan, "", inplace=True)

    try:
        selected_metadata = surface_metadata[
            (surface_metadata["fmu_id.realization"] == real)
            & (surface_metadata["fmu_id.iteration"] == iteration)
            & (surface_metadata["map_type"] == map_type)
            & (surface_metadata["data.time.t1"] == time1)
            & (surface_metadata["data.time.t2"] == time2)
            & (surface_metadata["data.name"] == name)
            & (surface_metadata["data.attribute"] == attribute)
        ]

        path = selected_metadata["filename"].values[0]

    except:
        path = ""

    return path


DESCRIPTION = "Check surface metadata"
parser = argparse.ArgumentParser(description=DESCRIPTION)
parser.add_argument("config_file", help="Enter name of config file")
args = parser.parse_args()

config_file = args.config_file
config_file = os.path.abspath(config_file)
config_folder = os.path.dirname(config_file)
config = read_config(config_file)
shared_settings = config.get("shared_settings")

surface_metadata_file = shared_settings.get("surface_metadata_file")
surface_metadata_file = os.path.join(config_folder, surface_metadata_file)
surface_metadata = pd.read_csv(surface_metadata_file)

data = {
    "name": "draupne_fm_1",
    "attr": "amplitude_full_min",
    "date": "2020-10-01-2019-10-01",
}
iteration = "pred"
real = "realization-0"
map_type = "simulated"
interval_mode = "normal"

filepath = get_real_runpath(
    surface_metadata, data, iteration, real, map_type, interval_mode
)

print("Map file:", filepath)
