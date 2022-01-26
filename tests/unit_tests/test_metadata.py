import os
import pytest
import pandas as pd
import webviz_4d._datainput._metadata as metadata

realizations = ["realization-0", "realization-1", "realization-1"]
ensembles = ["iter-0", "iter-0", "iter-1"]
map_types = ["observed", "simulated", "simulated"]
names = ["all", "zone1", "zone2"]
attributes = ["4d_diff_rms", "4d_diff_min", "4d_diff_max"]
statistics = ["", "", "mean"]
time1 = ["2018-10-01", "2019-10-01", "2020-10-01"]
time2 = ["2019-10-01", "2020-10-01", "2021-10-01"]

meta_df = pd.DataFrame()
meta_df["fmu_id.realization"] = realizations
meta_df["fmu_id.ensemble"] = ensembles
meta_df["map_type"] = map_types
meta_df["data.name"] = names
meta_df["content"] = attributes
meta_df["data.time.t1"] = time1
meta_df["data.time.t2"] = time2
meta_df["statistics"] = statistics

folder = "/test"
ext = ".gri"
filenames = []

for i in range(0, len(realizations)):
    filename = (
        folder
        + "/"
        + realizations[i]
        + "/"
        + ensembles[i]
        + "/share/observations/maps/"
        + names[i]
        + "--"
        + attributes[i]
        + "--"
        + time1[i].replace("-", "")
        + "_"
        + time2[i].replace("-", "")
        + ext
    )
    filenames.append(filename)
    print(filename)

meta_df["filename"] = filenames


def test_get_metadata():
    ens = metadata.get_ensembles(meta_df, "observed")
    assert ens == ["iter-0"]

    ens = metadata.get_ensembles(meta_df, "simulated")
    assert ens == ["iter-0", "iter-1"]
