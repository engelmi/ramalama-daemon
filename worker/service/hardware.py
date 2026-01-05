import os
import subprocess
import platform
import yaml
import json
from functools import lru_cache
from typing import Literal, TypedDict, Protocol

from worker.logger import logger

def quoted(arr) -> str:
    """Return string with quotes around elements containing spaces."""
    return " ".join(['"' + element + '"' if ' ' in element else element for element in arr])

def run_cmd(args, cwd=None, stdout=subprocess.PIPE, ignore_stderr=False, ignore_all=False, encoding=None, env=None):
    """
    Run the given command arguments.

    Args:
    args: command line arguments to execute in a subprocess
    cwd: optional working directory to run the command from
    stdout: standard output configuration
    ignore_stderr: if True, ignore standard error
    ignore_all: if True, ignore both standard output and standard error
    encoding: encoding to apply to the result text
    """

    logger.debug(f"run_cmd: {quoted(args)}")
    logger.debug(f"Working directory: {cwd}")
    logger.debug(f"Ignore stderr: {ignore_stderr}")
    logger.debug(f"Ignore all: {ignore_all}")
    logger.debug(f"env: {env}")

    serr = None
    if ignore_all or ignore_stderr:
        serr = subprocess.DEVNULL

    sout = stdout
    if ignore_all:
        sout = subprocess.DEVNULL

    if env:
        env = os.environ | env

    result = subprocess.run(args, check=True, cwd=cwd, stdout=sout, stderr=serr, encoding=encoding, env=env)
    logger.debug(f"Command finished with return code: {result.returncode}")

    return result


class CDI_DEVICE(TypedDict):
    name: str


class CDI_RETURN_TYPE(TypedDict):
    devices: list[CDI_DEVICE]


def get_podman_machine_cdi_config() -> CDI_RETURN_TYPE | None:
    cdi_config = run_cmd(["podman", "machine", "ssh", "cat", "/etc/cdi/nvidia.yaml"], encoding="utf-8").stdout.strip()
    if cdi_config:
        return yaml.safe_load(cdi_config)
    return None

def load_cdi_config(spec_dirs: list[str]) -> CDI_RETURN_TYPE | None:
    """ Loads the first YAML or JSON CDI configuration file found in the given directories."""

    for spec_dir in spec_dirs:
        for root, _, files in os.walk(spec_dir):
            for file in files:
                _, ext = os.path.splitext(file)
                file_path = os.path.join(root, file)
                if ext in [".yaml", ".yml"]:
                    try:
                        with open(file_path, "r") as stream:
                            return yaml.safe_load(stream)
                    except (OSError, yaml.YAMLError) as e:
                        logger.warning(f"Failed to load YAML file {file_path}: {e}")
                        continue
                elif ext == ".json":
                    try:
                        with open(file_path, "r") as stream:
                            return json.load(stream)
                    except (OSError, json.JSONDecodeError, UnicodeDecodeError) as e:
                        logger.warning(f"Failed to load JSON file {file_path}: {e}")
                        continue
    return None

def find_in_cdi(devices: list[str]) -> tuple[list[str], list[str]]:
    """ 
    Attempts to find a CDI configuration for each device in devices and returns a list of configured devices
    and a list of unconfigured devices.
    """

    if platform.system() == "Windows":
        cdi = get_podman_machine_cdi_config()
    else:
        cdi = load_cdi_config(['/var/run/cdi', '/etc/cdi'])
    try:
        cdi_devices = cdi.get("devices", []) if cdi else []
        cdi_device_names = [name for cdi_device in cdi_devices if (name := cdi_device.get("name"))]
    except (AttributeError, KeyError, TypeError) as e:
        # Malformed YAML or JSON. Treat everything as unconfigured but warn.
        logger.warning(f"Unable to process CDI configuration: {e}")
        return ([], devices)

    configured = []
    unconfigured = []
    for device in devices:
        if device in cdi_device_names:
            configured.append(device)
        # A device can be specified by a prefix of the uuid
        elif device.startswith("GPU") and any(name.startswith(device) for name in cdi_device_names):
            configured.append(device)
        else:
            logger.error(f"Device {device} does not have a CDI configuration")
            unconfigured.append(device)

    return configured, unconfigured

@lru_cache(maxsize=1)
def check_nvidia() -> Literal["cuda"] | None:
    try:
        command = ['nvidia-smi', '--query-gpu=index,uuid', '--format=csv,noheader']
        result = run_cmd(command, encoding="utf-8")
    except (OSError, subprocess.CalledProcessError):
        return None

    smi_lines = result.stdout.splitlines()
    parsed_lines: list[list[str]] = [[item.strip() for item in line.split(',')] for line in smi_lines if line]

    if not parsed_lines:
        return None

    indices, uuids = map(list, zip(*parsed_lines))
    # Get the list of devices specified by CUDA_VISIBLE_DEVICES, if any
    cuda_visible_devices = os.environ.get("CUDA_VISIBLE_DEVICES", "")
    visible_devices = cuda_visible_devices.split(',') if cuda_visible_devices else []
    for device in visible_devices:
        if device not in indices and not any(uuid.startswith(device) for uuid in uuids):
            logger.error(f"{device} not found")
            return None

    configured, unconfigured = find_in_cdi(visible_devices + ["all"])

    configured_has_all = "all" in configured
    if unconfigured and not configured_has_all:
        logger.error(f"No CDI configuration found for {','.join(unconfigured)}")
        logger.error("You can use the \"nvidia-ctk cdi generate\" command from the ")
        logger.error("nvidia-container-toolkit to generate a CDI configuration.")
        logger.error("See ramalama-cuda(7).")
        return None
    elif configured:
        if configured_has_all:
            configured.remove("all")
            if not configured:
                configured = indices

        os.environ["CUDA_VISIBLE_DEVICES"] = ','.join(configured)
        return "cuda"

    return None


class ContainerArgType(Protocol):
    container: bool | None

def check_metal() -> bool:
    return platform.system() == "Darwin"
