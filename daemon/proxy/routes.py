import requests
from flask import request, Response, redirect, url_for, abort
from flask_smorest import Blueprint, Api

from daemon.logger import logger
from daemon.data.shared import REGISTERED_WORKER


def setup_handler(blp: Blueprint):

    def proxy(worker_name: str, model: str, path: str) -> Response:
        worker = REGISTERED_WORKER.get(worker_name)
        if worker is None:
            if worker is None:
                logger.debug(f"'{worker_name}' not found as registered worker")
                abort(404)

        resp = requests.get(f"http://{worker.host}:{worker.api_port}/proxy/{model}/{path}")
        excluded_headers = ["content-encoding", "content-length", "transfer-encoding", "connection"]
        headers = [(name, value) for (name, value) in  resp.raw.headers.items() if name.lower() not in excluded_headers]
        response = Response(resp.content, resp.status_code, headers)
        return response


    @blp.route("/", methods=["GET"])
    @blp.response(200)
    def get_index():
        return "This is the proxy of ramalama-worker"

    @blp.route("/<worker>/<model>", methods=["GET"])
    @blp.response(200)
    def get_model_proxy_path(worker, model):
        return redirect(url_for("worker-proxy.get_model_chat_proxy", worker=worker, model=model, path=""))

    @blp.route("/<worker>/<model>/<path:path>", methods=["GET"])
    @blp.response(200)
    def get_model_proxy_path(worker, model, path):
        return proxy(worker, model, path)

    @blp.route("/<worker>/<model>/chat", defaults={"path": ""}, methods=["GET"])
    @blp.response(200)
    def get_model_chat_proxy(worker, model, path):
        return proxy(worker, model, f"/chat{path}")

    @blp.route("/<worker>/<model>/v1/chat/completions", methods=["POST"])
    @blp.response(200)
    def post_model_chat_completions(worker, model):
        worker = REGISTERED_WORKER.get(worker)

        def stream_completions(payload):
            with requests.post(f"http://{worker.host}:{worker.api_port}/proxy/{model}/v1/chat/completions", json=payload, stream=True) as stream:
                stream.raise_for_status()
                for chunk in stream.iter_content(chunk_size=1024):
                    if chunk:
                        yield chunk

        return Response(stream_completions(request.get_json()), mimetype="text/event-stream")


def setup(api: Api):
    proxy_blp = Blueprint("daemon-proxy", "proxy", url_prefix="/proxy")
    setup_handler(proxy_blp)

    api.register_blueprint(proxy_blp)
