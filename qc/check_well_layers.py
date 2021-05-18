import os
from pathlib import Path
import argparse

from webviz_4d._datainput._production import make_new_well_layer
from webviz_4d.plugins._surface_viewer_4D._webvizstore import (
    read_csv,
    read_csvs,
    get_path,
)
from webviz_4d._datainput.common import (
    read_config,
)

from webviz_4d._datainput.well import load_all_wells


DESCRIPTION = "Create information about the well layers in WebViz-4D"
parser = argparse.ArgumentParser(description=DESCRIPTION)
parser.add_argument("settings_file", help="Enter name of settings file")
parser.add_argument("interval", help="Enter wanted 4D interval")
args = parser.parse_args()

settings_file = args.settings_file
settings_file = os.path.abspath(settings_file)
settings_folder = os.path.dirname(settings_file)
settings = read_config(settings_file)

interval = args.interval

well_folder = settings["well_data"]
well_folder = os.path.join(settings_folder, well_folder)

# Read production data
prod_folder = settings["production_data"]
prod_folder = os.path.join(settings_folder, prod_folder)
prod_names = ["BORE_OIL_VOL.csv", "BORE_GI_VOL.csv", "BORE_WI_VOL.csv"]
prod_data = read_csvs(folder=prod_folder, csv_files=prod_names)
print("Reading production data from", prod_folder)
print(prod_data)

print("Reading well data from", well_folder)

if well_folder:
    all_wells_info = read_csv(csv_file=Path(well_folder) / "wellbore_info.csv")

    all_wells_info["file_name"] = all_wells_info["file_name"].apply(
        lambda x: get_path(Path(x))
    )
    all_wells_df = load_all_wells(all_wells_info)
    drilled_wells_files = list(
        all_wells_info[all_wells_info["layer_name"] == "Drilled wells"]["file_name"]
    )
    drilled_wells_df = all_wells_df.loc[all_wells_df["layer_name"] == "Drilled wells"]
    drilled_wells_info = all_wells_info.loc[
        all_wells_info["layer_name"] == "Drilled wells"
    ]
    drilled_wells_df.sort_values(by=["WELLBORE_NAME"], inplace=True)

    planned_wells_info = all_wells_info.loc[
        all_wells_info["wellbore.type"] == "planned"
    ]

    if planned_wells_info is not None:
        planned_well_layers = planned_wells_info["layer_name"].unique()
    else:
        planned_well_layers = []

well_colors = {
    "default": "black",
    "oil_open": "lime",
    "oil_production": "green",
    "gas_open": "salmon",
    "gas_production": "magenta",
    "gas_injection": "red",
    "water_injection": "blue",
    "wag_injection": "blueviolet",
    "planned": "purple",
}

drilled_well_layers = {
    "drilled_wells": "Drilled wells",
    "reservoir_section": "Reservoir sections",
    "active_production": "Active producers",
    "active_injection": "Active injectors",
    "production": "Producers",
    "production_start": "Producers - started",
    "production_completed": "Producers - completed",
    "injection": "Injectors",
    "injection_start": "Injectors -started",
    "injection_completed": "Injectors - completed",
}


fluids_dict = {
    "production": ["oil"],
    "active_production": ["oil"],
    "production_start": ["oil"],
    "production_completed": ["oil"],
    "injection": ["gas", "water"],
    "active_injection": ["gas", "water"],
    "injection_start": ["gas", "water"],
    "injection_completed": ["gas", "water"],
    "planned": [],
}

for key in drilled_well_layers:
    selection = key
    value = drilled_well_layers[key]

    if "production" in selection or "injection" in selection:
        fluids = fluids_dict[selection]
    else:
        fluids = []

    print("\n" + selection, interval, fluids)

    well_layer = make_new_well_layer(
        interval,
        all_wells_df,
        drilled_wells_info,
        prod_data,
        well_colors,
        selection=selection,
        fluids=fluids,
        label=value,
    )

    data = well_layer["data"]

    index = 1
    for item in data:
        print(index, item["tooltip"], item["color"])
        index = index + 1

SELECTION = "planned"
fluids = []

for key in planned_well_layers:
    value = key

    print("\n" + SELECTION, value)

    well_layer = make_new_well_layer(
        interval,
        all_wells_df,
        planned_wells_info,
        prod_data,
        well_colors,
        selection=SELECTION,
        fluids=fluids,
        label=value,
    )

    data = well_layer["data"]

    index = 1
    for item in data:
        print(index, item["tooltip"], item["color"])
        index = index + 1
