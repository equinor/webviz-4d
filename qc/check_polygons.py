import os
import pandas as pd
import argparse
from pathlib import Path

from webviz_4d._datainput.common import read_config
from webviz_4d._datainput._polygons import make_polyline_layer, create_polygon_layer
from webviz_4d._datainput._config import get_polygon_tagnames
from webviz_4d._datainput._polygons import get_polygon_name

top_reservoir = {
    "directory": "share/results",
    "iteration": "pred",
    "realization": "realization-1",
    "maps_directory": "maps/depth",
    "map_name": "draupne_fm_1_js_top",
    "map_tagname": "depth_structural_model",
    "polygons_directory": "polygons",
    "polygon_name": "draupne_fm_1_top",
}

zone_layers = {
    "faults": {"tagname": "fault_lines", "label": "Faults", "format": "csv"},
    "fwl": {"tagname": "field_outline", "label": "Field outline", "format": "csv"},
}

fmu_directory = "/scratch/johan_sverdrup2/share/23p20p0/23p20p0_histandpred_ff_20230917"


def create_zone_polygon(
    zone_polygon, zone_name, realization, iteration, polygon_mapping
):
    print("Wanted zone polygon", zone_name, zone_polygon, realization, iteration)
    layer = {}
    color = None

    tagname = zone_layers.get(zone_polygon).get("tagname")
    label = zone_layers.get(zone_polygon).get("label")
    format = zone_layers.get(zone_polygon).get("format")

    if realization is None and iteration is None:
        realization = top_reservoir.get("realization")
        iteration = top_reservoir.get("iteration")

    polygons_folder = os.path.join(
        fmu_directory,
        realization,
        iteration,
        top_reservoir.get("directory"),
        top_reservoir.get("polygons_directory"),
    )

    name = get_polygon_name(polygon_mapping, zone_name, tagname)

    tooltip = name + "-" + tagname
    polygon_file = name + "--" + tagname + "." + format
    polygon_file = os.path.join(polygons_folder, polygon_file)

    if os.path.exists(polygon_file):
        polygon_df = pd.read_csv(polygon_file)
        layer_df = create_polygon_layer(polygon_df)

        if len(layer_df) > 0:
            layer = make_polyline_layer(
                layer_df,
                format,
                tagname,
                label,
                tooltip,
                color,
            )
            print("Zone_polygon created", layer["name"])

    return layer


def main():
    """Check well layers"""
    description = "Check well layers"
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument("config_file", help="Enter path to the configuration file")

    args = parser.parse_args()
    config_file = args.config_file

    config = read_config(config_file)
    config_file = os.path.abspath(config_file)
    config_folder = os.path.dirname(config_file)
    config_folder = os.path.abspath(config_folder)

    polygon_mapping_file = config.get("shared_settings").get("polygon_mapping_file")
    polygon_mapping_file = os.path.join(config_folder, polygon_mapping_file)

    mapping = pd.read_csv(polygon_mapping_file)
    layers = None

    # Polygons
    default_layers = []
    zone_layers = None
    additional_layers = None

    zone_layers = {
        "faults": {"tagname": "fault_lines", "label": "Faults", "format": "csv"},
        "fwl": {
            "tagname": "field_outline",
            "label": "Field outline",
            "format": "csv} ",
        },
    }

    zone_name = "aasgard_fm"

    # Load default FMU polygons
    if top_reservoir is not None:
        # tagname = zone_layers.get(zone_polygon).get("tagname")

        for zone_polygon in zone_layers:
            layer = create_zone_polygon(zone_polygon, zone_name, None, None, mapping)
            print(layer["name"])

            if layer:
                name = layer["name"]
                data = layer["data"][0]
                tooltip = data["tooltip"]
                color = data["color"]
                print(zone_polygon, name, layer["checked"], color, tooltip)
                default_layers.append(layer)


if __name__ == "__main__":
    main()
