import os
import pandas as pd
import re

from webviz_4d._datainput.common import get_dates


def create_map_settings(
    attribute, name, map_type, ensemble, realization, default_interval
):

    map_dict = {
        "attribute": attribute,
        "name": name,
        "map_type": map_type,
        "ensemble": ensemble,
        "realization": realization,
        "interval": default_interval,
    }

    return map_dict


def get_map_defaults(selection_options, default_interval, observations, simulations):
    observed_options = selection_options[observations]
    simulated_options = selection_options[simulations]

    realizations = get_realizations(metadata_df, simulations)
    ensembles = get_ensembles(metadata_df, simulations)

    map_defaults = []

    if observed_options:
        ensemble = observed_options["ensemble"][0]
        realization = observed_options["realization"][0]
        attribute = observed_options["attribute"][0]
        name = observed_options["name"][0]

        map_default = create_map_settings(
            observed_attribute,
            observed_name,
            observations,
            ensemble,
            realization,
            default_interval,
        )
        map_defaults.append(map_default)

        if simulated_options:
            ensemble = simulated_options["ensemble"][0]
            realization = simulated_options["realization"][0]
            attribute = simulated_options["attribute"][0]
            name = simulated_options["name"][0]

            map_default = create_map_settings(
                observed_attribute,
                observed_name,
                observations,
                ensemble,
                realization,
                default_interval,
            )
            map_defaults.append(map_default)
            map_defaults.append(map_default)

    elif simulated_options:
        ensemble = simulated_options["ensemble"][0]
        realization = simulated_options["realization"][0]
        attribute = simulated_options["attribute"][0]
        name = simulated_options["name"][0]

        map_default = create_map_settings(
            observed_attribute,
            observed_name,
            observations,
            ensemble,
            realization,
            default_interval,
        )

        map_default = create_map_settings(
            simulated_attribute,
            simulated_name,
            simulations,
            ensemble,
            realization,
            default_interval,
        )
        map_defaults.append(map_default)
        map_defaults.append(map_default)
        map_defaults.append(map_default)

    return map_defaults


def check_yaml_file(surfacepath):
    mapfile_name = str(surfacepath)

    yaml_file = (
        os.path.dirname(mapfile_name) + "/." + os.path.basename(mapfile_name) + ".yaml"
    )
    status = os.path.isfile(yaml_file)

    return status


def get_all_intervals(meta_df, mode):
    all_intervals_list = []
    incremental_list = []

    interval_df = meta_df[["data.time.t1", "data.time.t2"]]
    new_df = interval_df.drop_duplicates()

    if mode == "reverse":
        all_intervals = new_df.sort_values(
            by=["data.time.t2", "data.time.t1"], ascending=[True, False]
        )
    else:
        all_intervals = new_df.sort_values(
            by=["data.time.t1", "data.time.t2"], ascending=[True, False]
        )

    for _index, row in all_intervals.iterrows():
        if mode == "reverse":
            all_intervals_list.append(row["data.time.t2"] + "-" + row["data.time.t1"])
        else:
            all_intervals_list.append(row["data.time.t1"] + "-" + row["data.time.t2"])

    t1_list = meta_df["data.time.t1"].drop_duplicates().sort_values().tolist()
    t2_list = meta_df["data.time.t2"].drop_duplicates().sort_values().tolist()
    all_list = t1_list + t2_list

    unique_list = list(set(all_list))
    unique_list.sort()

    incremental_list = []

    for i in range(1, len(unique_list)):
        if mode == "reverse":
            interval = unique_list[i] + "-" + unique_list[i - 1]
        else:
            interval = unique_list[i - 1] + "-" + unique_list[i]

        if interval in all_intervals_list:
            incremental_list.append(interval)

    sorted_all_list = incremental_list.copy()
    all_intervals_list.sort()

    for interval in all_intervals_list:
        if interval not in sorted_all_list:
            sorted_all_list.append(interval)

    return sorted_all_list, incremental_list


def unique_values(list_values):
    # clean_list = [value for value in list_values if str(value) != "nan"]
    # list_set = set(clean_list)
    # unique_list = list(list_set)

    return list_values


def get_col_values(dataframe, col_name):
    return unique_values(dataframe[col_name].values)


def get_selected_metadata(metadata_df, surfacepath):
    metadata = None

    try:
        metadata = metadata_df[metadata_df["filename"] == surfacepath]
    except:
        pass

    return metadata


def get_selected_interval(dates, indices):

    if indices[0] > indices[1]:
        difference = "reverse"
    else:
        difference = "normal"

    if difference == "reverse":
        start_date = dates[indices[1] - 1]
        end_date = dates[indices[0] - 1]
    elif difference == "normal":
        start_date = dates[indices[0] - 1]
        end_date = dates[indices[1] - 1]

    return start_date + "_" + end_date


def sort_realizations(realizations):
    numbers = []
    statistics = []
    sorted_list = []

    for realization in realizations:
        if realization in ["std", "mean"]:
            statistics.append(realization)
        else:
            ind = realization.find("-")
            numbers.append(int(realization[ind + 1 :]))

    numbers.sort()

    for number in numbers:
        sorted_list.append("realization-" + str(number))

    for statistic in statistics:
        if statistic not in sorted_list:
            sorted_list.append(statistic)

    return sorted_list


def get_attributes(metadata, map_type):
    attributes = []
    selected_type = metadata.loc[metadata["map_type"] == map_type]

    if not selected_type.empty:
        attribute_list = selected_type["data.content"].values
        attributes = list(set(attribute_list))

    return sorted(attributes)


def get_names(metadata, map_type):
    names = []
    selected_type = metadata.loc[metadata["map_type"] == map_type]

    if not selected_type.empty:
        names_list = selected_type["data.name"].values
        names = list(set(names_list))

    return sorted(names)


def get_realizations(metadata, map_type):
    realizations = []
    selected_type = metadata.loc[metadata["map_type"] == map_type]

    if not selected_type.empty:
        realizations_list = selected_type["fmu_id.realization"].values
        realizations = list(set(realizations_list))

    return sorted(realizations)


def get_ensembles(metadata, map_type):
    ensembles = []
    selected_type = metadata.loc[metadata["map_type"] == map_type]

    if not selected_type.empty:
        ensembles_list = selected_type["fmu_id.ensemble"].values
        ensembles = list(set(ensembles_list))

    return sorted(ensembles)
