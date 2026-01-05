import threading
from dataclasses import dataclass
from typing import Optional, Generic, TypeVar, Generator

T = TypeVar("T")

class ThreadsafeDict(Generic[T]):

    def __init__(self):
        self.lock = threading.Lock()
        self._model_port_map: dict[str, T] = {}

    def items(self) -> Generator[tuple[str, T], None, None]:
        with self.lock:
            for key, value in self._model_port_map.items():
                yield (key, value)

    def get(self, key: str) -> Optional[T]:
        return self._model_port_map.get(key)
    
    def add(self, key: str, value: T):
        with self.lock:
            self._model_port_map[key] = value
    
    def remove(self, key: str):
        with self.lock:
            del self._model_port_map[key]

@dataclass
class AvailableModel:
    model_name: str

@dataclass
class RegisteredWorker:
    name: str
    host: str
    api_port: int

REGISTERED_WORKER = ThreadsafeDict[RegisteredWorker]()
