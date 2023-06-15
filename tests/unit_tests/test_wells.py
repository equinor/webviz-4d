import os
import os
import pytest
from pathlib import Path
import xtgeo
import numpy as np

from webviz_4d.plugins._surface_viewer_4D._webvizstore import (
    read_csv,
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
    well_name = "55/33-A-4"
    well_file = well_name.replace("/", "_") + ".w"
    well_file = Path(os.path.join(test_folder, data_folder, well_folder, well_file))

    well = load_well(well_file)

    wellbore_info = "wellbore_info.csv"
    wellbore_info = Path(
        os.path.join(test_folder, data_folder, well_folder, wellbore_info)
    )

    all_wells_info = read_csv(csv_file=wellbore_info)

    # Test without resampling (delta = 0)
    delta = 0
    all_wells_df = load_all_wells(all_wells_info, delta)

    well_df = all_wells_df[all_wells_df["WELLBORE_NAME"] == well_name]
    assert np.allclose(well.dataframe["X_UTME"].to_list(), well_df["X_UTME"].to_list())

    # Test with resampling to 40 m MD
    well_file = well_name.replace("/", "_") + "_resampled.w"
    well_file = Path(os.path.join(test_folder, data_folder, well_folder, well_file))

    well = load_well(well_file)

    delta = 40
    all_wells_df = load_all_wells(all_wells_info, delta)

    well_df = all_wells_df[all_wells_df["WELLBORE_NAME"] == well_name]
    assert np.allclose(well.dataframe["MD"].to_list(), well_df["MD"].to_list())
