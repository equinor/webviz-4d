import pandas as pd
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

    well_df = well_dataframe[well_dataframe["MD"] >= md_start]

    if md_end:
        well_df = well_df[well_df["MD"] <= md_end]

    if len(well_df) > 20:
        dfr = well_df[::4]
        dfr_append_last = dfr.append(well_df.iloc[-1])

        well_df = dfr_append_last.reset_index(drop=True)

    positions = well_df[["X_UTME", "Y_UTMN"]].values

    return positions


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
