from flask import render_template, make_response
from flask_smorest import Blueprint
from typing import Any

from daemon.data.shared import REGISTERED_WORKER
from daemon.client.worker.api_client import ApiClient, Configuration
from daemon.client.worker.api.worker_api_api import WorkerApiApi

def setup_handler(blp: Blueprint):
    
    def get_models() -> dict[str, Any]:
        data: dict = {}
        for _, worker in REGISTERED_WORKER.items():
            
            available_models = []
            conf = Configuration(host=f"{worker.host}:{worker.api_port}")
            with ApiClient(conf) as client:
                models = WorkerApiApi(client).api_models_get()
                for model in models:
                    available_models.append(model.name)

            data[worker.name] = {
                "models": available_models
            }
        
        return data

    @blp.route("/", methods=["GET"])
    @blp.route("/ui", methods=["GET"])
    @blp.response(200, content_type="text/html")
    def index():
        data = get_models()
        resp = make_response(render_template("index.html", data=data))
        resp.mimetype = "text/html"
        return resp
