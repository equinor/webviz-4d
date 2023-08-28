import os
import pytest

import webviz_4d._datainput.common as common


config_file = "./tests/data/example_config.yaml"
config = common.read_config(config_file)
config_folder = os.path.dirname(config_file)

settings_file = common.get_config_item(config, "settings")
settings_file = os.path.join(config_folder, settings_file)
settings = common.read_config(settings_file)


def test_read_config():
    well_folder = common.get_config_item(config, "wellfolder")

    assert well_folder == "./well_data"


def test_well_colors():
    colors = common.get_object_colors(settings, "well_colors")

    default = colors["default"]
    oil = colors["oil_production"]

    assert default == "black"
    assert oil == "green"


def test_get_plot_label():
    interval = "2020-10-01-2019-10-01"
    plot_label = common.get_plot_label(settings, interval)
    assert plot_label == "PRM1 - PRM0"

    interval = "2021-10-01-2019-10-01"
    plot_label = common.get_plot_label(settings, interval)
    assert plot_label == "PRM2 - PRM0"
