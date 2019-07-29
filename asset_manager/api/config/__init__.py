import logging


logger = logging.getLogger(__name__)


from .default_config import *

try:
    from asset_manager_user_config import *
except ImportError:
    logger.info("No user config found"
