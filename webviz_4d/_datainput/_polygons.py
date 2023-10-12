import pandas as pd
import json


default_colors = {
    "field_outline": "lightslategray",
    "owc_outline": "lightslategray",
    "goc_outline": "red",
    "faults": "gray",
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


def create_polyline(polygon_row, polygon_info):
    """Create polyline data - polylines, color and tooltip"""

    zone = polygon_info.get("zone")
    year = polygon_row.get("year")
    line = polygon_row.get("line")
    zone = polygon_info.get("zone")

    if zone is not None:
        tooltip = zone + "-" + polygon_info.get("tagname")
    elif year is not None:
        tooltip = str(year) + "-line " + str(line)
    else:
        tooltip = polygon_info.get("tagname")

    color = polygon_info.get("color")

    positions = get_position_data(polygon_row)

    if positions:
        return {
            "type": "polyline",
            "color": color,
            "positions": positions,
            "tooltip": tooltip,
        }


def create_prm_polyline(polygon_row, polygon_info):
    """Create polyline data - prm receiver polylines, color and tooltip"""
    year = polygon_row["year"]
    line = polygon_row["line"]
    tooltip = str(year) + "-line " + str(line)
    color = polygon_info.get("color")

    positions = get_position_data(polygon_row)

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


def make_polyline_layer(dataframe, polygon_info):
    """Make layeredmap fault layer"""
    data = []
    layer = {}

    for _index, row in dataframe.iterrows():
        polyline_data = create_polyline(row, polygon_info)

        if polyline_data:
            data.append(polyline_data)
            label = polygon_info.get("label")

    if data:
        checked_state = checked.get(label, False)
        layer = {
            "name": label,
            "checked": checked_state,
            "base_layer": False,
            "data": data,
        }

    return layer


def make_prm_polyline_layer(dataframe, polygon_info):
    """Make layeredmap fault layer"""
    data = []
    layer = {}

    for _index, row in dataframe.iterrows():
        polyline_data = create_prm_polyline(row, polygon_info)

        if polyline_data:
            data.append(polyline_data)
            label = polygon_info.get("label")

    if data:
        checked_state = checked.get(label, False)
        layer = {
            "name": label,
            "checked": checked_state,
            "base_layer": False,
            "data": data,
        }

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


def get_polygon_info(layer_file, polygones_overview, settings):
    default_color = "black"

    info = polygones_overview[polygones_overview["file_name"] == layer_file]

    polygon_name = info["name"].values[0]
    polygon_type = info["type"].values[0]
    polygon_tagname = info["tagname"].values[0]
    polygon_label = info["label"].values[0]

    polygon_colors = settings.get("polygon_colors")

    if polygon_colors:
        color = polygon_colors.get(polygon_type, default_color)
    else:
        color = default_color

    keys = ["type", "zone", "tagname", "label", "color"]
    values = [polygon_type, polygon_name, polygon_tagname, polygon_label, color]

    polygon_info = {keys[i]: values[i] for i in range(len(keys))}

    return polygon_info


def get_polygon_name(mapping, zone, polygon_type):
    polygon_name = None

    selected_row = mapping[
        (mapping["surface_name"] == zone) & (mapping["polygon_type"] == polygon_type)
    ]

    selected_name = selected_row["polygon_name"]

    if len(selected_name) == 1:
        polygon_name = selected_name.values[0]

    return polygon_name


def get_polygon_layer(polygon_layers, selected_name, selected_tagname):
    layer = None

    for polygon_layer in polygon_layers:
        polygon_data = polygon_layer.get("data")[0]
        tooltip = polygon_data.get("tooltip")
        tooltip_items = tooltip.split("-")
        name = tooltip_items[0]
        tagname = tooltip_items[1]

        if name == selected_name and tagname == selected_tagname:
            layer = polygon_layer

    return layer
