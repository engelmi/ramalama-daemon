import os
import argparse
import socket

from worker.version import version

def abspath(astring) -> str:
    return os.path.abspath(astring)

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
        "--host",
        default="127.0.0.1",
        help="host for AI Model server to listen on",
    )
    parser.add_argument(
        "-p",
        "--port",
        type=parse_port_option,
        default="8080",
        help="port for AI Model server to listen on",
    )
    parser.add_argument(
        "--name",
        dest="name",
        default=socket.gethostname(),
        help="name of the worker used to register at the ramalama-daemon",
    )
    # default="/var/ramalama/store",
    parser.add_argument(
        "--store",
        default="/home/mengel/.local/share/ramalama/store",
        type=abspath,
        help="store directory the AI Models are located",
    )

    parser.add_argument(
        "--daemon-host",
        dest="daemon_host",
        default="127.0.0.1",
        help="host of the ramalama-daemon to register at",
    )
    parser.add_argument(
        "--daemon-port",
        dest="daemon_port",
        type=parse_port_option,
        default="8080",
        help="port of the ramalama-daemon to register at",
    )

    return parser.parse_args()
