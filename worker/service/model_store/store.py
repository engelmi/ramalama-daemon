import os
import re
import pathlib
from dataclasses import dataclass
from typing import List, Dict, Optional

from worker.service.model_store.reffile import RefJSONFile
from worker.service.model_store.error import NoRefFileFound, NoGGUFModelFileFound


DIRECTORY_NAME_BLOBS = "blobs"
DIRECTORY_NAME_REFS = "refs"
DIRECTORY_NAME_SNAPSHOTS = "snapshots"

def sanitize_filename(filename: str) -> str:
    return filename.replace(":", "-")

SPLIT_MODEL_PATH_RE = r'(.*?)(?:/)?([^/]*)-00001-of-(\d{5})\.gguf'

def is_split_file_model(model_path):
    """returns true if ends with -%05d-of-%05d.gguf"""
    return bool(re.match(SPLIT_MODEL_PATH_RE, model_path))

@dataclass
class ModelFile:
    name: str
    modified: float
    size: int
    is_partial: bool

@dataclass
class StoredModelIdentifier:
    model_source: str
    model_organization: str
    model_name: str
    model_tag: str

class StoredModel:

    def __init__(
        self,
        store_path: pathlib.Path,
        model_identifier: StoredModelIdentifier
    ):
        self._store_path = store_path
        self._model_source = model_identifier.model_source
        self._model_organization = model_identifier.model_organization
        self._model_name = model_identifier.model_name
        self._model_tag = model_identifier.model_tag

    @property
    def model_base_directory(self) -> pathlib.Path:
        return self._store_path / self._model_source / self._model_organization / self._model_name

    @property
    def blobs_directory(self) -> pathlib.Path:
        return self.model_base_directory / DIRECTORY_NAME_BLOBS

    @property
    def refs_directory(self) -> pathlib.Path:
        return self.model_base_directory / DIRECTORY_NAME_REFS

    @property
    def snapshots_directory(self) -> pathlib.Path:
        return self.model_base_directory / DIRECTORY_NAME_SNAPSHOTS

    def get_ref_file_path(self) -> pathlib.Path:
        return self.refs_directory / f"{self._model_tag}.json"

    def get_ref_file(self) -> RefJSONFile:
        ref_file_path = self.get_ref_file_path()
        if os.path.exists(ref_file_path):
            return RefJSONFile.from_path(ref_file_path)
        
        raise NoRefFileFound(self._model_source, self._model_organization, self._model_name, self._model_tag)
    
    def get_snapshot_directory_from_ref_file(self, ref_file: RefJSONFile) -> pathlib.Path:
        return self.snapshots_directory / sanitize_filename(ref_file.hash)

    def get_snapshot_file_path_from_ref_file(self, ref_file: RefJSONFile, filename: str) -> pathlib.Path:
        return self.get_snapshot_directory_from_ref_file(ref_file) / filename

    def get_entry_model_path(self) -> pathlib.Path:
        ref_file: RefJSONFile = self.get_ref_file()
        gguf_files = ref_file.model_files
        safetensor_files = ref_file.safetensor_model_files
        if safetensor_files:
            return self.get_snapshot_directory_from_ref_file(ref_file)
        elif not gguf_files:
            raise NoGGUFModelFileFound()

        # Use the first model file found, but...
        model_file = gguf_files[0]
        # ...if its a split model, use the file with index 1
        if is_split_file_model(self._model_name):
            index_models = [file for file in gguf_files if "-00001-of-" in file.name]
            if len(index_models) != 1:
                raise Exception(f"Found multiple index 1 gguf models: {index_models}")
            model_file = index_models[0]
        return self.get_snapshot_file_path_from_ref_file(ref_file, model_file.name)
    
    def get_mmproj_path(self) -> Optional[pathlib.Path]:
        ref_file: RefJSONFile = self.get_ref_file()
        if not ref_file.mmproj_files:
            return None

        # Use the first mmproj file
        mmproj_file = ref_file.mmproj_files[0]
        return self.get_snapshot_file_path_from_ref_file(ref_file, mmproj_file.name)

    def get_chat_template_path(self) -> Optional[pathlib.Path]:
        ref_file: RefJSONFile = self.get_ref_file()
        if not ref_file.chat_templates:
            return None

        # Use the last chat template file (may have been go template converted to jinja)
        chat_template_file = ref_file.chat_templates[-1]
        return self.get_snapshot_file_path_from_ref_file(ref_file, chat_template_file.name)


class GlobalModelStore:
    def __init__(
        self,
        base_path: pathlib.Path,
    ):
        self._store_base_path = base_path

    @property
    def path(self) -> pathlib.Path:
        return self._store_base_path

    def list_models(self) -> Dict[str, List[ModelFile]]:
        models: Dict[str, List[ModelFile]] = {}

        for root, subdirs, _ in os.walk(self.path):
            if DIRECTORY_NAME_REFS in subdirs:
                ref_dir = os.path.join(root, DIRECTORY_NAME_REFS)
                for ref_file_name in os.listdir(ref_dir):
                    ref_file_path = os.path.join(ref_dir, ref_file_name)
                    ref_file = RefJSONFile.from_path(ref_file_path)

                    model_path = root.replace(f"{self.path}", "").replace(os.sep, "", 1)

                    parts = model_path.split(os.sep)
                    model_source = parts[0]
                    model_path_without_source = "/".join(parts[1:])

                    separator = ":///" if model_source == "file" else "://"  # Use ':///' for file URLs, '://' otherwise
                    tag = ref_file_name.replace(".json", "")
                    model_name = f"{model_source}{separator}{model_path_without_source}:{tag}"

                    collected_files = []
                    for snapshot_file in ref_file.files:
                        is_partially_downloaded = False
                        snapshot_file_path = os.path.join(
                            root, DIRECTORY_NAME_SNAPSHOTS, ref_file.hash, snapshot_file.name
                        )
                        if not os.path.exists(snapshot_file_path):
                            blobs_partial_file_path = os.path.join(
                                root, DIRECTORY_NAME_BLOBS, ref_file.hash + ".partial"
                            )
                            if not os.path.exists(blobs_partial_file_path):
                                continue

                            snapshot_file_path = blobs_partial_file_path
                            is_partially_downloaded = True

                        last_modified = os.path.getmtime(snapshot_file_path)
                        file_size = os.path.getsize(snapshot_file_path)
                        collected_files.append(
                            ModelFile(snapshot_file.name, last_modified, file_size, is_partially_downloaded)
                        )
                    models[model_name] = collected_files

        return models

    def get_stored_model(self, stored_model_id: StoredModelIdentifier) -> StoredModel:
        return StoredModel(self.path, stored_model_id)
