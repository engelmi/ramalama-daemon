import threading
import hashlib
import subprocess
from datetime import datetime, timedelta
from typing import Optional

from worker.logger import logger
from worker.service.model_store.store import GlobalModelStore
from worker.service.model import extract_model_identifiers
from worker.service.inference.factory import assemble_command


class ServedModel:

    def __init__(self, model_id: str):
        self.model_id = model_id

    def setup(self, 
        serve_cmd: list[str],
        port: int,
        expires_after: timedelta,
    ):
        self.serve_cmd: list[str] = serve_cmd
        self.port: int = port

        self.expires_after = expires_after
        self.expiration_date: Optional[datetime] = None

        self.process: Optional[subprocess.Popen] = None

    def start(self):
        if self.process is not None:
            raise RuntimeError(f"Model {self.model_id} is already running.")
        self.update_expiration_date()
        self.process = subprocess.Popen(self.serve_cmd)

    def stop(self):
        if self.process:
            self.process.terminate()
            self.process.wait()
            self.process = None

    def update_expiration_date(self):
        self.expiration_date = datetime.now() + self.expires_after


class ModelRunner:

    def __init__(self, store: GlobalModelStore) -> None:
        self.store = store

        self._model_lock = threading.Lock()
        self._models: dict[str, ServedModel] = {}

        self._port_lock = threading.Lock()
        self._port_range: tuple[int, int] = (8081, 9080)
        self._used_ports: set[int] = set()

    @property
    def served_models(self) -> dict[str, ServedModel]:
        return self._models

    def next_available_port(self) -> int:
        with self._port_lock:
            for port in range(self._port_range[0], self._port_range[1] + 1):
                if port not in self._used_ports:
                    self._used_ports.add(port)
                    return port
        raise RuntimeError(f"No available ports in range {self._port_range[0]}-{self._port_range[1]}.")
    
    def model_id_from_input(self, model_input: str) -> str:
        source, name, tag, organization = extract_model_identifiers(model_input)
        hashable_identifier = f"{source}/{organization}/{name}/{tag}"

        h = hashlib.new("sha256")
        h.update(hashable_identifier.encode("utf-8"))
        return h.hexdigest()

    def serve_model(self, model_input: str, inference_options: dict[str, str], serve_options: dict[str, str]) -> ServedModel:
        model_id = self.model_id_from_input(model_input)

        new_served_model = ServedModel(model_id)
        with self._model_lock:
            if model_id in self._models:
                raise RuntimeError(f"Model with ID {model_id} already served.")
            
            self._models[model_id] = new_served_model
            logger.debug(f"{model_id}: Added to list of served models")
        
        try:
            port = self.next_available_port()
            logger.debug(f"{model_id}: Selected next available port '{port}'")
            inference_options["port"] = port

            serve_cmd = assemble_command(model_input, self.store.path, inference_options)
            logger.debug(f"{model_id}: Assembled serve command '{serve_cmd}'")

            expires_after_mins = serve_options.get("expires_after", 5)
            expires_after = timedelta(minutes=expires_after_mins)
            logger.debug(f"{model_id}: Served model will expire after {expires_after_mins}min of inactivity")

            new_served_model.setup(serve_cmd, port, expires_after)
            new_served_model.start()        
            logger.debug(f"{model_id}: Started serving model on port '{port}'")
        except Exception as ex:
            logger.error(f"Failed to serve model {model_id}: {ex}")
            del self._models[model_id]
            raise ex
        
        return new_served_model

    def stop_model(self, model_input: str) -> str:
        model_id = self.model_id_from_input(model_input)

        with self._model_lock:
            served_model = self._models.get(model_id, None)
            if served_model is None:
                raise RuntimeError(f"Model with ID {model_id} is not running.")

            served_model.stop()
            del self._models[model_id]
        
        with self._port_lock:
            self._used_ports.discard(served_model.port)
        
        return model_id

    def stop(self):
        for model_id in list(self._models.keys()):
            self.stop_model(model_id)
