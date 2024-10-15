from typing import List, Tuple, Callable
from pathlib import Path
import json
import os
import numpy as np
import pandas as pd

from webviz_config import WebvizPluginABC
from webviz_4d._datainput._surface import make_surface_layer, load_surface
from webviz_4d._datainput.common import (
    read_config,
    get_update_dates,
    get_plot_label,
    get_dates,
    get_last_date,
    get_map_min_max,
)
from webviz_4d._datainput.well import load_all_wells
from webviz_4d._datainput._production import make_new_well_layer
from webviz_4d._private_plugins.surface_selector import SurfaceSelector
from webviz_4d._datainput._colormaps import load_custom_colormaps
from webviz_4d._datainput._config import get_basic_well_layers
from webviz_4d._datainput._settings import get_color
from webviz_4d._datainput._polygons import (
    make_polyline_layer,
    get_polygon_name,
    get_polygon_files,
    get_default_polygon_files,
)
from webviz_4d._datainput._metadata import define_map_defaults
from ._webvizstore import read_csv, read_csvs, find_files, get_path
from ._callbacks import (
    set_first_map,
    set_second_map,
    set_third_map,
    change_maps_from_button,
)
from ._layout import set_layout


class SurfaceViewer4D(WebvizPluginABC):
    """### SurfaceViewer4D"""

    def __init__(
        self,
        app,
        well_data: Path = None,
        production_data: Path = None,
        polygon_data: Path = None,
        polygon_mapping_file: Path = None,
        colormap_data: Path = None,
        map1_defaults: dict = None,
        map2_defaults: dict = None,
        map3_defaults: dict = None,
        map_suffix: str = ".gri",
        settings_file: Path = None,
        surface_metadata_file: Path = None,
        surface_scaling_file: Path = None,
        interval_mode: str = "normal",
        selector_file: Path = None,
    ):
        super().__init__()
        self.shared_settings = app.webviz_settings.get("shared_settings")
        self.fmu_directory = self.shared_settings.get("fmu_directory")
        self.label = self.shared_settings.get("label", self.fmu_directory)

        basic_well_layers = self.shared_settings.get("basic_well_layers", None)
        additional_well_layers = self.shared_settings.get("additional_well_layers")

        self.map_suffix = map_suffix
        self.interval_mode = interval_mode

        self.number_of_maps = 3
        self.observations = "observed"
        self.simulations = "simulated"
        self.wellsuffix = ".w"

        self.surface_layer = None
        self.attribute_settings = {}
        self.well_update = ""
        self.production_update = ""
        self.selected_names = [None, None, None]
        self.selected_attributes = [None, None, None]
        self.selected_iterations = [None, None, None]
        self.selected_realizations = [None, None, None]
        self.selected_intervals = ["", "", ""]
        self.well_base_layers = []
        self.interval_well_layers = {}

        # Define well layers
        self.basic_well_layers = get_basic_well_layers(basic_well_layers)
        self.additional_well_layers = get_basic_well_layers(basic_well_layers)
        self.all_well_layers = self.basic_well_layers.update(additional_well_layers)

        # Top reservoir settings
        self.top_reservoir = self.shared_settings.get("top_reservoir", None)
        self.realization = self.top_reservoir.get("realization", "realization-0")
        self.iteration = self.top_reservoir.get("iteration", "iter-0")

        # Read selection options
        self.selector_file = selector_file
        selector_file = get_path(selector_file)
        self.selection_dict = read_config(get_path(path=self.selector_file))

        last_observed_date = get_last_date(self.selection_dict)

        if last_observed_date is None:
            last_observed_date = "9999-12-31"

        self.last_observed_date = last_observed_date

        # Get a list with filenames to all possible polygons
        if polygon_mapping_file:
            self.polygon_mapping_file = polygon_mapping_file
            self.polygon_mapping = self.load_polygon_mapping(self.polygon_mapping_file)

            directory = self.top_reservoir.get("directory")
            self.polygon_paths = get_polygon_files(
                self.polygon_mapping, self.selection_dict, directory, self.fmu_directory
            )
        else:
            print("WARNING: Polygon mapping not supplied")
            self.polygon_mapping = pd.DataFrame()

        # Get path to default polygon files
        default_polygon_files = get_default_polygon_files(
            self.fmu_directory, self.top_reservoir
        )

        self.polygon_paths = self.polygon_paths + default_polygon_files

        # Read production data
        self.prod_names = ["BORE_OIL_VOL.csv", "BORE_GI_VOL.csv", "BORE_WI_VOL.csv"]
        self.prod_folder = production_data
        print("Reading production data from", self.prod_folder)
        self.prod_data = read_csvs(folder=self.prod_folder, csv_files=self.prod_names)

        # Read maps metadata
        print("Reading maps metadata from", surface_metadata_file)
        self.surface_metadata_file = surface_metadata_file
        self.surface_metadata = (
            read_csv(csv_file=surface_metadata_file)
            if surface_metadata_file is not None
            else None
        )

        # Read custom colormaps
        print("Reading custom colormaps from:", colormap_data)
        self.colormap_data = colormap_data
        if self.colormap_data is not None:
            self.colormap_files = [
                get_path(Path(fn))
                for fn in json.load(find_files(self.colormap_data, ".csv"))
            ]
            load_custom_colormaps(self.colormap_files)

        # Read attribute maps settings (min-/max-values)
        self.surface_scaling_file = surface_scaling_file
        self.colormap_settings = self.load_surface_scaling(self.surface_scaling_file)

        # Read settings
        config_dir = os.path.dirname(os.path.abspath(self.selector_file))
        self.settings_path = settings_file

        if self.settings_path:
            print("Reading settings from", self.settings_path)
            self.settings = read_config(get_path(path=self.settings_path))
            # self.delimiter = None
            self.attribute_settings = self.settings.get("attribute_settings")
            self.default_colormap = self.settings.get("default_colormap", "seismic_r")
        else:
            self.settings = None
            self.default_colormap = "seismic_r"
            print("WARNING: no settings file found, using default values")

        # Define default map settings
        map_defaults = [map1_defaults, map2_defaults, map3_defaults]
        self.map_defaults = define_map_defaults(
            map_defaults,
            self.selection_dict,
            self.observations,
            self.simulations,
        )

        # Polygons
        self.polygon_data = polygon_data
        self.default_polygon_layers = []
        self.zone_polygon_tagnames = []
        self.zone_polygon_layers = []
        self.additional_polygons = []
        self.surface_type = None

        self.zone_polygon_layers = self.shared_settings.get("zone_polygon_layers")

        # Create default FMU polygons layers
        if self.top_reservoir is not None:
            self.zone_polygon_layers = self.shared_settings.get("zone_polygon_layers")
            zone_name = self.top_reservoir.get("polygon_name")

            if self.zone_polygon_layers:
                for zone_polygon in self.zone_polygon_layers:
                    layer = self.create_polygon_layer(zone_polygon, "zone", zone_name)
                    self.default_polygon_layers.append(layer)

        # Create additional polygon layers (read )
        self.additional_polygons = self.shared_settings.get("additional_polygon_layers")
        self.additional_layers = []

        if self.additional_polygons and len(self.additional_polygons) > 0:
            for additional_polygon in self.additional_polygons:
                layer = self.create_polygon_layer(
                    additional_polygon, "additional", None
                )

                if layer:
                    self.additional_layers.append(layer)

        # Read update dates and well data
        #    self.drilled_wells_df: dataframe with wellpaths (x- and y positions) for all drilled wells
        #    self.drilled_wells_info: dataframe with metadata for all drilled wells

        self.well_layer_dir = Path(os.path.join(config_dir, "well_layers"))
        self.well_data = well_data
        print("Reading well data from", self.well_data)

        if self.well_data:
            delta = 40  # Well trajectory resampling (along MD)
            self.process_well_data(delta)

            print("Loading all well layers ...")
            self.create_well_layers()

        # Create selectors (attributes, names and dates) for all 3 maps
        self.selector = SurfaceSelector(app, self.selection_dict, self.map_defaults[0])
        self.selector2 = SurfaceSelector(app, self.selection_dict, self.map_defaults[1])
        self.selector3 = SurfaceSelector(app, self.selection_dict, self.map_defaults[2])
        self.set_callbacks(app)

    def add_webvizstore(self) -> List[Tuple[Callable, list]]:
        store_functions: List[Tuple[Callable, list]] = [
            (
                read_csvs,
                [{"folder": self.prod_folder, "csv_files": self.prod_names}],
            )
        ]

        if self.polygon_mapping_file is not None:
            store_functions.append(
                (get_path, [{"path": Path(self.polygon_mapping_file)}])
            )

            for fn in self.polygon_paths:
                store_functions.append((get_path, [{"path": Path(fn)}]))

        store_functions.append(
            (read_csv, [{"csv_file": Path(self.surface_metadata_file)}])
        )
        if self.surface_scaling_file is not None:
            store_functions.append(
                (get_path, [{"path": Path(self.surface_scaling_file)}])
            )

        if self.colormap_data is not None:
            store_functions.append(
                (find_files, [{"folder": self.colormap_data, "suffix": ".csv"}])
            )
            store_functions.append(
                (get_path, [{"path": fn} for fn in self.colormap_files])
            )

        if self.polygon_data is not None:
            for key in self.additional_polygons.keys():
                tagname = self.additional_polygons.get(key).get("tagname")
                file_format = self.additional_polygons.get(key).get("format")
                file_name = os.path.join(
                    self.polygon_data,
                    "additional_layers",
                    tagname + "." + file_format,
                )
                store_functions.append((get_path, [{"path": Path(file_name)}]))

        if self.selector_file is not None:
            store_functions.append((get_path, [{"path": self.selector_file}]))

        if self.well_data is not None:
            store_functions.append(
                (read_csv, [{"csv_file": Path(self.well_data) / "wellbore_info.csv"}])
            )
            for fn in list(self.wellbore_info["file_name"]):
                store_functions.append((get_path, [{"path": Path(fn)}]))

            store_functions.append(
                (
                    get_path,
                    [
                        {"path": Path(self.well_data) / ".welldata_update.yaml"},
                        {"path": Path(self.well_data) / ".production_update.yaml"},
                    ],
                )
            )

            store_functions.append(
                (
                    get_path,
                    [
                        {"path": Path(self.well_layer_dir) / "well_layers.yaml"},
                    ],
                )
            )

            for fn in self.layer_files:
                store_functions.append((get_path, [{"path": Path(fn)}]))

        for fn in list(self.surface_metadata["filename"]):
            store_functions.append((get_path, [{"path": Path(fn)}]))

        if self.settings_path is not None:
            store_functions.append((get_path, [{"path": self.settings_path}]))

        return store_functions

    def iterations(self, map_number):
        map_type = self.map_defaults[map_number]["map_type"]
        return self.selection_dict[map_type]["iteration"]

    def realizations(self, map_number):
        map_type = self.map_defaults[map_number]["map_type"]
        return self.selection_dict[map_type]["realization"]

    @property
    def layout(self):
        return set_layout(parent=self)

    def get_real_runpath(self, data, iteration, real, map_type):
        selected_interval = data["date"]
        name = data["name"]
        attribute = data["attr"]

        if self.interval_mode == "normal":
            time2 = selected_interval[0:10]
            time1 = selected_interval[11:]
        else:
            time1 = selected_interval[0:10]
            time2 = selected_interval[11:]

        self.surface_metadata.replace(np.nan, "", inplace=True)

        try:
            selected_metadata = self.surface_metadata[
                (self.surface_metadata["fmu_id.realization"] == real)
                & (self.surface_metadata["fmu_id.iteration"] == iteration)
                & (self.surface_metadata["map_type"] == map_type)
                & (self.surface_metadata["data.time.t1"] == time1)
                & (self.surface_metadata["data.time.t2"] == time2)
                & (self.surface_metadata["data.name"] == name)
                & (self.surface_metadata["data.attribute"] == attribute)
            ]

            filepath = selected_metadata["filename"].values[0]
            path = get_path(Path(filepath))

        except:
            path = ""
            print("WARNING: selected map not found. Selection criteria are:")
            print(map_type, real, iteration, name, attribute, time1, time2)

        return path

    def get_heading(self, map_ind, observation_type):
        if self.map_defaults[map_ind]["map_type"] == observation_type:
            txt = "Observed map: "
            info = "-"
        else:
            txt = "Simulated map: "
            info = (
                self.selected_iterations[map_ind]
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
        label = get_plot_label(self.settings, self.selected_intervals[map_ind])

        return heading, sim_info, label

    def create_additional_well_layers(self, interval):
        interval_overview = self.well_layers_overview.get("additional").get(interval)
        interval_well_layers = []

        if get_dates(interval)[0] <= self.production_update:
            for key, value in interval_overview.items():
                layer_dir = Path(self.well_layer_dir / "additional" / interval)
                well_layer_file = get_path(Path(layer_dir / value))
                label = self.additional_well_layers.get(key)

                well_layer = make_new_well_layer(
                    well_layer_file,
                    self.pdm_wells_df,
                    label,
                )

                if well_layer is not None:
                    interval_well_layers.append(well_layer)
                    self.layer_files.append(well_layer_file)

        return interval_well_layers

    def get_map_scaling(self, data, map_type, realization):
        min_max = None
        colormap_settings = self.colormap_settings

        if self.colormap_settings is not None:
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

            zone = data.get("name")

            selected_data = colormap_settings[
                (colormap_settings["map_type"] == map_type)
                & (colormap_settings["data.attribute"] == data["attr"])
                & (colormap_settings["interval"] == interval)
                & (colormap_settings["data.name"] == zone)
            ]

            if "std" in realization:
                settings = selected_data[selected_data["realization"] == "std"]
            elif map_type == "observed":
                settings = selected_data[selected_data["realization"] == realization]
            else:
                settings = selected_data[
                    selected_data["realization"] == "realization-0"
                ]

            min_max = settings[["lower_limit", "upper_limit"]]

        return min_max

    def make_map(self, data, iteration, real, attribute_settings, map_idx):
        self.realization = real
        self.iteration = iteration
        data = json.loads(data)
        selected_zone = data.get("name")
        map_type = self.map_defaults[map_idx]["map_type"]
        surface_file = self.get_real_runpath(data, iteration, real, map_type)

        if "realization" in real:
            self.surface_type = "realization"
        elif "---" in real:
            self.surface_type = "observation"
        else:
            self.surface_type = "aggregation"

        if os.path.isfile(surface_file):
            surface = load_surface(surface_file)
            attribute_settings = json.loads(attribute_settings)

            min_val, max_val = get_map_min_max(surface, attribute_settings, data)
            metadata = self.get_map_scaling(data, map_type, real)

            surface_layers = [
                make_surface_layer(
                    surface,
                    name=data["attr"],
                    color=attribute_settings.get(data["attr"], {}).get(
                        "color", self.default_colormap
                    ),
                    min_val=min_val,
                    max_val=max_val,
                    unit=attribute_settings.get(data["attr"], {}).get("unit", ""),
                    hillshading=False,
                    min_max_df=metadata,
                )
            ]

            # Check if there are polygons available for the new map
            if self.zone_polygon_layers and len(self.zone_polygon_layers) > 0:
                for index, zone_polygon in enumerate(self.zone_polygon_layers):
                    layer = self.create_polygon_layer(
                        zone_polygon, "zone", selected_zone
                    )

                    if len(layer) == 0:  # Specific polygon not found, use default
                        layer = self.default_polygon_layers[index]

                    surface_layers.append(layer)

            # Add additional polygon layers (if existing)
            if self.additional_layers and len(self.additional_layers) > 0:
                for layer in self.additional_layers:
                    surface_layers.append(layer)

            if self.basic_well_layers:
                for well_layer in self.well_basic_layers:
                    surface_layers.append(well_layer)

            interval = data["date"]

            # Load new interval well layers if selected interval has changed (or has not been set)
            if interval != self.selected_intervals[map_idx]:
                if get_dates(interval)[0] <= self.last_observed_date:
                    index = self.interval_names.index(interval)
                    self.interval_well_layers = self.all_interval_layers[index]
                    self.selected_intervals[map_idx] = interval
                else:
                    self.interval_well_layers = []

            for interval_layer in self.interval_well_layers:
                surface_layers.append(interval_layer)

            self.selected_names[map_idx] = data["name"]
            self.selected_attributes[map_idx] = data["attr"]
            self.selected_iterations[map_idx] = iteration
            self.selected_realizations[map_idx] = real
            self.selected_intervals[map_idx] = interval

            heading, sim_info, label = self.get_heading(map_idx, self.observations)
        else:
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

    def create_well_layers(self):
        self.well_basic_layers = []
        self.all_interval_layers = []
        self.layer_files = []

        basic_layers = self.well_layers_overview.get("basic")

        for key, value in basic_layers.items():
            layer_file = get_path(Path(self.well_layer_dir / "basic" / value))
            label = self.basic_well_layers.get(key)

            well_layer = make_new_well_layer(
                layer_file,
                self.all_wells_df,
                label,
            )

            if well_layer:
                self.well_basic_layers.append(well_layer)
                self.layer_files.append(layer_file)

        self.intervals = self.well_layers_overview.get("additional")
        self.interval_names = []

        for interval in self.intervals:
            interval_layers = self.create_additional_well_layers(interval)
            self.all_interval_layers.append(interval_layers)
            self.interval_names.append(interval)

    def process_well_data(self, delta):
        self.well_update, self.production_update = self.get_dates()

        self.wellbore_info = read_csv(
            csv_file=Path(self.well_data) / "wellbore_info.csv"
        )

        self.all_wells_info = read_csv(
            csv_file=Path(self.well_data) / "wellbore_info.csv"
        )

        self.all_wells_info["file_name"] = self.all_wells_info["file_name"].apply(
            lambda x: get_path(Path(x))
        )

        self.all_wells_df = load_all_wells(self.all_wells_info, delta)
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

        self.pdm_wells_info = self.drilled_wells_info.loc[
            self.drilled_wells_info["wellbore.pdm_name"] != ""
        ]

        self.pdm_wells_df = load_all_wells(self.pdm_wells_info, delta)

        layer_overview_file = get_path(Path(self.well_layer_dir / "well_layers.yaml"))
        self.well_layers_overview = read_config(layer_overview_file)

    def get_dates(self):
        update_dates = get_update_dates(
            welldata=get_path(Path(self.well_data) / ".welldata_update.yaml"),
            productiondata=get_path(Path(self.well_data) / ".production_update.yaml"),
        )

        well_update = update_dates["well_update_date"]
        production_update = update_dates["production_last_date"]

        return well_update, production_update

    def load_polygon_mapping(self, mapping_file):
        print("Reading polygon mapping from", mapping_file)

        if os.path.exists(get_path(mapping_file)):
            polygon_mapping = pd.read_csv(get_path(mapping_file))
        else:
            polygon_mapping = pd.DataFrame()
            print("WARNING: Polygon mapping file not found", self.polygon_mapping_file)

        return polygon_mapping

    def load_surface_scaling(self, surface_scaling_file):
        print("Reading surface scaling from", surface_scaling_file)

        if os.path.exists(get_path(surface_scaling_file)):
            surface_scaling = pd.read_csv(get_path(surface_scaling_file))
        else:
            surface_scaling = pd.DataFrame()
            print("WARNING: Surface scaling file not found", self.surface_scaling_file)

        return surface_scaling

    def create_polygon_layer(self, polygon, polygon_type, zone_name):
        """Create a polygon layer which can either be a zone polygon or an additional polygon
        Two types of polygons are supported:
        - zone polygons (from the fmu execution)
        - additional polygons (e.g. prm lines, shadow areas, ...)"""
        layer = []
        color = None

        if polygon_type == "additional":
            tagname = self.additional_polygons.get(polygon).get("tagname")
            label = self.additional_polygons.get(polygon).get("label")
            format = self.additional_polygons.get(polygon).get("format")
            tooltip = tagname
            polygon_colors = self.settings.get("polygon_colors")

            if polygon_colors:
                color = polygon_colors.get(tagname)

            polygon_file = os.path.join(
                self.polygon_data,
                "additional_layers",
                tagname + "." + format,
            )

            print("Reading polygon file:", polygon_file)

            self.polygon_paths.append(polygon_file)
            polygon_df = pd.read_csv(get_path(Path(polygon_file)))

            layer = make_polyline_layer(
                polygon_type, polygon_df, format, tagname, label, tooltip, color
            )

        elif polygon_type == "zone":
            tagname = self.zone_polygon_layers.get(polygon).get("tagname")
            label = self.zone_polygon_layers.get(polygon).get("label")
            format = self.zone_polygon_layers.get(polygon).get("format")

            if self.surface_type is None:
                self.surface_type = "observation"

            if self.surface_type == "realization":
                polygons_folder = os.path.join(
                    self.fmu_directory,
                    self.realization,
                    self.iteration,
                    self.top_reservoir.get("directory"),
                    self.top_reservoir.get("polygons_directory"),
                )
            else:
                polygons_folder = os.path.join(
                    self.fmu_directory,
                    self.top_reservoir.get("iteration"),
                    self.top_reservoir.get("directory"),
                    self.top_reservoir.get("polygons_directory"),
                )

            if polygons_folder is not None:
                if not self.polygon_mapping.empty:
                    name = get_polygon_name(self.polygon_mapping, zone_name, tagname)
                else:
                    name = self.top_reservoir.get("polygon_name")

                tooltip = name + "-" + tagname

                polygon_file = name + "--" + tagname + "." + format
                polygon_file = os.path.join(polygons_folder, polygon_file)

                if os.path.exists(get_path(Path(polygon_file))):
                    polygon_df = pd.read_csv(get_path(Path(polygon_file)))

                    if "REAL" in polygon_df.columns:
                        selected_df = polygon_df[polygon_df["REAL"] == 0]
                        polygon_df = selected_df.copy()

                    polygon_type = "zone"
                    color = get_color(self.settings, "polygon", polygon)

                    if len(polygon_df) > 0 and "ID" in polygon_df.columns:
                        layer = make_polyline_layer(
                            polygon_type,
                            polygon_df,
                            format,
                            tagname,
                            label,
                            tooltip,
                            color,
                        )
                    else:
                        print("WARNING: layer not created")
                        layer = None

        return layer

    def set_callbacks(self, app):
        set_first_map(parent=self, app=app)
        set_second_map(parent=self, app=app)
        set_third_map(parent=self, app=app)
        change_maps_from_button(parent=self, app=app)
