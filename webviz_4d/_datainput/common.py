""" Collection of some functions used by the 4D viewer or data preparation scripts """

import os
import io
from pathlib import Path
import json
import yaml


defaults = {
    "well_suffix": ".w",
    "map_suffix": ".gri",
    "delimiter": "--",
    "surface_metadata": "surface_metadata.csv",
}


def read_config(config_file):
    """Return the content of a configuration file as a dict"""
    config_dict = {}

    with open(config_file, "r") as stream:
        config_dict = yaml.safe_load(stream)

    return config_dict


def get_config_item(config, key):
    """Get the value of a SurfaceViewer4D key"""
    value = None

    pages = config["pages"]

    for page in pages:
        content = page["content"]

        try:
            surface_viewer4d = content[0]["SurfaceViewer4D"]
            value = surface_viewer4d[key]
            return value
        except:
            try:
                value = defaults[key]
            except:
                pass
    return value


def get_dates(interval):
    date1 = interval[0:10]
    date2 = interval[11:21]

    return date1, date2


def get_interval(date_string):
    date_string.replace("-", "")
    interval = date_string[0:8] + "_" + date_string[8:]

    return interval


def find_files(folder, suffix) -> io.BytesIO:
    """Return a sorted list of all files in a folder with a specified suffix"""
    return io.BytesIO(
        json.dumps(
            sorted([str(filename) for filename in Path(folder).glob(f"*{suffix}")])
        ).encode()
    )


def convert_date(date):
    """Convert between dates with or without hyphen"""
    date_string = date

    if len(date) == 8:
        date_string = date[0:4] + "-" + date[4:6] + "-" + date[6:8]

    if "-" in date:
        date_string = date[0:4] + date[5:7] + date[8:10]

    return date_string


def get_update_dates(welldata, productiondata):
    update_dates = {}

    try:
        with open(welldata, "r") as stream:
            well_meta_data = yaml.safe_load(stream)

        well_update = well_meta_data[0]["welldata"]["update_time"]
        update_dates["well_update_date"] = well_update.strftime("%Y-%m-%d")
    except:
        update_dates["well_update_date"] = ""
    try:
        with open(productiondata, "r") as stream:
            production_meta_data = yaml.safe_load(stream)
        first_date = production_meta_data[0]["production"]["start_date"].strftime(
            "%Y-%m-%d"
        )
        last_date = production_meta_data[0]["production"]["last_date"].strftime(
            "%Y-%m-%d"
        )
        update_dates["production_first_date"] = first_date
        update_dates["production_last_date"] = last_date
    except:
        update_dates["production_first_date"] = ""
        update_dates["production_last_date"] = ""

    return update_dates


def get_position_data(well_dataframe, md_start):
    """Return x- and y-values for a well after a given depth"""
    well_dataframe = well_dataframe[well_dataframe["MD"] > md_start]
    positions = well_dataframe[["X_UTME", "Y_UTMN"]].values

    return positions


def get_plot_label(configuration, interval):
    difference_mode = "normal"
    labels = []

    dates = [
        interval[:4] + interval[5:7] + interval[8:10],
        interval[11:15] + interval[16:18] + interval[19:21],
    ]

    for date in dates:
        # date = convert_date(date)
        try:
            labels_dict = configuration["date_labels"]
            label = labels_dict[int(date)]
        except:
            label = date[:4] + "-" + date[4:6] + "-" + date[6:8]

        labels.append(label)

    if difference_mode == "normal":
        label = str(labels[0]) + " - " + str(labels[1])
    else:
        label = str(labels[1]) + " - " + str(labels[0])

    return label


def get_well_colors(settings):
    """Return well colors from a configuration"""

    return settings["well_colors"]


def get_colormap(configuration, attribute):
    colormap = None
    minval = None
    maxval = None

    try:
        attribute_dict = configuration[attribute]
        # print("attribute_dict", attribute_dict)
        colormap = attribute_dict["colormap"]
        minval = attribute_dict["min_value"]
        minval = attribute_dict["max_value"]
    except:
        try:
            map_settings = configuration("map_settings")
            colormap = map_settings("default_colormap")
        except:
            print("No default colormaps found for ", attribute)

    return colormap, minval, maxval
