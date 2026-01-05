from flask_smorest import Blueprint

from daemon.logger import logger
from daemon.data.shared import REGISTERED_WORKER
from daemon.client.worker.api_client import ApiClient, Configuration
from daemon.client.worker.api.worker_api_api import WorkerApiApi
from daemon.manager.dto.model import AvailableModelDTO

def setup_handler(blp: Blueprint):

    @blp.route("/models", methods=["GET"])
    @blp.response(200, AvailableModelDTO(many=True))
    def get_models():
        logger.debug("/models called")
        
        ret: list[dict] = []
        for _, worker in REGISTERED_WORKER.items():
            
            conf = Configuration(host=f"{worker.host}:{worker.api_port}")
            with ApiClient(conf) as client:
                models = WorkerApiApi(client).api_models_get()
                for model in models:
                    ret.append({"worker": worker.name, "name": model.name, "size": model.size, "modified": model.modified})

        return ret
