import os
import pandas as pd
import json
from pathlib import Path

from webviz_config.webviz_store import webvizstore
from webviz_config.common_cache import CACHE

from webviz_4d.plugins._surface_viewer_4D._webvizstore import (
    read_csv,
)


default_colors = {
    "owc_outline": "lightslategray",
    "goc_outline": "red",
    "faults": "gray",
    "prm_receivers": "darkgray",
    "4D_undershoot": "salmon",
    "injectites": "khaki",
}

checked = {
    "Initial OWC": True,
    "Initial GOC": True,
    "Faults": True,
}

# key_list = list(supported_polygons.keys())
# val_list = list(supported_polygons.values())


def get_position_data(polyline):
    """Return x- and y-values for a selected polygon"""
    positions_txt = polyline["coordinates"]

    if isinstance(positions_txt, str):
        positions = json.loads(positions_txt)
    else:
        positions = positions_txt

    return positions


def get_fault_polyline(fault, tooltip, color):
    """Create polyline data - fault polylines, color and tooltip"""
    if color is None:
        color = default_colors.get("faults")

    positions = get_position_data(fault)

    if positions:
        return {
            "type": "polyline",
            "color": color,
            "positions": positions,
            "tooltip": tooltip,
        }


def get_prm_polyline(prm, color):
    """Create polyline data - prm receiver polylines, color and tooltip"""
    if color is None:
        color = default_colors.get("prm_receivers")

    positions = get_position_data(prm)
    year = prm["year"]
    line = prm["line"]
    tooltip = str(year) + "-line " + str(line)

    if positions:
        return {
            "type": "polyline",
            "color": color,
            "positions": positions,
            "tooltip": tooltip,
        }


def get_contact_polyline(contact, key, label, color):
    """Create polyline data - owc polyline, color and tooltip"""
    data = []
    tooltip = label

    coordinates_txt = contact["coordinates"][0]
    coordinates = json.loads(coordinates_txt)

    if color is None:
        color = default_colors.get(key)

    for i in range(0, len(coordinates)):
        positions = coordinates[i]

        if positions:
            polyline_data = {
                "type": "polyline",
                "color": color,
                "positions": positions,
                "tooltip": tooltip,
            }

            data.append(polyline_data)

    return data


def make_new_polyline_layer(dataframe, key, label, color):
    """Make layeredmap fault layer"""
    data = []

    if "outline" in key:
        data = get_contact_polyline(dataframe, key, label, color)
    elif key == "prm_receivers":
        for _index, row in dataframe.iterrows():
            polyline_data = get_prm_polyline(row, color)

            if polyline_data:
                data.append(polyline_data)
    else:
        for _index, row in dataframe.iterrows():
            polyline_data = get_fault_polyline(row, key, color)

            if polyline_data:
                data.append(polyline_data)
    if data:
        checked_state = checked.get(label, False)
        layer = {
            "name": label,
            "checked": checked_state,
            "base_layer": False,
            "data": data,
        }

    return layer


def load_polygons(polygon_data, configuration, polygon_colors):
    polygon_layers = []

    if configuration is not None:
        for key, value in configuration.items():
            selected_file = key + ".csv"
            csv_file = Path(polygon_data) / selected_file

            try:
                polygon_df = read_csv(csv_file)
                name = polygon_df["name"].unique()[0]

                default_color = default_colors.get(name)

                if polygon_colors and key in polygon_colors.keys():
                    color = polygon_colors[key]
                else:
                    color = default_color

                label = configuration.get(name)
                polygon_layer = make_new_polyline_layer(polygon_df, name, label, color)
                polygon_layers.append(polygon_layer)
            except:
                print("Polygon file not found:", csv_file)

    return polygon_layers


def load_zone_polygons(csv_files, polygon_colors):
    polygon_layers = []

    for csv_file in csv_files:
        polygon_df = read_csv(csv_file)

        name = os.path.basename(csv_file).replace(".csv", "")
        label = "Faults"

        default_color = default_colors.get(name)

        if polygon_colors:
            color = polygon_colors.get("faults")
        else:
            color = default_color

        polygon_layer = make_new_polyline_layer(polygon_df, name, label, color)
        polygon_layers.append(polygon_layer)

    return polygon_layers


def get_zone_layer(polygon_layers, zone_name):
    for layer in polygon_layers:
        data = layer["data"]
        tooltip = data[0]["tooltip"]

        if tooltip == zone_name:
            return layer

    return None


def create_zone_layer(polygon_file_name, name):
    layer = None

    if os.path.exists(polygon_file_name):
        polygon_df = pd.read_csv(polygon_file_name)
        layer = create_fault_layer(polygon_df, name)

    return layer


def create_fault_layer(faults_df, name):
    layer_df = pd.DataFrame()
    seg_id = []
    coordinates = []
    coordinates_row = []

    id = 0
    for _index, row in faults_df.iterrows():
        utmx = float(row["X_UTME"])
        utmy = float(row["Y_UTMN"])

        if utmx > 1000.0 and utmy > 1000.0:
            coordinates_row.append([utmx, utmy])
            id = id + 1
        else:
            seg_id.append(int(id))
            coordinates.append(coordinates_row)
            coordinates_row = []

    layer_df["SEG I.D."] = seg_id
    layer_df["geometry"] = "Polygon"
    layer_df["coordinates"] = coordinates
    layer_df["name"] = name

    return layer_df


def has_header(df):
    try:
        number = float(df.columns[0])
        status = False
    except:
        status = True

    return status


def create_polygon_layer(polygon_df):
    """Create polygon layer"""
    all_positions = []
    positions = []
    ids = []

    if has_header(polygon_df):
        for _index, row in polygon_df.iterrows():
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

    else:
        id = 0
        for _index, row in polygon_df.iterrows():
            utmx = float(row[0])
            utmy = float(row[1])

            if utmx > 1000.0 and utmy > 1000.0:
                positions.append([utmx, utmy])
                id = id + 1
            else:
                ids.append(id)
                all_positions.append(positions)
                positions = []

    layer_df = pd.DataFrame()
    layer_df["id"] = ids
    layer_df["geometry"] = "Polygon"
    layer_df["coordinates"] = all_positions

    return layer_df
