import os
import math
import pandas as pd
from typing import Optional
from pathlib import Path

from webviz_4d.plugins._surface_viewer_4D._webvizstore import get_path, read_csv


class Polygon:
    """Class for a polygon in webviz-4d"""

    def __init__(
        self, file_name: str, layer_name: str, polygon_format: Optional[str] = "rms"
    ):
        rms_headers = ["X", "Y", "Z", "ID"]
        prm_headers = [
            "Installation",
            "RECEIVER_POINT",
            "RECEIVER_LINE",
            "RCV_UTMX",
            "RCV_UTMY",
        ]
        supported_formats = {"rms": rms_headers, "prm": prm_headers, "csv": rms_headers}

        if polygon_format not in supported_formats:
            print("ERROR:", polygon_format, "not supported")
            print("Supported types are:", supported_formats.keys())
            exit()

        if polygon_format == "prm":
            sep = "\t"
        else:
            sep = ","

        if not os.path.exists(file_name):
            print("ERROR: File", file_name, "not found")
            exit()

        self.dataframe = pd.read_csv(file_name, sep=sep)
        self.format = polygon_format
        self.layer_name = layer_name

    def __str__(self):
        txt = " ".join(self.dataframe.columns) + "\n"
        first_row = self.dataframe.values[:1][0]
        txt = txt + " ".join(["{:.2f}".format(x) for x in first_row]) + "\n"
        txt = txt + "... \n"
        last_row = self.dataframe.values[:-1][0]
        txt = txt + " ".join(["{:.2f}".format(x) for x in last_row]) + "\n"

        return txt

    def create_rms_layer(self):
        all_positions = []
        positions = []
        ids = []

        polygon_df = self.dataframe

        for _index, row in polygon_df.iterrows():
            if not math.isnan(row["ID"]):
                position = [row["X"], row["Y"]]

                if _index == 0:
                    poly_id = row["ID"]

                if row["ID"] == poly_id:
                    position = [row["X"], row["Y"]]
                    positions.append(position)
                else:
                    all_positions.append(positions)
                    positions = []
                    poly_id = row["ID"]
                    position = [row["X"], row["Y"]]
                    positions.append(position)
                    ids.append(poly_id)

        # Add last line
        all_positions.append(positions)
        ids.append(poly_id)

        layer_df = pd.DataFrame()
        layer_df["id"] = ids
        layer_df["geometry"] = "Polygon"
        layer_df["coordinates"] = all_positions
        layer_df["name"] = self.layer_name

        return layer_df

    def create_prm_layer(self):
        layer_df = pd.DataFrame()
        years = []
        lines = []
        coordinates = []
        coordinates_row = []

        current_line = 1
        for _index, row in self.dataframe.iterrows():
            utmx = float(row["RCV_UTMX"])
            utmy = float(row["RCV_UTMY"])
            line = int(row["RECEIVER_LINE"])
            year = int(row["Installation"])

            if current_line == 1:
                current_year = year

            if line == current_line:
                coordinates_row.append([utmx, utmy])
            else:
                coordinates.append(coordinates_row)
                years.append(current_year)
                lines.append(current_line)

                coordinates_row = []
                coordinates_row.append([utmx, utmy])
                current_line = line
                current_year = year

        # Add last line
        coordinates.append(coordinates_row)
        years.append(current_year)
        lines.append(current_line)

        layer_df["line"] = lines
        layer_df["geometry"] = "Polygon"
        layer_df["coordinates"] = coordinates
        layer_df["year"] = years
        layer_df["name"] = self.layer_name

        return layer_df

    def create_layer(self):
        if self.format == "prm":
            layer_df = self.create_prm_layer()
        else:
            layer_df = self.create_rms_layer()

        return layer_df

    def get_polygon_filename(
        fmu_directory: str,
        name: str,
        tagname: str,
        iteration: str,
        realization: str,
        polygon_directory: str,
        mapping_file: Optional[str] = "polygon_mapping_file.csv",
    ):
        extensions = [".csv", ".pol"]
        file_name = None
        polygon_mapping = pd.DataFrame()

        if os.path.exists(get_path(mapping_file)):
            polygon_mapping = read_csv(get_path(mapping_file))

        for extension in extensions:
            fname = name + "--" + tagname + extension
            file_name = os.path.join(
                fmu_directory,
                realization,
                iteration,
                "share/results",
                polygon_directory,
                fname,
            )

            if os.path.exists(file_name):
                return file_name

        if not polygon_mapping.empty:
            mapping = polygon_mapping[
                [polygon_mapping]["surface"]
                == name & [polygon_mapping]["polygon_type"]
                == tagname
            ]

        return file_name
