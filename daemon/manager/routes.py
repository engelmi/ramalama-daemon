from flask_smorest import Blueprint, Api

from daemon.manager.handler import manager, model, worker, ui

web_blp = Blueprint("daemon-web", "web-ui", url_prefix="/")
api_blp = Blueprint("daemon-api", "rest-api", url_prefix="/api")

def setup(api: Api):

    manager.setup_handler(api_blp)
    model.setup_handler(api_blp)
    worker.setup_handler(api_blp)
    api.register_blueprint(api_blp)

    ui.setup_handler(web_blp)
    api.register_blueprint(web_blp)
