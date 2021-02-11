import os
import pytest

import webviz_4d._datainput.common as common


def test_read_config():
    config_file = "./tests/data/example_config.yaml"
    config = common.read_config(config_file)
    well_folder = common.get_config_item(config, "wellfolder")

    assert well_folder == "./well_data"


def test_get_well_colors():
    config_file = "./tests/data/example_config.yaml"
    config_folder = os.path.dirname(config_file)
    config = common.read_config(config_file)

    settings_file = common.get_config_item(config, "settings")
    settings_file = os.path.join(config_folder, settings_file)
    settings = common.read_config(settings_file)
    colors = common.get_well_colors(settings)

    default = colors["default"]
    oil = colors["oil_production"]

    assert default == "black"
    assert oil == "green"


# def test_get_update_dates():
#     config_file = "./tests/data/example_config.yaml"
#     config_folder = os.path.dirname(config_file)
#     config = common.read_config(config_file)

#     well_folder = common.get_config_item(config, "wellfolder")
#     well_folder = os.path.join(config_folder, well_folder)

#     update_date = common.get_update_dates(well_folder)

#     assert update_date["well_update_date"] == "2020-12-01 16:03:29"
#     assert update_date["production_first_date"] == "2019-10-01"
#     assert update_date["production_last_date"] == "2020-12-01"


def get_plot_label():
    config_file = "./tests/data/example_config.yaml"
    config_folder = os.path.dirname(config_file)
    config = common.read_config(config_file)

    settings_file = common.get_config_item(config, "settings")
    settings_file = os.path.join(config_folder, settings_file)
    settings = common.read_config(settings_file)

    intervals = settings["date_labels"]
    interval = intervals[0]
    label = intervals[interval]

    plot_label = common.get_plot_label(settings, interval)

    assert label == "20191001"
    assert plot_label == label
