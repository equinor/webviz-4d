from typing import List, Tuple, Union, Dict, Callable, Any
import io
from pathlib import Path
import json
import os
import glob
import pandas as pd
import numpy as np
from datetime import datetime

from webviz_config import WebvizPluginABC
from webviz_4d._datainput._surface import make_surface_layer, load_surface
from webviz_4d._datainput.common import (
    read_config,
    get_well_colors,
    get_update_dates,
    get_plot_label,
    get_dates,
)

from webviz_4d._datainput.well import load_all_wells
from webviz_4d._datainput._production import make_new_well_layer

from webviz_4d._private_plugins.surface_selector import SurfaceSelector
from webviz_4d._datainput._colormaps import load_custom_colormaps
from webviz_4d._datainput._polygons import load_polygons

from webviz_4d._datainput._metadata import (
    get_col_values,
    create_map_defaults,
    get_map_defaults,
    sort_realizations,
)

from ._webvizstore import read_csv, read_csvs, find_files, get_path
from ._callbacks import (
    set_first_map,
    set_second_map,
    set_third_map,
    change_maps_from_button,
)
from ._layout import set_layout


class SurfaceViewer4D(WebvizPluginABC):
    """### SurfaceViewer4D """

    def __init__(
        self,
        app,
        wellfolder: Path = None,
        production_data: Path = None,
        polygons_folder: Path = None,
        colormaps_folder: Path = None,
        map1_defaults: dict = None,
        map2_defaults: dict = None,
        map3_defaults: dict = None,
        map_suffix: str = ".gri",
        default_interval: str = None,
        settings: Path = None,
        delimiter: str = "--",
        surface_metadata_file: Path = None,
        attribute_maps_file: Path = None,
        interval_mode: str = "reverse",
        selector_file: Path = None,
    ):

        super().__init__()
        self.shared_settings = app.webviz_settings["shared_settings"]
        self.fmu_directory = self.shared_settings["fmu_directory"]
        self.map_suffix = map_suffix
        self.delimiter = delimiter
        self.interval_mode = interval_mode

        self.number_of_maps = 3
        self.observations = "observed"
        self.simulations = "simulated"
        self.wellsuffix = ".w"

        self.surface_layer = None
        self.well_base_layers = None
        self.attribute_settings = {}
        self.well_update = ""
        self.production_update = ""
        self.selected_names = [None, None, None]
        self.selected_attributes = [None, None, None]
        self.selected_ensembles = [None, None, None]
        self.selected_realizations = [None, None, None]
        self.well_base_layers = []
        self.interval_well_layers = {}

        # Read production data
        self.prod_names = ["BORE_OIL_VOL.csv", "BORE_GI_VOL.csv", "BORE_WI_VOL.csv"]
        self.prod_folder = production_data
        self.prod_data = read_csvs(folder=self.prod_folder, csv_files=self.prod_names)
        print("Reading production data from", self.prod_folder)

        # Read maps metadata
        self.surface_metadata_file = surface_metadata_file
        print("Reading maps metadata from", self.surface_metadata_file)
        self.surface_metadata = (
            read_csv(csv_file=self.surface_metadata_file)
            if self.surface_metadata_file is not None
            else None
        )
        self.selector_file = selector_file
        self.selection_list = read_config(get_path(path=self.selector_file))

        # Read custom colormaps
        self.colormaps_folder = colormaps_folder
        if self.colormaps_folder is not None:
            self.colormap_files = [
                get_path(Path(fn))
                for fn in json.load(find_files(self.colormaps_folder, ".csv"))
            ]
            print("Reading custom colormaps from:", self.colormaps_folder)
            load_custom_colormaps(self.colormap_files)

        # Read attribute maps settings (min-/max-values)
        self.colormap_settings = None
        self.attribute_maps_file = attribute_maps_file
        if self.attribute_maps_file is not None:
            self.colormap_settings = read_csv(csv_file=self.attribute_maps_file)
            print("Colormaps settings loaded from file", self.attribute_maps_file)

        # Read settings
        self.settings = settings
        if self.settings:
            self.config = read_config(get_path(path=self.settings))

            try:
                self.attribute_settings = self.config["map_settings"][
                    "attribute_settings"
                ]
            except:
                pass

        # Read settings (defaults)
        if default_interval is None:
            try:
                default_interval = self.selection_list[self.observations]["interval"][0]
            except:
                try:
                    default_interval = self.selection_list[self.simulations][
                        "interval"
                    ][0]
                except:
                    default_interval = None

        self.map_defaults = []
        self.maps_metadata_list = []

        if map1_defaults is not None:
            map1_defaults["interval"] = default_interval
            self.map_defaults.append(map1_defaults)
            self.map1_options = self.selection_list[map1_defaults["map_type"]]

        if map2_defaults is not None:
            map2_defaults["interval"] = default_interval
            self.map_defaults.append(map2_defaults)
            self.map2_options = self.selection_list[map2_defaults["map_type"]]

        if map3_defaults is not None:
            map3_defaults["interval"] = default_interval
            self.map_defaults.append(map3_defaults)
            self.map2_options = self.selection_list[map2_defaults["map_type"]]

        print("Default interval", default_interval)

        if map1_defaults is None or map2_defaults is None or map3_defaults is None:
            self.map_defaults = get_map_defaults(
                self.selection_list,
                default_interval,
                self.observations,
                self.simulations,
            )
        else:
            self.map_defaults = []
            self.map_defaults.append(map1_defaults)
            self.map_defaults.append(map2_defaults)
            self.map_defaults.append(map3_defaults)

        self.selected_intervals = [default_interval, default_interval, default_interval]

        self.colors = get_well_colors(self.config)

        # Read custom colormaps
        self.polygons_folder = polygons_folder
        self.polygon_layers = None
        if self.polygons_folder is not None:
            self.polygon_files = [
                get_path(Path(fn))
                for fn in json.load(find_files(self.polygons_folder, ".csv"))
            ]
            print("Reading polygons from:", self.polygons_folder)
            self.polygon_layers = load_polygons(self.polygon_files)

        # Read update dates and well data
        #    self.drilled_wells_df: dataframe with wellpaths (x- and y positions) for all drilled wells
        #    self.drilled_wells_info: dataframe with metadata for all drilled wells
        self.wellfolder = wellfolder
        print("Reading well data from", self.wellfolder)

        if self.wellfolder:
            self.wellbore_info = read_csv(
                csv_file=Path(self.wellfolder) / "wellbore_info.csv"
            )
            update_dates = get_update_dates(
                welldata=get_path(Path(self.wellfolder) / ".welldata_update.yaml"),
                productiondata=get_path(
                    Path(self.wellfolder) / ".production_update.yaml"
                ),
            )
            self.well_update = update_dates["well_update_date"]
            self.production_update = update_dates["production_last_date"]
            self.all_wells_info = read_csv(
                csv_file=Path(self.wellfolder) / "wellbore_info.csv"
            )

            self.all_wells_info["file_name"] = self.all_wells_info["file_name"].apply(
                lambda x: get_path(Path(x))
            )
            self.all_wells_df = load_all_wells(self.all_wells_info)
            self.drilled_wells_files = list(
                self.wellbore_info[self.wellbore_info["layer_name"] == "Drilled wells"][
                    "file_name"
                ]
            )
            self.drilled_wells_df = self.all_wells_df.loc[
                self.all_wells_df["layer_name"] == "Drilled wells"
            ]
            self.drilled_wells_info = self.all_wells_info.loc[
                self.all_wells_info["layer_name"] == "Drilled wells"
            ]

            interval = self.selected_intervals[0]

            # Create well layers for the layers that are independent of the selected 4D interval
            if self.drilled_wells_df is not None:
                basic_well_layers = {
                    "drilled_wells": "Drilled wells",
                    "reservoir_section": "Reservoir sections",
                    "active_production": "Active producers",
                    "active_injection": "Active injectors",
                }

                for key, value in basic_well_layers.items():
                    if "production" in key:
                        fluids = ["oil"]
                    elif "injection" in key:
                        fluids = ["gas", "water"]
                    else:
                        fluids = []

                    # print("Creating well layer for", value)
                    well_layer = make_new_well_layer(
                        interval,
                        self.drilled_wells_df,
                        self.drilled_wells_info,
                        self.prod_data,
                        self.colors,
                        selection=key,
                        fluids=fluids,
                        label=value,
                    )

                    if well_layer is not None:
                        self.well_base_layers.append(well_layer)

            # Load wellpaths for planned wells and create planned well layers
            try:
                planned_well_df = self.all_wells_df.loc[
                    self.all_wells_df["layer_name"] != "Drilled wells"
                ]

                planned_well_info = self.all_wells_info.loc[
                    self.all_wells_info["layer_name"] != "Drilled wells"
                ]
            except:
                planned_well_df = None
                planned_well_info = None

            if planned_well_df is not None:
                planned_layers_df = planned_well_info["layer_name"].dropna()
                planned_layers = planned_layers_df.unique()

                for planned_layer in planned_layers:
                    self.well_base_layers.append(
                        make_new_well_layer(
                            self.selected_intervals[0],
                            planned_well_df,
                            planned_well_info,
                            prod_data=None,
                            colors=self.colors,
                            selection="planned",
                            fluids=[],
                            label=planned_layer,
                        )
                    )

            # Create production and injection layers for the default interval
            self.additional_well_layers = {
                "production": "Producers",
                "production_start": "Producers - started",
                "production_completed": "Producers - completed",
                "injection": "Injectors",
                "injection_start": "Injectors -started",
                "injection_completed": "Injectors - completed",
            }

            self.interval_well_layers = self.create_additional_well_layers(interval)

        # Create selectors (attributes, names and dates) for all 3 maps
        self.selector = SurfaceSelector(app, self.selection_list, self.map_defaults[0])
        self.selector2 = SurfaceSelector(app, self.selection_list, self.map_defaults[1])
        self.selector3 = SurfaceSelector(app, self.selection_list, self.map_defaults[2])
        self.set_callbacks(app)

    def add_webvizstore(self) -> List[Tuple[Callable, list]]:
        store_functions: List[Tuple[Callable, list]] = [
            (
                read_csvs,
                [{"folder": self.prod_folder, "csv_files": self.prod_names}],
            )
        ]
        for fn in [
            self.surface_metadata_file,
            self.attribute_maps_file,
        ]:
            if fn is not None:
                store_functions.append(
                    (
                        read_csv,
                        [
                            {"csv_file": fn},
                        ],
                    )
                )
        if self.colormaps_folder is not None:
            store_functions.append(
                (find_files, [{"folder": self.colormaps_folder, "suffix": ".csv"}])
            )
            store_functions.append(
                (get_path, [{"path": fn} for fn in self.colormap_files])
            )
        if self.polygons_folder is not None:
            store_functions.append(
                (find_files, [{"folder": self.polygons_folder, "suffix": ".csv"}])
            )
            store_functions.append(
                (get_path, [{"path": fn} for fn in self.polygon_files])
            )
        if self.selector_file is not None:
            store_functions.append((get_path, [{"path": self.selector_file}]))
        if self.wellfolder is not None:
            store_functions.append(
                (read_csv, [{"csv_file": Path(self.wellfolder) / "wellbore_info.csv"}])
            )
            for fn in list(self.wellbore_info["file_name"]):
                store_functions.append((get_path, [{"path": Path(fn)}]))
            store_functions.append(
                (
                    get_path,
                    [
                        {"path": Path(self.wellfolder) / ".welldata_update.yaml"},
                        {"path": Path(self.wellfolder) / ".production_update.yaml"},
                    ],
                )
            )

        for fn in list(self.surface_metadata["filename"]):
            store_functions.append((get_path, [{"path": Path(fn)}]))

        if self.settings is not None:
            store_functions.append((get_path, [{"path": self.settings}]))
        return store_functions

    def ensembles(self, map_number):
        map_type = self.map_defaults[map_number]["map_type"]
        return self.selection_list[map_type]["ensemble"]

    def realizations(self, map_number):
        map_type = self.map_defaults[map_number]["map_type"]
        return self.selection_list[map_type]["realization"]

    @property
    def layout(self):
        return set_layout(parent=self)

    def get_real_runpath(self, data, ensemble, real, map_type):
        selected_interval = data["date"]
        name = data["name"]
        attribute = data["attr"]

        if self.interval_mode == "reverse":
            time2 = selected_interval[0:10]
            time1 = selected_interval[11:]
        else:
            time1 = selected_interval[0:10]
            time2 = selected_interval[11:]

        try:
            selected_metadata = self.surface_metadata[
                (self.surface_metadata["fmu_id.realization"] == real)
                & (self.surface_metadata["fmu_id.ensemble"] == ensemble)
                & (self.surface_metadata["map_type"] == map_type)
                & (self.surface_metadata["data.time.t1"] == time1)
                & (self.surface_metadata["data.time.t2"] == time2)
                & (self.surface_metadata["data.name"] == name)
                & (self.surface_metadata["data.content"] == attribute)
            ]

            filepath = selected_metadata["filename"].values[0]
            path = get_path(Path(filepath))

        except:
            path = ""

        return path

    def get_heading(self, map_ind, observation_type):
        if self.map_defaults[map_ind]["map_type"] == observation_type:
            txt = "Observed map: "
            info = "-"
        else:
            txt = "Simulated map: "
            info = (
                self.selected_ensembles[map_ind]
                + " "
                + self.selected_realizations[map_ind]
            )

        heading = (
            txt
            + self.selected_attributes[map_ind]
            + " ("
            + self.selected_names[map_ind]
            + ")"
        )

        sim_info = info
        label = get_plot_label(self.config, self.selected_intervals[map_ind])

        return heading, sim_info, label

    def create_selector_lists(self, map_defaults):
        map_type = map_defaults["map_type"]
        map_metadata = self.surface_metadata[
            self.surface_metadata["map_type"] == map_type
        ]

        intervals_df = map_metadata[["data.time.t1", "data.time.t2"]]
        intervals_list = []

        for _index, row in intervals_df.iterrows():
            if self.interval_mode == "reverse":
                interval = row["data.time.t2"] + "-" + row["data.time.t1"]
            else:
                interval = row["data.time.t1"] + "-" + row["data.time.t2"]

            if interval not in intervals_list:
                intervals_list.append(interval)

        return map_metadata, intervals_list

    def create_additional_well_layers(self, interval):
        interval_well_layers = []

        if get_dates(interval)[0] <= self.production_update:
            for key, value in self.additional_well_layers.items():
                layer_name = interval + "_" + key
                #print("Creating well layer for", layer_name)

                if "production" in key:
                    fluids = ["oil"]
                elif "injection" in key:
                    fluids = ["gas", "water"]
                else:
                    fluids = []

                well_layer = make_new_well_layer(
                    interval,
                    self.drilled_wells_df,
                    self.drilled_wells_info,
                    self.prod_data,
                    self.colors,
                    selection=key,
                    fluids=fluids,
                    label=value,
                )

                if well_layer is not None:
                    interval_well_layers.append(well_layer)

        return interval_well_layers

    def make_map(self, data, ensemble, real, attribute_settings, map_idx):
        data = json.loads(data)

        attribute_settings = json.loads(attribute_settings)
        map_type = self.map_defaults[map_idx]["map_type"]

        surface_file = self.get_real_runpath(data, ensemble, real, map_type)

        if os.path.isfile(surface_file):
            surface = load_surface(surface_file)

            if self.colormap_settings is not None:
                m_data = self.colormap_settings.loc[
                    self.colormap_settings["map type"] == map_type
                ]

                a_data = m_data.loc[m_data["attribute"] == data["attr"]]

                interval = data["date"]
                interval = (
                    interval[0:4]
                    + interval[5:7]
                    + interval[8:10]
                    + "_"
                    + interval[11:15]
                    + interval[16:18]
                    + interval[19:21]
                )

                i_data = a_data.loc[a_data["interval"] == interval]
                metadata = i_data[["lower_limit", "upper_limit"]]
            else:
                metadata = None

            surface_layers = [
                make_surface_layer(
                    surface,
                    name=data["attr"],
                    color=attribute_settings.get(data["attr"], {}).get(
                        "color", "inferno"
                    ),
                    min_val=attribute_settings.get(data["attr"], {}).get("min", None),
                    max_val=attribute_settings.get(data["attr"], {}).get("max", None),
                    unit=attribute_settings.get(data["attr"], {}).get("unit", ""),
                    hillshading=False,
                    min_max_df=metadata,
                )
            ]

            for polygon_layer in self.polygon_layers:
                surface_layers.append(polygon_layer)

            if self.well_base_layers:
                for well_layer in self.well_base_layers:
                    surface_layers.append(well_layer)

            interval = data["date"]

            if (
                interval != self.selected_intervals[map_idx]
            ):  # Create new interval layers if selected interval has changesd
                self.interval_well_layers = self.create_additional_well_layers(interval)

            for interval_layer in self.interval_well_layers:
                surface_layers.append(interval_layer)

            self.selected_names[map_idx] = data["name"]
            self.selected_attributes[map_idx] = data["attr"]
            self.selected_ensembles[map_idx] = ensemble
            self.selected_realizations[map_idx] = real
            self.selected_intervals[map_idx] = interval

            heading, sim_info, label = self.get_heading(map_idx, self.observations)
        else:
            print("WARNING: File", surface_file, "doesn't exist")
            heading = "Selected map doesn't exist"
            sim_info = "-"
            surface_layers = []
            label = "-"

        return (
            heading,
            sim_info,
            surface_layers,
            label,
        )

    def set_callbacks(self, app):
        set_first_map(parent=self, app=app)
        set_second_map(parent=self, app=app)
        set_third_map(parent=self, app=app)
        change_maps_from_button(parent=self, app=app)
