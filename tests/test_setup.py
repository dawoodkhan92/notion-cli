# tests/test_setup.py
import json
from unittest.mock import patch

def test_setup_saves_api_key(tmp_path):
    import ntn
    inputs = iter(["ntn_testkey123", "", ""])
    with patch("builtins.input", side_effect=inputs):
        with patch("ntn.CONFIG_DIR", tmp_path / ".ntn"):
            with patch("ntn.CONFIG_FILE", tmp_path / ".ntn" / "config.json"):
                ntn.cmd_setup(None)
    config = json.loads((tmp_path / ".ntn" / "config.json").read_text())
    assert config["api_key"] == "ntn_testkey123"
