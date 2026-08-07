import json
import pytest
from pathlib import Path
from src.config import load_config, ConfigError

def test_load_valid_config(tmp_path):
    config_data = {
        "client_name": "ADM Solar",
        "subreddits": ["solar", "solarenergy"],
        "keywords": ["solar panels"],
        "brand_context": "ADM Solar installs residential solar.",
        "notify_email": "rachelle@keystone.com",
        "max_threads": 15,
        "sort": "hot"
    }
    config_file = tmp_path / "adm-solar.json"
    config_file.write_text(json.dumps(config_data))

    config = load_config(str(config_file))

    assert config.client_name == "ADM Solar"
    assert config.subreddits == ["solar", "solarenergy"]
    assert config.max_threads == 15
    assert config.sort == "hot"

def test_missing_required_field_raises(tmp_path):
    config_data = {"client_name": "ADM Solar"}  # missing required fields
    config_file = tmp_path / "bad.json"
    config_file.write_text(json.dumps(config_data))

    with pytest.raises(ConfigError, match="Missing required field"):
        load_config(str(config_file))

def test_file_not_found_raises():
    with pytest.raises(ConfigError, match="not found"):
        load_config("clients/nonexistent.json")

def test_invalid_sort_raises(tmp_path):
    config_data = {
        "client_name": "ADM Solar",
        "subreddits": ["solar"],
        "keywords": ["solar"],
        "brand_context": "context",
        "notify_email": "test@test.com",
        "max_threads": 10,
        "sort": "invalid"
    }
    config_file = tmp_path / "bad.json"
    config_file.write_text(json.dumps(config_data))

    with pytest.raises(ConfigError, match="sort must be one of"):
        load_config(str(config_file))
