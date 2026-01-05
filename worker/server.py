#!/usr/bin/env python3

from flask import Flask
from flask_smorest import Api

from worker.cli import setup_cli
from worker.routes import setup

from worker.client.daemon.api_client import ApiClient, Configuration
from worker.client.daemon.api.daemon_api_api import DaemonApiApi
from worker.client.daemon.api.daemon_api_api import WorkerRegistrationDTO
from worker.logger import configure_logger, logger, LogLevel


def setup_server(model_store_dir: str) -> tuple[Flask, Api]:
    app = Flask(__name__)

    # General OpenAPI configuration
    app.config["API_TITLE"] = "Ramalama-Worker REST API"
    app.config["API_VERSION"] = "1.0"
    app.config["OPENAPI_VERSION"] = "3.0.3"

    # Location of the generated OpenAPI spec
    app.config["OPENAPI_URL_PREFIX"] = ""
    app.config["OPENAPI_JSON_PATH"] = "openapi.json"

    api = Api(app)
    setup(api, model_store_dir)

    return (app, api)

def register(name: str, server_host: str, server_port: int, daemon_host: str, daemon_port: str) -> bool:
    daemon_url = f"{daemon_host}:{daemon_port}"
    conf = Configuration(host=daemon_url)
    with ApiClient(conf) as client:
        w = WorkerRegistrationDTO(name=name, host=server_host, api_port=server_port)
        DaemonApiApi(client).api_worker_register_post(w)
    logger.info(f"Successfully registered at daemon '{daemon_url}'")

def main():
    args = setup_cli()
    configure_logger(lvl=LogLevel.DEBUG, log_file=None)

    app, _ = setup_server(args.store)
    register(args.name, args.host, int(args.port), args.daemon_host, args.daemon_port)

    app.run(debug = False, host=args.host, port=args.port)

if __name__ == "__main__":
    main()
