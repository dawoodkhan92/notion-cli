# tests/test_config.py
import os
import json
import pytest
from unittest.mock import patch

def test_load_config_from_env(tmp_path):
    """API key from env var loads correctly"""
    with patch.dict(os.environ, {"NOTION_API_KEY": "test_key_123"}):
        with patch("ntn.CONFIG_FILE", tmp_path / "config.json"):
            from ntn import load_config
            config = load_config()
    assert config["api_key"] == "test_key_123"

def test_load_config_from_file(tmp_path):
    """API key loaded from config file when env var absent"""
    config_data = {"api_key": "file_key_456", "databases": {}}
    config_file = tmp_path / "config.json"
    config_file.write_text(json.dumps(config_data))

    import ntn
    with patch.dict(os.environ, {}, clear=True):
        with patch("ntn.CONFIG_FILE", config_file):
            config = ntn.load_config()
    assert config["api_key"] == "file_key_456"

def test_load_config_missing_key_raises(tmp_path):
    """Raises ValueError when no API key found anywhere"""
    import ntn
    with patch.dict(os.environ, {}, clear=True):
        with patch("ntn.CONFIG_FILE", tmp_path / "nonexistent.json"):
            with pytest.raises(ValueError, match="No Notion API key"):
                ntn.load_config()

def test_save_config_creates_directory(tmp_path):
    """save_config creates ~/.ntn/ dir and writes file"""
    import ntn
    config = {"api_key": "test", "databases": {}}
    config_dir = tmp_path / ".ntn"
    config_file = config_dir / "config.json"

    with patch("ntn.CONFIG_DIR", config_dir):
        with patch("ntn.CONFIG_FILE", config_file):
            ntn.save_config(config)

    assert config_dir.exists()
    assert json.loads(config_file.read_text()) == config
