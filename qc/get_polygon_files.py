import os.path
import pandas as pd
from webviz_4d._datainput._polygons import get_polygon_files
from webviz_4d._datainput.common import read_config


def main():
    polygon_mapping_file = "/project/johan_sverdrup/share/webviz/2024_02_19/fields/johan_sverdrup/2024_02_config/february_config/polygon_mapping.csv"
    polygon_mapping = pd.read_csv(polygon_mapping_file)
    print(polygon_mapping)

    selector_file = "/project/johan_sverdrup/share/webviz/2024_02_19/fields/johan_sverdrup/2024_02_config/february_config/selectors.yaml"
    selection = read_config(selector_file)
    print(selection)

    fmu_dir = "/scratch/johan_sverdrup2/share/23p20p0/23p20p0_histandpred_ff_20230917"
    directory = "share/results"

    polygon_paths = get_polygon_files(polygon_mapping, selection, directory, fmu_dir)

    for path in polygon_paths:
        print(path)


if __name__ == "__main__":
    main()
