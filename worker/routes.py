from flask_smorest import Blueprint, Api

from worker.handler import model, proxy

api_blp = Blueprint("worker-api", "rest-api", url_prefix="/api")
proxy_blp = Blueprint("worker-proxy", "proxy", url_prefix="/proxy")


def setup(api: Api, model_store_dir: str):
    model.setup_handler(api_blp, model.Config(model_store_dir))
    api.register_blueprint(api_blp)

    proxy.setup_handler(proxy_blp)
    api.register_blueprint(proxy_blp)
