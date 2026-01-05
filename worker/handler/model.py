import io
import pathlib
import traceback
from flask_smorest import Blueprint

from worker.logger import logger
from worker.service.model_store.store import GlobalModelStore
from worker.dto.model import AvailableModelDTO, ModelServeRequestDTO, ModelStopRequestDTO, ModelServeResponseDTO
from worker.service.model_runner.runner import ModelRunner
from worker.data.shared import SERVED_MODELS


def get_exception_traceback_str(exc: Exception) -> str:
    file = io.StringIO()
    traceback.print_exception(exc, file=file)
    return file.getvalue().rstrip()

class Config:

    def __init__(self, model_store_dir: str):
        self.model_store_dir = pathlib.Path(model_store_dir)

def setup_handler(blp: Blueprint, config: Config):

    store = GlobalModelStore(config.model_store_dir)
    model_runner = ModelRunner(store)

    @blp.route("/models", methods=["GET"])
    @blp.response(200, AvailableModelDTO(many=True))
    def get_models():
        logger.debug("/models called")

        ret: list[dict] = []
        for name, model_files in store.list_models().items():
            size_sum = 0
            last_modified = 0.0
            for file in model_files:
                size_sum += file.size
                last_modified = max(file.modified, last_modified)
            
            ret.append({"name": name, "size": size_sum, "modified": last_modified})

        return ret

    @blp.route("/models/<id>", methods=["GET"])
    @blp.response(200)
    def get_models_model(id):
        logger.debug(f"/models/{id} called")

    @blp.route("/models/serve", methods=["POST"])
    @blp.arguments(ModelServeRequestDTO)
    @blp.response(200, ModelServeResponseDTO)
    def post_models_model_start(serve_request):
        logger.debug(f"/models/serve called")

        srequest: ModelServeRequestDTO = ModelServeRequestDTO.from_dict(serve_request)
        try:
            served_model = model_runner.serve_model(srequest.model, srequest.inference_options, srequest.serve_options)
            # add the model id and its port to the served model map for the proxy to forward requests properly
            SERVED_MODELS[served_model.model_id] = served_model.port

            return {"model_id": served_model.model_id}
        except Exception as ex:
            logger.error(f"{srequest.model}: Failed to serve model: {ex}")
            logger.debug(f"{srequest.model}: {get_exception_traceback_str(ex)}")
            raise ex

    @blp.route("/models/stop", methods=["POST"])
    @blp.arguments(ModelStopRequestDTO)
    @blp.response(200)
    def post_models_model_stop(stop_request):
        logger.debug(f"/models/stop called")

        srequest: ModelStopRequestDTO = ModelStopRequestDTO.from_dict(stop_request)
        try:
            model_id = model_runner.stop_model(srequest.model)
            # remove the model id from the served model map to stop the proxy to forward requests
            del SERVED_MODELS[model_id]
        except Exception as ex:
            logger.error(f"{srequest.model}: Failed to stop model: {ex}")
            logger.debug(f"{srequest.model}: {get_exception_traceback_str(ex)}")
            raise ex
