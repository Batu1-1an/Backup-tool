import os
import pytest
import yaml
import sys

# Add the src directory to the path to import the backup_tool module
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))
from backup_tool import config

# Define a fixture for creating temporary config files
@pytest.fixture
def temp_config_file(tmp_path):
    """Creates a temporary valid YAML config file for testing."""
    config_content = {
        "backup_sources": ["/path/to/source1", "/path/to/source2"],
        "backup_target": {
            "path": "//server/share",
            "type": "smb",
            "credentials": {"username": "testuser", "password": "testpassword"}
        },
        "schedule": {
            "daily": "02:00",
            "weekly": "Sunday 03:00"
        },
        "logging": {
            "log_file": "/var/log/backup_tool/test.log",
            "level": "INFO"
        }
    }
    config_file = tmp_path / "valid_config.yaml"
    with open(config_file, 'w') as f:
        yaml.dump(config_content, f)
    return str(config_file) # Return path as string

@pytest.fixture
def temp_invalid_config_file(tmp_path):
    """Creates a temporary invalid YAML config file (missing required section)."""
    config_content = {
        "backup_sources": ["/path/to/source1"],
        # Missing backup_target and schedule
    }
    config_file = tmp_path / "invalid_config.yaml"
    with open(config_file, 'w') as f:
        yaml.dump(config_content, f)
    return str(config_file)

@pytest.fixture
def temp_empty_config_file(tmp_path):
    """Creates a temporary empty file."""
    config_file = tmp_path / "empty_config.yaml"
    config_file.touch()
    return str(config_file)

# --- Test Cases ---

def test_load_config_valid(temp_config_file):
    """Tests loading a valid configuration file."""
    loaded_config = config.load_config(temp_config_file)
    assert loaded_config is not None
    assert "backup_sources" in loaded_config
    assert "backup_target" in loaded_config
    assert "schedule" in loaded_config
    assert loaded_config["backup_target"]["type"] == "smb"
    assert loaded_config["schedule"]["daily"] == "02:00"

def test_load_config_missing_file():
    """Tests loading a non-existent configuration file."""
    with pytest.raises(config.ConfigError, match="Configuration file not found"):
        config.load_config("non_existent_config.yaml")

def test_load_config_invalid_yaml(tmp_path):
    """Tests loading a file with invalid YAML syntax."""
    invalid_yaml_file = tmp_path / "invalid_syntax.yaml"
    with open(invalid_yaml_file, "w") as f:
        f.write("backup_sources: [/path/source1\nbackup_target: { path: //share") # Invalid YAML
    with pytest.raises(config.ConfigError, match="Error parsing configuration file"):
        config.load_config(str(invalid_yaml_file))

def test_load_config_empty_file(temp_empty_config_file):
    """Tests loading an empty configuration file."""
    with pytest.raises(config.ConfigError, match="Configuration file is empty or invalid"):
        config.load_config(temp_empty_config_file)

def test_load_config_missing_section(temp_invalid_config_file):
    """Tests loading a config file missing a required section."""
    with pytest.raises(config.ConfigError, match="Missing required section"):
        config.load_config(temp_invalid_config_file)

def test_load_config_env_vars(tmp_path):
    """Tests loading a configuration file with environment variable expansion."""
    # Define a config with an environment variable
    config_content = {
        "backup_sources": ["/path/to/source1"],
        "backup_target": {
            "path": "$BACKUP_TARGET_PATH", # Use an environment variable
            "type": "smb"
        },
        "schedule": {"daily": "02:00"}
    }
    config_file = tmp_path / "env_var_config.yaml"
    with open(config_file, 'w') as f:
        yaml.dump(config_content, f)

    # Set the environment variable
    os.environ['BACKUP_TARGET_PATH'] = '//server/share/from_env'

    try:
        # Load the config
        loaded_config = config.load_config(str(config_file))

        # Assert that the environment variable was expanded
        assert loaded_config is not None
        assert "backup_target" in loaded_config
        assert "path" in loaded_config["backup_target"]
        assert loaded_config["backup_target"]["path"] == '//server/share/from_env'

    finally:
        # Clean up the environment variable
        if 'BACKUP_TARGET_PATH' in os.environ:
            del os.environ['BACKUP_TARGET_PATH']