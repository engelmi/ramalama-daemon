import argparse

from daemon.version import version

def parse_port_option(option: str) -> str:
    port = int(option)
    if port <= 0 or port >= 65535:
        raise ValueError(f"Invalid port '{port}'")
    return option

def setup_cli():
    parser = argparse.ArgumentParser(
        description="ramalama-daemon - Background service managing AI workloads",
        formatter_class=argparse.RawTextHelpFormatter,
    )

    parser.add_argument("--version", action="version", version=version())
    parser.add_argument(
        "-p",
        "--port",
        type=parse_port_option,
        default="8080",
        help="port for AI Model server to listen on",
    )

    return parser.parse_args()
