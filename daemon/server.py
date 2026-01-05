#!/usr/bin/env python3

import os
from pathlib import Path
from flask import Flask
from flask_smorest import Api

from daemon.cli import setup_cli
from daemon.proxy import routes as proxy_routes
from daemon.manager import routes as mgr_routes
from daemon.logger import configure_logger, LogLevel, LOGGER_NAME

BASE_DIR = Path(os.path.abspath(os.path.dirname(__file__)))

def setup_server() -> tuple[Flask, Api]:
    app = Flask(LOGGER_NAME, template_folder=BASE_DIR / "manager" / "templates")

    # General OpenAPI configuration
    app.config["API_TITLE"] = "Ramalama-Daemon REST API"
    app.config["API_VERSION"] = "1.0"
    app.config["OPENAPI_VERSION"] = "3.0.3"
    
    # Location of the generated OpenAPI spec
    app.config["OPENAPI_URL_PREFIX"] = ""
    app.config["OPENAPI_JSON_PATH"] = "openapi.json"

    api = Api(app)
    mgr_routes.setup(api)
    proxy_routes.setup(api)

    return (app, api)

def main():
    args = setup_cli()
    configure_logger(lvl=LogLevel.DEBUG, log_file=None)

    app, _ = setup_server()
    app.run(debug = False, port=args.port)


if __name__ == "__main__":
    main()
