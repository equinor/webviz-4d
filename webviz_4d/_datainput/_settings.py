def get_color(settings, data_type, tagname):
    color = None
    color_settings = settings.get(data_type + "_colors", None)

    if color_settings:
        color = color_settings.get(tagname)

    return color
