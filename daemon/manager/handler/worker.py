from flask_smorest import Blueprint
from flask import abort

from daemon.logger import logger
from daemon.client.worker.api_client import ApiClient, Configuration
from daemon.client.worker.api.worker_api_api import WorkerApiApi, ModelServeRequestDTO as WorkerModelServeRequestDTO
from daemon.data.shared import REGISTERED_WORKER, RegisteredWorker
from daemon.manager.dto.worker import WorkerRegistrationDTO, RegisteredWorkerDTO, WorkerUnregistrationDTO
from daemon.manager.dto.model import AvailableModelDTO, ModelServeRequestDTO, ModelStopRequestDTO, ModelServeResponseDTO

def setup_handler(blp: Blueprint):

    @blp.route("/worker", methods=["GET"])
    @blp.response(200, RegisteredWorkerDTO(many=True))
    def get_workers():
        logger.debug("/worker called")

        rw: list[dict] = []
        for _, worker in REGISTERED_WORKER.items():
            rw.append({"name": worker.name, "host": worker.host, "api_port": worker.api_port})

        return rw

    @blp.route("/worker/register", methods=["POST"])
    @blp.arguments(WorkerRegistrationDTO)
    @blp.response(201)
    def post_workers_register(worker_data):
        logger.debug("/worker/register called")

        w = WorkerRegistrationDTO.from_dict(worker_data)
        REGISTERED_WORKER.add(w.name, RegisteredWorker(name=w.name, host=w.host, api_port=w.api_port))

    @blp.route("/worker/unregister", methods=["DELETE"])
    @blp.response(204)
    def delete_workers_unregister(worker_data):
        logger.debug("/worker/unregister called")

        w = WorkerUnregistrationDTO.from_dict(worker_data)
        REGISTERED_WORKER.remove(w.name)

    @blp.route("/worker/<name>", methods=["GET"])
    @blp.response(200, RegisteredWorkerDTO)
    def get_workers_models(name):
        logger.debug(f"/worker/{name} called")
        
        worker = REGISTERED_WORKER.get(name)
        if worker is None:
            logger.debug(f"'{name}' not found as registered worker")
            abort(404)
        
        return {"name": worker.name, "host": worker.host, "api_port": worker.api_port}

    @blp.route("/worker/<name>/models", methods=["GET"])
    @blp.response(200, AvailableModelDTO(many=True))
    def get_workers_models(name):
        logger.debug(f"/worker/{name}/models called")
        
        worker = REGISTERED_WORKER.get(name)
        if worker is None:
            logger.debug(f"'{name}' not found as registered worker")
            abort(404)
        
        ret: list[dict] = []
        conf = Configuration(host=f"{worker.host}:{worker.api_port}")
        with ApiClient(conf) as client:
            models = WorkerApiApi(client).api_models_get()
            for model in models:
                ret.append({"worker": worker.name, "name": model.name, "size": model.size, "modified": model.modified}) 

        return ret

    @blp.route("/worker/<name>/models/<model>", methods=["GET"])
    @blp.response(200)
    def get_workers_model(name, model):
        logger.debug(f"/worker/{name}/models/{model} called")

    @blp.route("/worker/<name>/models/serve", methods=["POST"])
    @blp.arguments(ModelServeRequestDTO)
    @blp.response(200, ModelServeResponseDTO)
    def post_workers_model_start(serve_request, name):
        logger.debug(f"/worker/{name}/models/serve called")

        worker = REGISTERED_WORKER.get(name)
        if worker is None:
            logger.debug(f"'{name}' not found as registered worker")
            abort(404)

        conf = Configuration(host=f"{worker.host}:{worker.api_port}")
        with ApiClient(conf) as client:
            resp = WorkerApiApi(client).api_models_serve_post(WorkerModelServeRequestDTO.from_dict(serve_request))
            
            return {"model_id": resp.model_id, "chat_path": f"/proxy/{worker.name}/{resp.model_id}/chat"}

    @blp.route("/worker/<name>/models/stop", methods=["POST"])
    @blp.arguments(ModelStopRequestDTO)
    @blp.response(200)
    def post_workers_model_stop(stop_request, name):
        logger.debug(f"/worker/{name}/models/stop called")

        worker = REGISTERED_WORKER.get(name)
        if worker is None:
            logger.debug(f"'{name}' not found as registered worker")
            abort(404)

        return ""