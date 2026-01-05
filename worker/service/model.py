from urllib.parse import urlparse
from enum import Enum, StrEnum

class ModelSource(Enum):
    HUGGINGFACE=1
    MODELSCOPE=2
    OLLAMA=3
    OCI=4
    RLCR=5
    URL=6

# This corresponds to the ramalama configuration option for transport
class ModelTransport(StrEnum):
    HUGGINGFACE="huggingface"
    MODELSCOPE="modelscope"
    OLLAMA="ollama"
    OCI="oci"
    RLCR="rlcr"
    URL="url"
    

def detect_model_source(model_input: str, transport: ModelTransport = ModelTransport.OLLAMA) -> ModelSource:
    for prefix in ["huggingface://", "hf://", "hf.co/"]:
        if model_input.startswith(prefix):
            return ModelSource.HUGGINGFACE
    for prefix in ["modelscope://", "ms://"]:
        if model_input.startswith(prefix):
            return ModelSource.MODELSCOPE
    for prefix in ["ollama://", "ollama.com/library/"]:
        if model_input.startswith(prefix):
            return ModelSource.OLLAMA
    for prefix in ["oci://", "docker://"]:
        if model_input.startswith(prefix):
            return ModelSource.OCI
    if model_input.startswith("rlcr://"):
        return ModelSource.RLCR
    for prefix in ["http://", "https://", "file://"]:
        if model_input.startswith(prefix):
            return ModelSource.URL
        
    if transport == ModelTransport.OLLAMA:
        return ModelSource.OLLAMA
    if transport == ModelTransport.HUGGINGFACE:
        return ModelSource.HUGGINGFACE
    if transport == ModelTransport.MODELSCOPE:
        return ModelSource.MODELSCOPE
    if transport == ModelTransport.OCI:
        return ModelSource.OCI
    if transport == ModelTransport.RLCR:
        return ModelSource.RLCR
    if transport == ModelTransport.URL:
        return ModelSource.URL
    
    raise KeyError(f'transport "{transport}" not supported. Must be oci, huggingface, modelscope, or ollama.')


def rm_until_substring(input: str, substring: str) -> str:
    pos = input.find(substring)
    if pos == -1:
        return input
    return input[pos + len(substring) :]

def prune_model_input(model_input: str) -> tuple[ModelSource, str]:
    # remove protocol from model input
    pruned_model_input = rm_until_substring(model_input, "://")

    model_source = detect_model_source(model_input)
    if model_source == ModelSource.HUGGINGFACE:
        pruned_model_input = rm_until_substring(pruned_model_input, "hf.co/")
    elif model_source == ModelSource.MODELSCOPE:
        pruned_model_input = rm_until_substring(pruned_model_input, "modelscope.cn/")
    elif model_source == ModelSource.OLLAMA:
        pruned_model_input = rm_until_substring(pruned_model_input, "ollama.com/library/")

    return (model_source, pruned_model_input)

def extract_model_identifiers(model_input: str) -> tuple[str, str, str, str]:
    model_source, pruned_model_input = prune_model_input(model_input)

    # use pruned model input for base model name
    model_name = pruned_model_input
    model_tag = "latest"
    model_organization = ""
    model_source_id = ""

    # extract model tag from name if exists
    if ":" in model_name:
        model_name, model_tag = model_name.split(":", 1)

    # extract model organization from name if exists and update name
    split = model_name.rsplit("/", 1)
    model_organization = split[0].removeprefix("/") if len(split) > 1 else ""
    model_name = split[1] if len(split) > 1 else split[0]

    if model_source == ModelSource.HUGGINGFACE:
        model_source_id = "huggingface"
        # if it is a repo then normalize the case insensitive quantization tag
        if '/' not in model_organization and model_tag != "latest":
            model_tag = model_tag.upper()
    elif model_source == ModelSource.MODELSCOPE:
        model_source_id = "modelscope"
    elif model_source == ModelSource.OLLAMA:
        model_source_id = "ollama"
        # use the ollama default namespace if no model organization has been identified
        model_organization = "library" if not model_organization else model_organization
    elif model_source == ModelSource.URL:
        model_source_id = urlparse(model_input).scheme
        parts = model_organization.split("/")
        if len(parts) > 2 and parts[-2] == "blob":
            model_organization = "/".join(parts[:-2])
            model_tag = parts[-1]

        # handling huggingface specific URLs for more precise identifiers
        if len(parts) > 2 and "https://huggingface.co".endswith(parts[0]) and parts[-2] == "resolve":
            model_organization = "/".join(parts[:-2])
            model_tag = parts[-1]

        if len(parts) > 3 and parts[-3] == "file":
            model_organization = "/".join(parts[:-3])
            model_tag = parts[-1]

        # handling modelscope specific URLs for more precise identifiers
        if len(parts) > 2 and "https://modelscope.cn".endswith(parts[0]) and parts[-2] == "resolve":
            model_organization = "/".join(parts[:-2])
            model_tag = parts[-1]
    elif model_source in [ModelSource.OCI, ModelSource.RLCR]:
        model_source_id = "oci"

    return model_source_id, model_name, model_tag, model_organization
