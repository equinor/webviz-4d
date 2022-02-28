import os
import pytest
from pathlib import Path
import xtgeo

import webviz_4d._datainput.common as common

from webviz_4d.plugins._surface_viewer_4D._webvizstore import (
    read_csv,
    find_files,
    get_path,
)
from webviz_4d._datainput.well import (
    load_well,
    load_all_wells,
)

config_file = "./tests/data/example_config.yaml"
config = common.read_config(config_file)
config_folder = os.path.dirname(config_file)

settings_file = common.get_config_item(config, "settings")
settings_file = os.path.join(config_folder, settings_file)
settings_folder = os.path.dirname(settings_file)
settings = common.read_config(settings_file)

well_folder = settings["wellfolder"]
well_folder = Path(os.path.join(settings_folder, well_folder))


def test_load_well():
    well_file = "./tests/data/well_data/55_33-A-1.w"

    xtgeo_well_A1 = xtgeo.well_from_file(well_file, mdlogname="MD")
    well_A1 = load_well(well_file)

    assert well_A1.name == xtgeo_well_A1.name


def test_load_all_wells():
    well_file = "./tests/data/well_data/55_33-A-1.w"
    xtgeo_well_A1 = xtgeo.well_from_file(well_file, mdlogname="MD")
    well_A1 = load_well(well_file)

    all_wells_info = read_csv(csv_file=Path(well_folder) / "wellbore_info.csv")
    all_wells_df = load_all_wells(all_wells_info)

    well_A1_df = all_wells_df[all_wells_df["WELLBORE_NAME"] == "55/33-A-1"]

    assert well_A1.dataframe["X_UTME"].all() == well_A1_df["X_UTME"].all()
