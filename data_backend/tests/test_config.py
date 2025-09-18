import pytest

from data_backend.config import get_config


def test_get_config_valid(tmp_path):
    config_path = tmp_path / "config.yaml"
    config_content = """leagues: [139, 140]"""
    config_path.write_text(config_content)
    config = get_config(config_path)
    assert config == {"leagues": [139, 140]}


def test_get_config_file_not_found(tmp_path):
    config_path = tmp_path / "nonexistent.yaml"
    with pytest.raises(FileNotFoundError):
        get_config(config_path)


def test_get_config_yaml_error(tmp_path):
    config_path = tmp_path / "invalid.yaml"
    config_content = """invalid_yaml: [unclosed_list"""
    config_path.write_text(config_content)
    with pytest.raises(RuntimeError):
        get_config(config_path)
