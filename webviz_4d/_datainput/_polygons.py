import os
import pandas as pd
import json
import glob


default_colors = {
    "field_outline": "lightslategray",
    "fwl": "lightslategray",
    "owc_outline": "lightslategray",
    "goc_outline": "red",
    "fault_lines": "gray",
}

checked = {"OWC": True, "GOC": True, "FWL": True, "Faults": True, "Field outline": True}


def get_position_data(polyline):
    """Return x- and y-values for a selected polygon"""
    positions_txt = polyline["coordinates"]

    if isinstance(positions_txt, str):
        positions = json.loads(positions_txt)
    else:
        positions = positions_txt

    return positions


def has_header(df):
    """Check if a dataframe has headers and that one of them is X"""
    try:
        number = float(df.columns[0])
        status = False
    except:
        status = True

        if "X" in df.columns:
            status = True
        else:
            status = False

    return status


def convert_polygon_layer(polygon_df):
    """Create polygon layer"""
    all_positions = []
    positions = []
    ids = []
    tooltips = []
    tooltip = None

    polygon_df.dropna(subset=["ID"], inplace=True)

    if has_header(polygon_df):
        for _index, row in polygon_df.iterrows():
            if "tooltip" in polygon_df.columns:
                tooltip = row["tooltip"]

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

                if tooltip:
                    tooltips.append(tooltip)

        # Add last line
        all_positions.append(positions)
        ids.append(poly_id)

        if tooltip:
            tooltips.append(tooltip)
    else:
        return pd.DataFrame()

    layer_df = pd.DataFrame()
    layer_df["id"] = ids
    layer_df["geometry"] = "Polygon"
    layer_df["coordinates"] = all_positions

    if len(tooltips) > 0:
        layer_df["tooltip"] = tooltips

    return layer_df


def get_polygon_name(mapping, zone, polygon_type):
    polygon_name = zone

    selected_row = mapping[(mapping["surface_name"] == zone)]
    selected_name = selected_row[polygon_type]

    if len(selected_name) == 1:
        polygon_name = selected_name.values[0]

    return polygon_name


def make_polyline_layer(
    polygon_type, polygon_df, format, tagname, label, tooltip, color
):
    """Make layeredmap fault layer"""
    data = []

    if color == None:
        color = default_colors.get(tagname)

    if polygon_type == "zone":
        dataframe = convert_polygon_layer(polygon_df)

        if dataframe.empty:
            print("WARNING: empty dataframe as input to make_polyline_layer")
            return None

        if format == "csv":
            for _index, row in dataframe.iterrows():
                if "tooltip" in dataframe.columns:
                    tooltip = row["tooltip"]

                polyline_data = get_polyline(row, tooltip, color)

                if polyline_data:
                    data.append(polyline_data)
        else:
            print("ERROR unknown format:", format)
    elif polygon_type == "additional":
        dataframe = polygon_df.copy()

        if format == "csv":
            for _index, row in dataframe.iterrows():
                if "year" in dataframe.columns:
                    tooltip = "Line " + str(row["line"]) + " (" + str(row["year"]) + ")"

                polyline_data = get_polyline(row, tooltip, color)

                if polyline_data:
                    data.append(polyline_data)
    else:
        print("ERROR unknown format:", format)

    if data:
        checked_state = checked.get(label)
        layer = {
            "name": label,
            "checked": checked_state,
            "base_layer": False,
            "data": data,
        }
    else:
        layer = None

    return layer


def get_polyline(layer, tooltip, color):
    """Create polyline data - based on coordinates, color and tooltip"""
    if color is None:
        color = "black"

    positions_txt = layer["coordinates"]

    if isinstance(positions_txt, str):
        positions = json.loads(positions_txt)
    else:
        positions = positions_txt

    if positions:
        return {
            "type": "polyline",
            "color": color,
            "positions": positions,
            "tooltip": tooltip,
        }
    else:
        print("WARNING: not possible to create layer")
        print("Input layer:")
        print(layer)
        return {}


def get_polygon_files(polygon_mapping, selection_list, directory, fmu_dir):
    # Create a list with filenames to all possible polygons
    polygon_overview = {}
    paths = []

    # Create polygon overview
    polygon_types = polygon_mapping.columns[1:]

    for polygon_type in polygon_types:
        surface_names = polygon_mapping[polygon_type].to_list()
        unique_names = list(set(surface_names))
        polygon_overview.update({polygon_type: unique_names})

    realizations = selection_list.get("simulated").get("realization")
    iterations = selection_list.get("simulated").get("iteration")

    for realization in realizations:
        if "realization" in realization:
            for iteration in iterations:
                for polygon_type in polygon_overview.keys():
                    surfaces = polygon_overview.get(polygon_type)

                    for surface in surfaces:
                        file_name = surface + "--" + polygon_type + ".csv"
                        path = os.path.join(
                            fmu_dir,
                            realization,
                            iteration,
                            directory,
                            "polygons",
                            file_name,
                        )

                        paths.append(path)

    return paths


def get_default_polygon_files(fmu_dir, top_reservoir):
    directory = top_reservoir.get("directory")
    polygons_directory = top_reservoir.get("polygons_directory")

    default_iteration = top_reservoir.get("iteration")
    default_realization = top_reservoir.get("realization")

    # Default polygons for realizations and iterations
    polygons_folder = os.path.join(
        fmu_dir,
        default_realization,
        default_iteration,
        directory,
        polygons_directory,
    )

    default_polygon_files = glob.glob(os.path.join(polygons_folder, "*"))

    # Default polygons if only aggregated data
    polygons_folder = os.path.join(
        fmu_dir,
        directory,
        polygons_directory,
    )

    polygon_files = glob.glob(os.path.join(polygons_folder, "*"))
    default_polygon_files = default_polygon_files + polygon_files

    return default_polygon_files
