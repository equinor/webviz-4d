import os
import pytest

import webviz_4d._datainput.common as common
import webviz_4d._datainput._metadata as metadata


# def test_compose_filename():
#     config_file = "./tests/data/example_config.yaml"
#     config = common.read_config(config_file)

#     shared_settings = config["shared_settings"]

#     real = "realization-0"
#     ensemble = "iter-0"
#     map_type1 = "observed"
#     map_type2 = "simulated"
#     name = "all"
#     attribute = "4d_diff_rms"
#     interval = "2020-10-01-2019-10-01"
#     delimiter = "--"

#     filename1 = metadata.compose_filename(
#         shared_settings, real, ensemble, map_type1, name, attribute, interval, delimiter
#     )

#     filename2 = metadata.compose_filename(
#         shared_settings, real, ensemble, map_type2, name, attribute, interval, delimiter
#     )

#     assert (
#         filename1
#         == "/scratch/example/fmu_case/realization-0/iter-0/share/observations/maps/all--4d_diff_rms--20201001_20191001.gri"
#     )
#     assert (
#         filename2
#         == "/scratch/example/fmu_case/realization-0/iter-0/share/results/maps/all--4d_diff_rms--20201001_20191001.gri"
#     )
