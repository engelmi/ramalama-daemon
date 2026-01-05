import json
from dataclasses import dataclass
from enum import StrEnum


class StoreFileType(StrEnum):
    GGUF_MODEL = "gguf"
    SAFETENSOR_MODEL = "safetensor"
    MMPROJ = "mmproj"
    CHAT_TEMPLATE = "chat_template"
    OTHER = "other"

    @staticmethod
    def from_str(s: str) -> "StoreFileType":
        if s == StoreFileType.GGUF_MODEL.value:
            return StoreFileType.GGUF_MODEL
        if s == StoreFileType.SAFETENSOR_MODEL.value:
            return StoreFileType.SAFETENSOR_MODEL
        if s == StoreFileType.MMPROJ.value:
            return StoreFileType.MMPROJ
        if s == StoreFileType.CHAT_TEMPLATE.value:
            return StoreFileType.CHAT_TEMPLATE
        return StoreFileType.OTHER


@dataclass
class StoreFile:
    hash: str
    name: str
    type: StoreFileType


@dataclass
class RefJSONFile:
    hash: str
    path: str
    files: list[StoreFile]

    version: str = "v1.0.1"

    def to_json(self) -> str:
        return json.dumps(self, default=lambda o: o.__dict__, sort_keys=True, indent=2)

    def write_to_file(self):
        with open(self.path, "w") as file:
            file.write(self.to_json())
            file.flush()

    @property
    def model_files(self) -> list[StoreFile]:
        return [file for file in self.files if file.type == StoreFileType.GGUF_MODEL]

    @property
    def safetensor_model_files(self) -> list[StoreFile]:
        return [file for file in self.files if file.type == StoreFileType.SAFETENSOR_MODEL]

    @property
    def chat_templates(self) -> list[StoreFile]:
        return [file for file in self.files if file.type == StoreFileType.CHAT_TEMPLATE]

    @property
    def mmproj_files(self) -> list[StoreFile]:
        return [file for file in self.files if file.type == StoreFileType.MMPROJ]

    def remove_file(self, hash: str):
        for file in self.files:
            if file.hash == hash:
                self.files.remove(file)
                break

    @staticmethod
    def from_path(path: str) -> "RefJSONFile":
        with open(path, "r") as f:
            data = json.loads(f.read())

            ref_version = data["version"]
            ref_hash = data["hash"]
            ref_path = path
            ref_files = []
            for file in data["files"]:
                file_hash = file["hash"]
                file_name = file["name"]
                file_type = StoreFileType.from_str(file["type"])
                ref_files.append(StoreFile(file_hash, file_name, file_type))

            ref_file = RefJSONFile(
                version=ref_version,
                hash=ref_hash,
                path=ref_path,
                files=ref_files,
            )
            
            return ref_file
