import pandas as pd
import json


default_colors = {
    "field_outline": "lightslategray",
    "fwl": "lightslategray",
    "owc_outline": "lightslategray",
    "goc_outline": "red",
    "fault_lines": "gray",
    "prm_receivers": "darkgray",
    "4D_undershoot": "salmon",
    "injectites": "khaki",
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


def create_polygon_layer(polygon_df):
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


def make_polyline_layer(polygon_df, format, tagname, label, tooltip, color):
    """Make layeredmap fault layer"""
    data = []
    dataframe = create_polygon_layer(polygon_df)

    if dataframe.empty:
        print("WARNING: empty dataframe as input to make_polyline_layer")
        return None

    if color == None:
        color = default_colors.get(tagname)

    if format == "csv":
        for _index, row in dataframe.iterrows():
            if "tooltip" in dataframe.columns:
                tooltip = row["tooltip"]

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

    positions = layer["coordinates"]

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
