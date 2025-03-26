"""Configuration management for One_Touch_Plus.

This module loads the default configuration and any temporary overrides, 
merges them, and validates the final configuration for use in the scraper.
"""

import os
import yaml
# from schema import Schema, And, Or  # Example if using schema for validation

def load_config():
    """Load and merge the scraper configuration from YAML files.

    This function loads the default asynchronous config and then overrides it 
    with any temporary config values (if provided), to produce a final configuration dictionary.

    Returns:
        dict: The merged configuration for the scraper.
    """
    config = {}
    base_config_path = os.path.join('configs', 'async_config.yaml')
    user_config_path = os.path.join('data', 'temp_config.yaml')  # user/job specific config
    try:
        with open(base_config_path, 'r') as f:
            config = yaml.safe_load(f) or {}
    except FileNotFoundError:
        # If base config is missing, proceed with empty config (or default values)
        config = {}
    # If a temporary config exists, merge it on top of base config
    if os.path.exists(user_config_path):
        with open(user_config_path, 'r') as f:
            user_config = yaml.safe_load(f) or {}
        # Merge user_config into base config (shallow merge for stub)
        for key, value in user_config.items():
            if isinstance(value, dict) and key in config:
                # Merge nested dicts
                config[key].update(value)
            else:
                config[key] = value
    # TODO: Consider deep merging for nested configurations if needed.
    return config

def validate_config(config):
    """Validate the given configuration for required keys and value types.

    This function uses a schema or manual checks to ensure the configuration is valid.
    It should raise an exception or return False if the config is invalid, otherwise True.

    Args:
        config (dict): The configuration dictionary to validate.

    Returns:
        bool: True if configuration is valid (or no issues found in stub), otherwise raises an error.
    """
    # TODO: Implement validation logic, possibly using schema library for structured validation.
    # Example:
    # schema = Schema({...}) 
    # schema.validate(config)
    # For now, just do basic sanity checks in this stub.
    if not isinstance(config, dict):
        raise ValueError("Configuration should be a dictionary.")
    # (Additional checks for expected top-level keys could be added here)
    return True
