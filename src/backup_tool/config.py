import yaml
import os

class ConfigError(Exception):
    """Custom exception for configuration errors."""
    pass

def expand_env_vars(data):
    """
    Recursively expands environment variables in string values within a dictionary or list.

    Args:
        data (dict or list): The data structure to traverse.

    Returns:
        dict or list: The data structure with environment variables expanded.
    """
    if isinstance(data, dict):
        return {k: expand_env_vars(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [expand_env_vars(item) for item in data]
    elif isinstance(data, str):
        return os.path.expandvars(data)
    else:
        return data

def load_config(config_path):
    """
    Loads, validates, and expands environment variables in the configuration from a YAML file.

    Args:
        config_path (str): The path to the configuration file.

    Returns:
        dict: The loaded configuration dictionary with environment variables expanded.

    Raises:
        ConfigError: If the configuration file is invalid or missing required fields.
    """
    if not os.path.exists(config_path):
        raise ConfigError(f"Configuration file not found at: {config_path}")

    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ConfigError(f"Error parsing configuration file: {e}")

    # Basic validation (can be expanded later)
    if not config:
        raise ConfigError("Configuration file is empty or invalid.")

    required_sections = ["backup_sources", "backup_target", "schedule"]
    for section in required_sections:
        if section not in config:
            raise ConfigError(f"Missing required section in configuration: '{section}'")

    # Further validation for specific sections can be added here
    # Example: Check if backup_sources is a list and contains paths

    # Expand environment variables
    config = expand_env_vars(config)

    return config

# Example usage (for testing/demonstration)
if __name__ == "__main__":
    # Set an example environment variable for testing
    os.environ['BACKUP_USER'] = 'testuser_from_env'

    example_config_content = """
backup_sources:
  - /path/to/server1/data
  - /path/to/server2/configs

backup_target:
  path: //network/share/backups
  type: smb
  credentials:
    username: $BACKUP_USER # This should be expanded
    password: YOUR_PASSWORD_HERE

schedule:
  daily: "02:00"
  # weekly: "Sunday 03:00"
"""
    example_config_path = "example_backup_config.yaml"
    with open(example_config_path, "w") as f:
        f.write(example_config_content)

    try:
        loaded_config = load_config(example_config_path)
        print("Configuration loaded successfully:")
        print(loaded_config)
        # Verify environment variable expansion
        print(f"Expanded username: {loaded_config['backup_target']['credentials']['username']}")
    except ConfigError as e:
        print(f"Configuration Error: {e}")
    finally:
        # Clean up the example file and environment variable
        if os.path.exists(example_config_path):
            os.remove(example_config_path)
        if 'BACKUP_USER' in os.environ:
            del os.environ['BACKUP_USER']
