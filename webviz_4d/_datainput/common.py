"""Collection of some functions used by the 4D viewer or data preparation scripts"""

import io
import numpy as np
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


def get_object_colors(settings, object_type):
    """Return object colors from settings if existing"""

    well_colors = {
        "default": "black",
        "oil_production": "green",
        "gas_production": "salmon",
        "gas_injection": "red",
        "water_injection": "cyan",
        "wag_injection": "gold",
        "planned": "purple",
    }

    polygon_colors = {
        "default": "gray",
        "owc_outline": "lightslategray",
        "goc_outline": "red",
        "faults": "gray",
        "prm_receivers": "darkgray",
        "4D_undershoot": "salmon",
        "injectites": "khaki",
    }

    object_colors = {"polygon_colors": polygon_colors, "well_colors": well_colors}

    if object_type in object_colors.keys():
        if settings is not None and object_type in settings.keys():
            colors = settings[object_type]
        else:
            colors = object_colors[object_type]
    else:
        colors = None

    return colors


def get_last_date(selection_list):
    observed_items = selection_list.get("observed")

    if observed_items is not None:
        observed_intervals = observed_items.get("interval")

        observed_dates = []
        for interval in observed_intervals:
            dates = get_dates(interval)
            observed_dates.append(dates[0])
            observed_dates.append(dates[1])

        last_date = max(observed_dates)
    else:
        last_date = None

    return last_date


def get_map_min_max(surface, attribute_settings, data):
    if attribute_settings:
        min_val = attribute_settings.get(data["attr"], {}).get("min", None)
        max_val = attribute_settings.get(data["attr"], {}).get("max", None)
    else:
        x, y, z = surface.get_xyz_values1d(activeonly=True)
        max_val = np.percentile(z, 100)
        min_val = -max_val

    return min_val, max_val


def get_realization_status(realizations):
    # Check if the configuration contains only realizations, only aggregations
    # or both
    status = []

    for realization in realizations:
        if "realization" in realization:
            status.append("realizations")

        if "p50" in realizations:
            status.append("aggregations")

    return status
