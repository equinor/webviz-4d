import os

default_basic_well_layers = {
    "drilled_wells": "Drilled wells",
    "reservoir_section": "Reservoir sections",
    "active_production": "Current producers",
    "active_injection": "Current injectors",
}

default_additional_well_layers = {
    "production": "Producers",
    "production_start": "Producers - started",
    "production_completed": "Producers - completed",
    "injection": "Injectors",
    "injection_start": "Injectors - started",
    "injection_completed": "Injectors - completed",
}


def get_basic_well_layers(basic_well_layers):
    if basic_well_layers is None:
        basic_well_layers = default_basic_well_layers

    return basic_well_layers


def get_additional_well_layers(additional_well_layers):
    if additional_well_layers is None:
        additional_well_layers = default_additional_well_layers

    return additional_well_layers


def get_polygon_tagnames(shared_settings, polygon_class):
    polygon_configuration = shared_settings.get(polygon_class + "_polygon_layers")
    polygon_tagnames = []

    for _key, value in polygon_configuration.items():
        tagname = value.get("tagname")
        polygon_tagnames.append(tagname)

    return polygon_tagnames
