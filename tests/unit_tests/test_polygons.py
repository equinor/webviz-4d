import os
import json
from pathlib import Path

from webviz_4d.plugins._surface_viewer_4D._webvizstore import (
    find_files,
    get_path,
)
from webviz_4d._datainput.common import (
    read_config,
)

# from webviz_4d._datainput._polygons import (
#     load_zone_polygons,
# )

config_file = "./tests/data/example_config.yaml"
config = read_config(config_file)
config_folder = os.path.dirname(config_file)

shared_settings = config.get("shared_settings")
polygon_settings = shared_settings.get("polygon_layers")
polygon_data = shared_settings.get("polygon_data")
polygon_data = Path(os.path.join(config_folder, polygon_data))

settings_file = shared_settings.get("settings_file")
settings_file = Path(os.path.join(config_folder, settings_file))

settings = read_config(get_path(settings_file))
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
zone_items = {
    0: {"label": "Faults", "tooltip": "topvolantis-faultlines", "color": "gray"},
    1: {"label": "FWL", "tooltip": "topvolantis-outline_fwl", "color": "blue"},
    2: {"label": "GOC", "tooltip": "topvolantis-outline_goc", "color": "red"},
}


# def test_load_zone_polygons():
#     zone_polygon_folder = Path(os.path.join(polygon_data, "zone_polygons"))
#     polygon_files = sorted(
#         [
#             get_path(Path(fn))
#             for fn in json.load(find_files(zone_polygon_folder, ".csv"))
#         ]
#     )

#     polygon_layers = load_zone_polygons(polygon_files, polygon_settings, settings)

#     for index, layer in enumerate(polygon_layers):
#         layer_name = layer.get("name")
#         assert layer_name == zone_items[index].get("label")

#         data = layer.get("data")[0]

#         color = data.get("color")
#         assert color == zone_items[index].get("color")

#         tooltip = data.get("tooltip")
#         assert tooltip == zone_items[index].get("tooltip")
