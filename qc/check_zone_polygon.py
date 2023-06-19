import os
from pathlib import Path
import pandas as pd
import argparse
import numpy as np

from webviz_4d.plugins._surface_viewer_4D._webvizstore import get_path
from webviz_4d._datainput._polygons import (
    create_polygon_layer,
    make_new_polyline_layer,
    load_polygons,
)

from webviz_4d._datainput.common import read_config


def create_zone_layer(
    fmu_directory, settings, polygon_mapping_file, iteration, realization, zone
):
    sep = ","
    dtype = None
    layer = None

    default_color = "gray"
    color = settings.get("polygon_colors", default_color)

    if polygon_mapping_file is not None:
        polygon_mapping = pd.read_csv(polygon_mapping_file)

        if zone in polygon_mapping["surface_name"].to_list():
            selected_zone = polygon_mapping[polygon_mapping["surface_name"] == zone]
            polygon_file = selected_zone["polygon_file"].to_numpy()[0]
            print(zone, polygon_file)

            selected_polygon_file = os.path.join(
                fmu_directory,
                realization,
                iteration,
                "share/results/polygons",
                polygon_file,
            )
            selected_polygon_path = get_path(Path(selected_polygon_file))
            print("DEBUG: selected_polygon_path", selected_polygon_path)

            if (
                selected_polygon_path.is_file()
                and selected_polygon_path.suffix == ".pol"
            ):
                sep = " "
                dtype = np.float64

                selected_polygon_df = pd.read_csv(
                    selected_polygon_path, sep=sep, dtype=dtype
                )
                dataframe = create_polygon_layer(selected_polygon_df)

                layer = make_new_polyline_layer(dataframe, zone, "Faults", color)

    return layer


DESCRIPTION = "Check zone layer"
parser = argparse.ArgumentParser(description=DESCRIPTION)
parser.add_argument("config_file", help="Enter name of config file")
args = parser.parse_args()

config_file = args.config_file
config_file = os.path.abspath(config_file)
config_folder = os.path.dirname(config_file)
config = read_config(config_file)
shared_settings = config.get("shared_settings")

fmu_directory = shared_settings.get("fmu_directory")
polygon_mapping_file = shared_settings.get("polygon_mapping_file")
polygon_mapping_file = os.path.join(config_folder, polygon_mapping_file)
iteration = "iter-1"
real = "realization-0"
selected_zone = "sn_10_1"

zone_layer = create_zone_layer(
    fmu_directory, shared_settings, polygon_mapping_file, iteration, real, selected_zone
)

polygon_data = shared_settings.get("polygon_data")
polygon_data = os.path.join(config_folder, polygon_data)

polygon_configuration = shared_settings.get("polygon_layers")

settings_file = shared_settings.get("settings_file")
settings_file = os.path.join(config_folder, settings_file)
settings = read_config(settings_file)
polygon_colors = settings.get("polygon_colors")

polygon_layers = load_polygons(polygon_data, polygon_configuration, polygon_colors)
