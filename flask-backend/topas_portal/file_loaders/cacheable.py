import json
from pathlib import Path
from functools import wraps
import pandas as pd

from ..data_type import DataType
from ..config import CohortConfig


def cacheable(data_type_key: DataType):
    """
    Decorator to cache loader outputs as Feather files if config['cache_dir'] is set.
    Preserves original index (including MultiIndex) and columns (including MultiIndex).
    """

    def decorator(func):
        @wraps(func)
        def wrapper(cohort_name: str, config: CohortConfig):
            cache_dir = Path(config.get_cache_directory())
            feather_path, meta_path = _get_cache_paths(
                cohort_name, cache_dir, data_type_key
            )

            input_files = config.get_input_file_paths(cohort_name, data_type_key)

            # Try loading from cache
            if (
                cache_dir.is_dir()
                and feather_path.exists()
                and meta_path.exists()
                and _cache_matches_inputs(meta_path, input_files)
            ):
                print(f"[CACHE HIT] {data_type_key} for {cohort_name}")
                return _load_cache(feather_path, meta_path)

            # Run the actual loader
            df = func(cohort_name, config)

            # Save to cache if directory exists
            if cache_dir.is_dir() and isinstance(df, pd.DataFrame):
                _save_cache(df, feather_path, meta_path, input_files)
                print(f"[CACHE SAVED] {data_type_key} for {cohort_name}")

            return df

        return wrapper

    return decorator


def _get_cache_paths(cohort_name: str, cache_dir: Path, data_type_key: DataType):
    """Return paths for feather file and metadata json."""
    feather_path = cache_dir / cohort_name / f"{data_type_key.value}.feather"
    meta_path = feather_path.with_suffix(".meta.json")
    return feather_path, meta_path


def _save_cache(
    df: pd.DataFrame, feather_path: Path, meta_path: Path, input_files: list[Path]
):
    """Save DataFrame and metadata to Feather and JSON, flattening MultiIndexes."""
    feather_path.parent.mkdir(exist_ok=True, parents=True)

    index_names = []
    if not pd.api.types.is_numeric_dtype(df.index):
        index_names = df.index.names
        df = df.reset_index()

    if isinstance(df.columns, pd.MultiIndex):
        raise NotImplementedError("Multi column indices are not supported yet.")
    columns_index_name = ""
    if df.columns.name:
        columns_index_name = df.columns.name

    df.to_feather(feather_path)

    # Gather file metadata
    file_info = []
    for f in input_files:
        if Path(f).exists():
            file_info.append(
                {
                    "path": str(f),
                    "size": Path(f).stat().st_size,
                    "mtime": Path(f).stat().st_mtime,
                }
            )

    meta = {
        "index_columns": index_names,
        "columns_index_name": columns_index_name,
        "input_files": file_info,
    }
    with open(meta_path, "w") as f:
        json.dump(meta, f, indent=2)


def _load_cache(feather_path: Path, meta_path: Path):
    """Load DataFrame from Feather and restore index and columns, including MultiIndex."""
    df = pd.read_feather(feather_path)
    with open(meta_path, "r") as f:
        meta = json.load(f)

    df.columns.name = meta["columns_index_name"]
    if len(meta["index_columns"]) > 0:
        if len(meta["index_columns"]) == 1 and meta["index_columns"][0] is None:
            meta["index_columns"] = ["index"]
        df = df.set_index(meta["index_columns"])

    return df


def _cache_matches_inputs(meta_path: Path, input_files):
    """Return True if all input files match size and mtime stored in meta JSON."""
    with open(meta_path, "r") as f:
        meta = json.load(f)

    cached_files = {entry["path"]: entry for entry in meta.get("input_files", [])}

    for f in input_files:
        f = str(f)
        if f not in cached_files:
            return False  # new file
        if not Path(f).exists():
            return False
        stat = Path(f).stat()
        cached = cached_files[f]
        if cached["size"] != stat.st_size or cached["mtime"] != stat.st_mtime:
            return False  # modified file

    return True
