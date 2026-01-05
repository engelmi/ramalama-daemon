import argparse
import pathlib
from typing import Optional, Any
from dataclasses import dataclass

from worker.service.hardware import check_nvidia, check_metal
from worker.service.model_store.store import GlobalModelStore, StoredModel, StoredModelIdentifier
from worker.service.model import extract_model_identifiers
from worker.logger import DEFAULT_LOG_DIR

@dataclass
class RamalamaArgsContext:
    cache_reuse: Optional[int] = 256
    container: Optional[bool] = False
    ctx_size: Optional[int] = 0
    debug: Optional[bool] = False
    host: Optional[str] = "0.0.0.0"
    gguf: Optional[str] = "Q4_K_M"
    logfile: Optional[str] = f"{DEFAULT_LOG_DIR / 'my.log'}"
    max_tokens: Optional[int] = 0
    model_draft: Optional[str] = None
    ngl: Optional[int] = -1
    port: Optional[int] = 8080
    runtime_args: Optional[str] = None
    seed: Optional[int] = None
    temp: Optional[float] = "0.8"
    thinking: Optional[bool] = True
    threads: Optional[int] = -1
    webui: Optional[bool] = True

    @staticmethod
    def from_dict(options: dict[str, Any]) -> "RamalamaArgsContext":
        ctx = RamalamaArgsContext()
        
        ctx.cache_reuse = options.get("cache_reuse", 256)
        ctx.container = options.get("container", False)
        ctx.ctx_size = options.get("ctx_size", 0)
        ctx.debug = options.get("debug", False)
        ctx.host = options.get("host", "0.0.0.0")
        ctx.gguf = options.get("gguf", "Q4_K_M")
        ctx.logfile = options.get("logfile", f"{DEFAULT_LOG_DIR / 'my.log'}")
        ctx.max_tokens = options.get("max_tokens", 0)
        ctx.model_draft = options.get("model_draft", None)
        ctx.ngl = options.get("ngl", -1)
        ctx.port = options.get("port", 8080)
        ctx.runtime_args = options.get("runtime_args", None)
        ctx.seed = options.get("seed", None)
        ctx.temp = options.get("temp", "0.8")
        ctx.thinking = options.get("thinking", True)
        ctx.threads = options.get("threads", -1)
        ctx.webui = options.get("webui", True)
        
        return ctx


class RamalamaRagGenArgsContext:

    def __init__(self) -> None:
        self.debug: Optional[bool]= None
        self.format: Optional[str]= None
        self.ocr: Optional[bool]= None
        self.inputdir: Optional[str] = None
        self.paths: Optional[list[str]] = None
        self.urls: Optional[list[str]] = None

    @staticmethod
    def from_argparse(args: argparse.Namespace) -> "RamalamaRagGenArgsContext":
        ctx = RamalamaRagGenArgsContext()
        ctx.debug = getattr(args, "debug", None)
        ctx.format = getattr(args, "format", None)
        ctx.ocr = getattr(args, "ocr", None)
        ctx.inputdir = getattr(args, "inputdir", None)
        ctx.paths = getattr(args, "PATHS", None)
        ctx.urls = getattr(args, "urls", None)
        return ctx


class RamalamaRagArgsContext:

    def __init__(self) -> None:
        self.debug: bool | None = None
        self.port: str | None = None
        self.model_host: str | None = None
        self.model_port: str | None = None

    @staticmethod
    def from_argparse(args: argparse.Namespace) -> "RamalamaRagArgsContext":
        ctx = RamalamaRagArgsContext()
        ctx.debug = getattr(args, "debug", None)
        ctx.port = getattr(args, "port", None)
        ctx.model_host = getattr(args, "model_host", None)
        ctx.model_port = getattr(args, "model_port", None)
        return ctx


class RamalamaModelContext:

    def __init__(self, store_path: pathlib.Path, model_input: str):
        self.model_input = model_input

        source_id, name, tag, organization = extract_model_identifiers(model_input)
        self.model_source_id = source_id
        self.model_name = name
        self.model_tag = tag
        self.model_organization = organization

        self.stored_model: StoredModel = GlobalModelStore(store_path).get_stored_model(StoredModelIdentifier(source_id, organization, name, tag))

    @property
    def name(self) -> str:
        return f"{self.model_name}:{self.model_tag}"

    @property
    def alias(self) -> str:
        return f"{self.model_organization}/{self.model_name}"

    @property
    def model_path(self) -> str:
        return self.stored_model.get_entry_model_path()

    @property
    def mmproj_path(self) -> Optional[str]:
        return self.stored_model.get_mmproj_path()

    @property
    def chat_template_path(self) -> Optional[str]:
        return self.stored_model.get_chat_template_path()


class RamalamaHostContext:

    def __init__(
        self, is_container: bool, uses_nvidia: bool, uses_metal: bool, should_colorize: bool, rpc_nodes: Optional[str]
    ):
        self.is_container = is_container
        self.uses_nvidia = uses_nvidia
        self.uses_metal = uses_metal
        self.should_colorize = should_colorize
        self.rpc_nodes = rpc_nodes


class RamalamaCommandContext:

    def __init__(
        self,
        args: RamalamaArgsContext | RamalamaRagGenArgsContext | RamalamaRagArgsContext,
        model: RamalamaModelContext | None,
        host: RamalamaHostContext,
    ):
        self.args = args
        self.model = model
        self.host = host
