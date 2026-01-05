import os
import sys
import pathlib


def _get_default_config_dirs() -> list[pathlib.Path]:
    """Get platform-appropriate config directories."""
    dirs = [
        pathlib.Path(f"{sys.prefix}/share/ramalama"),
        pathlib.Path(f"{sys.prefix}/local/share/ramalama"),
    ]

    if os.name == 'nt':
        # Windows-specific paths using APPDATA and LOCALAPPDATA
        appdata = os.getenv("APPDATA", os.path.expanduser("~/AppData/Roaming"))
        localappdata = os.getenv("LOCALAPPDATA", os.path.expanduser("~/AppData/Local"))
        dirs.extend(
            [
                pathlib.Path(os.path.join(localappdata, "ramalama")),
                pathlib.Path(os.path.join(appdata, "ramalama")),
            ]
        )
    else:
        # Unix-specific paths
        dirs.extend(
            [
                pathlib.Path("/etc/ramalama"),
                pathlib.Path(os.path.expanduser(os.path.join(os.getenv("XDG_DATA_HOME", "~/.local/share"), "ramalama"))),
                pathlib.Path(os.path.expanduser(os.path.join(os.getenv("XDG_CONFIG_HOME", "~/.config"), "ramalama"))),
            ]
        )

    return dirs

DEFAULT_CONFIG_DIRS = _get_default_config_dirs()

def get_all_inference_spec_dirs(subdir: str) -> list[pathlib.Path]:
    development_spec_dir = pathlib.Path(__file__).parent / subdir
    all_dirs = [development_spec_dir, *[conf_dir / "inference" for conf_dir in DEFAULT_CONFIG_DIRS]]

    return [d for d in all_dirs if d.exists()]


def get_inference_spec_files() -> dict[str, pathlib.Path]:
    files: dict[str, pathlib.Path] = {}

    for spec_dir in get_all_inference_spec_dirs("engines"):

        # Give preference to .yaml, then .json spec files
        file_extensions = ["*.yaml", "*.yml", "*.json"]
        for file_extension in file_extensions:
            # On naming collisions, i.e. muliple specs for one inference engine, prefer the
            # spec files discovered later (i.e. user-level > system-level)
            for spec_file in sorted(pathlib.Path(spec_dir).glob(file_extension)):
                file = pathlib.Path(spec_file)
                runtime = file.stem
                files[runtime] = file

    return files


def get_inference_schema_files() -> dict[str, pathlib.Path]:
    files: dict[str, pathlib.Path] = {}

    for schema_dir in get_all_inference_spec_dirs("schema"):

        for spec_file in sorted(pathlib.Path(schema_dir).glob("schema.*.json")):
            file = pathlib.Path(spec_file)
            version = file.name.replace("schema.", "").replace(".json", "")
            files[version] = file

    return files