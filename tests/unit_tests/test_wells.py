import os
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

test_folder = "tests"
data_folder = "data"
well_folder = "well_data"


def test_load_well():
    well_file = "55_33-A-1.w"
    well_file = Path(os.path.join(test_folder, data_folder, well_folder, well_file))

    xtgeo_well_A1 = xtgeo.well_from_file(well_file, mdlogname="MD")
    well_A1 = load_well(well_file)

    assert well_A1.name == xtgeo_well_A1.name


def test_load_all_wells():
    well_file = "55_33-A-1.w"
    well_file = Path(os.path.join(test_folder, data_folder, well_folder, well_file))

    xtgeo_well_A1 = xtgeo.well_from_file(well_file, mdlogname="MD")
    well_A1 = load_well(well_file)

    wellbore_info = "wellbore_info.csv"
    wellbore_info = Path(
        os.path.join(test_folder, data_folder, well_folder, wellbore_info)
    )

    all_wells_info = read_csv(csv_file=wellbore_info)
    all_wells_df = load_all_wells(all_wells_info)

    well_A1_df = all_wells_df[all_wells_df["WELLBORE_NAME"] == "55/33-A-1"]

    assert well_A1.dataframe["X_UTME"].all() == well_A1_df["X_UTME"].all()
