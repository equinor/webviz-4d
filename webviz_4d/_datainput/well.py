import os
import glob
import json
import numpy
import statistics
import pandas as pd
import yaml
from pandas import json_normalize
import xtgeo

from webviz_config.common_cache import CACHE
from webviz_4d._datainput.common import find_files


def load_well(well_path):
    """ Return a well object (xtgeo) for a given file (RMS ascii format) """
    return xtgeo.Well(well_path, mdlogname="MD")


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
        # print(wellfile)
        well = load_well(wellfile)
        well.downsample()

        # print("    - loaded")

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
    """ Return x- and y-values for a well between given depths """

    well_dataframe = well_dataframe[well_dataframe["MD"] >= md_start]

    if md_end:
        well_dataframe = well_dataframe[well_dataframe["MD"] <= md_end]

    positions = well_dataframe[["X_UTME", "Y_UTMN"]].values

    return positions


def get_well_polyline(
    short_name,
    well_dataframe,
    well_type,
    fluid,
    info,
    md_start,
    md_end,
    selection,
    colors,
):
    """ Create polyline data - well trajectory, color and tooltip """
    # print("get_well_polyline", selection, short_name)

    color = "black"

    if colors:
        color = colors["default"]

    tooltip = str(short_name) + " : " + well_type

    status = False

    if fluid and not pd.isna(fluid):
        tooltip = tooltip + " (" + info + ")"

    if selection:
        if ("reservoir" in selection) and not pd.isna(fluid) and md_start > 0:
            positions = get_position_data(well_dataframe, md_start, md_end)
            status = True

        elif selection == "planned" and well_type == selection:
            if colors:
                color = colors[selection]

            positions = get_position_data(well_dataframe, md_start, md_end)
            status = True

        elif well_type == selection and not pd.isna(fluid) and md_start > 0:
            ind = fluid.find(",")

            if ind > 0:
                fluid = "mixed"

            if colors:
                color = colors[fluid + "_" + selection]

            positions = get_position_data(well_dataframe, md_start, md_end)
            status = True

        elif pd.isna(fluid):
            positions = get_position_data(well_dataframe, md_start, md_end)
            status = True

        elif "active" in selection:
            positions = get_position_data(well_dataframe, md_start, md_end)
            status = True

        elif selection == "production_start" or selection == "production_completed":
            positions = get_position_data(well_dataframe, md_start, md_end)
            color = colors[fluid + "_production"]
            status = True

        elif selection == "injection_start" or selection == "injection_completed":
            positions = get_position_data(well_dataframe, md_start, md_end)
            color = colors[fluid + "_injection"]
            status = True

    else:
        positions = get_position_data(well_dataframe, md_start, md_end)
        status = True

    if status:
        return {
            "type": "polyline",
            "color": color,
            "positions": positions,
            "tooltip": tooltip,
        }
