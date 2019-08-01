import appdirs
import json
import logging
import os


logger = logging.getLogger(__name__)


from .default_config import *

try:
    from asset_manager_config import *
except ImportError:
    logger.info("No user config found")


def _settings_path():
    config_folder = appdirs.user_config_dir("asset-manager")
    return os.path.join(config_folder, "config.json")


def user_settings() -> dict:
    settings_path = _settings_path()

    if not os.path.exists(settings_path):
        return {}
    else:
        with open(settings_path, "r") as f:
            return json.loads(f.read())


def set_user_settings(settings: dict) -> None:
    settings_path = _settings_path()

    settings_dir = os.path.dirname(settings_path)
    if not os.path.exists(settings_dir):
        os.makedirs(settings_dir)

    with open(settings_path, "w") as f:
        f.write(json.dumps(settings))

