import requests
from flask import request, Response, redirect, url_for
from flask_smorest import Blueprint

from worker.data.shared import SERVED_MODELS


def setup_handler(blp: Blueprint):

    def proxy(model, path):
        port = SERVED_MODELS.get(model)
        resp = requests.get(f"http://localhost:{port}/{path}")
        excluded_headers = ["content-encoding", "content-length", "transfer-encoding", "connection"]
        headers = [(name, value) for (name, value) in  resp.raw.headers.items() if name.lower() not in excluded_headers]
        response = Response(resp.content, resp.status_code, headers)
        return response


    @blp.route("/", methods=["GET"])
    @blp.response(200)
    def get_index():
        return "This is the proxy of ramalama-worker"

    @blp.route("/<model>", methods=["GET"])
    @blp.response(200)
    def get_model_proxy_path(model):
        return redirect(url_for("worker-proxy.get_model_chat_proxy", model=model, path=""))

    @blp.route("/<model>/<path:path>", methods=["GET"])
    @blp.response(200)
    def get_model_proxy_path(model, path):
        return proxy(model, path)

    @blp.route("/<model>/chat", defaults={"path": ""}, methods=["GET"])
    @blp.response(200)
    def get_model_chat_proxy(model, path):
        return proxy(model, path)

    @blp.route("/<model>/v1/chat/completions", methods=["POST"])
    @blp.response(200)
    def post_model_chat_completions(model):
        port = SERVED_MODELS.get(model)

        def stream_completions(payload):
            with requests.post(f"http://localhost:{port}/v1/chat/completions", json=payload, stream=True) as stream:
                stream.raise_for_status()
                for chunk in stream.iter_content(chunk_size=1024):
                    if chunk:
                        yield chunk

        return Response(stream_completions(request.get_json()), mimetype="text/event-stream")
