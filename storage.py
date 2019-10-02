"""Provide basic persistent storage.

When modifying the module-global 'storage' field,
call save() to make it persist cross restarts.
"""

import pickle
import logging
from pathlib import Path
from typing import Any, Dict

from config import config


storage_path = Path(config.MAIN.storage_file)
storage: Dict[str, Any] = {}


def load() -> None:
    global storage
    if not storage_path.is_file():
        logging.debug("Persistent storage not found, starting fresh")
        return

    with storage_path.open('rb') as fp:
        storage = pickle.load(fp)


def save() -> None:
    with storage_path.open('wb') as fp:
        pickle.dump(storage, fp, protocol=4)


load()
