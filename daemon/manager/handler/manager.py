from flask_smorest import Blueprint

from daemon.logger import logger

def setup_handler(blp: Blueprint):

    @blp.route("/config", methods=["GET"])
    @blp.response(200)
    def get_config():
        logger.debug("/config called")

    @blp.route("/config/reload", methods=["POST"])
    @blp.response(200)
    def post_config_reload():
        logger.debug("/config/reload called")
