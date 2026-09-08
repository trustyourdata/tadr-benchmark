import json
from pathlib import Path

import yaml

from ..models import CampaignManifest, Contract, ScenarioSpec


class UniqueKeyLoader(yaml.SafeLoader):
    pass


def unique_mapping(loader, node, deep=False):
    result = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in result:
            raise ValueError("duplicate mapping key")
        result[key] = loader.construct_object(value_node, deep=deep)
    return result


UniqueKeyLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, unique_mapping)


def load_model(path: Path, model: type[Contract]):
    if path.suffix not in {".yaml", ".yml", ".json"}:
        raise ValueError("specifications must be YAML or JSON")
    data = yaml.load(path.read_text(encoding="utf-8"), Loader=UniqueKeyLoader)
    # Re-enter via JSON to keep strict JSON array/object semantics uniform.
    return model.model_validate_json(json.dumps(data, allow_nan=False))


def load_campaign(path: Path) -> CampaignManifest:
    return load_model(path, CampaignManifest)


def load_scenario(path: Path) -> ScenarioSpec:
    return load_model(path, ScenarioSpec)
