import pandas as pd
import math
import numpy as np
import xtgeo


def load_well(well_path):
    """Return a well object (xtgeo) for a given file (RMS ascii format)"""
    return xtgeo.well_from_file(well_path, mdlogname="MD")


def load_all_wells(metadata):
    """For all wells in a folder return
    - a list of dataframes with the well trajectories
    - dataframe with metadata for all the wells"""

    all_wells_list = []

    try:
        wellfiles = metadata["file_name"]
        wellfiles.dropna(inplace=True)
    except:
        wellfiles = []
        raise Exception("No wellfiles found")

    for wellfile in wellfiles:
        well = load_well(wellfile)

        well.dataframe = well.dataframe[["X_UTME", "Y_UTMN", "Z_TVDSS", "MD"]]
        well_metadata = metadata.loc[metadata["wellbore.rms_name"] == well.wellname]
        layer_name = well_metadata["layer_name"].values[0]

        if layer_name == "Drilled wells":
            well.dataframe["WELLBORE_NAME"] = well.truewellname
            short_name = well.shortwellname
        else:
            well.dataframe["WELLBORE_NAME"] = well.wellname
            short_name = well.wellname

        well_info = metadata.loc[metadata["wellbore.short_name"] == short_name]
        layer_name = well_info["layer_name"].values[0]
        well.dataframe["layer_name"] = layer_name

        all_wells_list.append(well.dataframe)

    all_wells_df = pd.concat(all_wells_list)
    return all_wells_df


def get_position_data(well_dataframe, md_start, md_end):
    """Return x- and y-values for a well between given depths"""
    delta = 200
    positions = [[]]

    if not math.isnan(md_start):
        well_df = well_dataframe[well_dataframe["MD"] >= md_start]
        resampled_df = resample_well(well_df, md_start, md_end, delta)
        positions = resampled_df[["X_UTME", "Y_UTMN"]].values

    return positions


def resample_well(well_df, md_start, md_end, delta):
    # Resample well trajectory by selecting only positions with a lateral distance larger than the given delta value
    if math.isnan(md_end):
        md_end = well_df["MD"].iloc[-1]

    dfr = well_df[(well_df["MD"] >= md_start) & (well_df["MD"] <= md_end)]

    x = dfr["X_UTME"].values
    y = dfr["Y_UTMN"].values
    tvd = dfr["Z_TVDSS"].values
    md = dfr["MD"].values

    x_new = [x[0]]
    y_new = [y[0]]
    tvd_new = [tvd[0]]
    md_new = [md[0]]
    j = 0

    for i in range(1, len(x)):
        dist = ((x[i] - x[j]) ** 2 + (y[i] - y[j]) ** 2) ** 0.5
        # print(i, j, md[i], dist)

        if dist > delta:
            x_new.append(x[i])
            y_new.append(y[i])
            tvd_new.append(tvd[i])
            md_new.append(md[i])
            j = i

    x_new.append(x[-1])
    y_new.append(y[-1])
    tvd_new.append(tvd[-1])
    md_new.append(md[-1])

    dfr_new = pd.DataFrame()
    dfr_new["X_UTME"] = x_new
    dfr_new["Y_UTMN"] = y_new
    dfr_new["Z_TVDSS"] = tvd_new
    dfr_new["MD"] = md_new

    return dfr_new


def get_well_polyline(
    well_dataframe,
    md_start,
    md_end,
    color,
    tooltip,
):
    """Create polyline data - contains well trajectory, color and tooltip"""

    positions = get_position_data(well_dataframe, md_start, md_end)

    return {
        "type": "polyline",
        "color": color,
        "positions": positions,
        "tooltip": tooltip,
    }
