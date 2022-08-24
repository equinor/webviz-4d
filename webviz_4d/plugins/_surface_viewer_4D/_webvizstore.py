from typing import List, Tuple, Callable
import json
import os
from io import BytesIO
from pathlib import Path

import pandas as pd
from webviz_config.webviz_store import webvizstore


@webvizstore
def get_path(path) -> Path:
    return Path(path)


@webvizstore
def read_csvs(folder: Path, csv_files: list) -> pd.DataFrame:
    all_prod_df = pd.DataFrame()

    for name in csv_files:
        csv_file = os.path.join(folder, name)

        if os.path.isfile(csv_file):
            prod_df = pd.read_csv(csv_file)
            all_prod_df = pd.concat([all_prod_df, prod_df])

    all_prod_df.reset_index(inplace=True, drop=True)

    return all_prod_df


@webvizstore
def read_csv(csv_file: Path) -> pd.DataFrame:
    return pd.read_csv(csv_file)


@webvizstore
def find_files(folder: Path, suffix: str) -> BytesIO:
    return BytesIO(
        json.dumps(
            sorted([str(filename) for filename in folder.glob(f"*{suffix}")])
        ).encode()
    )
