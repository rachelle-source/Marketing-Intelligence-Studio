import json
from pathlib import Path
from src.models import ClientConfig

REQUIRED_FIELDS = ["client_name", "subreddits", "keywords", "brand_context", "notify_email", "max_threads", "sort"]
VALID_SORTS = {"hot", "new", "top"}

class ConfigError(Exception):
    pass

def load_config(path: str) -> ClientConfig:
    config_path = Path(path)
    if not config_path.exists():
        raise ConfigError(f"Config file not found: {path}")

    with open(config_path) as f:
        data = json.load(f)

    for field in REQUIRED_FIELDS:
        if field not in data:
            raise ConfigError(f"Missing required field: '{field}' in {path}")

    if data["sort"] not in VALID_SORTS:
        raise ConfigError(f"sort must be one of {VALID_SORTS}, got '{data['sort']}'")

    return ClientConfig(
        client_name=data["client_name"],
        subreddits=data["subreddits"],
        keywords=data["keywords"],
        brand_context=data["brand_context"],
        notify_email=data["notify_email"],
        max_threads=data["max_threads"],
        sort=data["sort"],
    )
