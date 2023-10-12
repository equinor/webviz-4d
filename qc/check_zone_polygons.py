import os
import glob
import argparse
import pandas as pd
from typing import Optional

from webviz_4d.plugins._surface_viewer_4D._webvizstore import get_path, read_csv
from webviz_4d._datainput._polygons import (
    load_zone_polygons,
)
from webviz_4d._datainput.common import read_config


def get_polygon_filename(
    fmu_directory: str,
    name: str,
    tagname: str,
    iteration: str,
    realization: str,
    polygon_directory: str,
    mapping_file: Optional[str] = "polygon_mapping_file.csv",
):
    extensions = [".csv", ".pol"]
    file_name = None
    polygon_mapping = pd.DataFrame()

    if os.path.exists(get_path(mapping_file)):
        polygon_mapping = read_csv(get_path(mapping_file))

    for extension in extensions:
        fname = name + "--" + tagname + extension
        file_name = os.path.join(
            fmu_directory,
            realization,
            iteration,
            polygon_directory,
            fname,
        )

        if os.path.exists(file_name):
            return file_name

    if not polygon_mapping.empty:
        mapping = polygon_mapping[
            [polygon_mapping]["surface"]
            == name & [polygon_mapping]["polygon_type"]
            == tagname
        ]

    return file_name


def main():
    DESCRIPTION = "Check zone layer"
    parser = argparse.ArgumentParser(description=DESCRIPTION)
    parser.add_argument("config_file", help="Enter name of config file")
    args = parser.parse_args()

    config_file = args.config_file
    config_file = os.path.abspath(config_file)
    config_folder = os.path.dirname(config_file)
    config = read_config(config_file)
    shared_settings = config.get("shared_settings")

    settings_file = shared_settings.get("settings_file")
    settings_file = os.path.join(config_folder, settings_file)
    settings = read_config(settings_file)

    polygon_config = shared_settings.get("polygon_layers")
    polygon_folder = shared_settings.get("polygon_data")
    polygon_folder = os.path.join(config_folder, polygon_folder)
    zone_folder = os.path.join(polygon_folder, "zone_polygons")

    zone_layer_files = glob.glob(zone_folder + "/*.csv")

    fmu_dir = shared_settings.get("fmu_directory")
    surface_name = "topvolantis"
    tagname = "gl_faultlines_extract_postprocess"
    iteration = "iter-0"
    realization = "realization-0"
    polygon_dir = "share/results/polygons"

    file_name = get_polygon_filename(
        fmu_directory=fmu_dir,
        name=surface_name,
        tagname=tagname,
        iteration=iteration,
        realization=realization,
        polygon_directory=polygon_dir,
    )

    zone_layers = load_zone_polygons(zone_layer_files, polygon_config, settings)

    for layer in zone_layers:
        data = layer.get("data")[0]
        print(layer.get("name"), data.get("tooltip"))


if __name__ == "__main__":
    main()
