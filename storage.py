"""Provide basic persistent storage.
"""

import json
import logging
from pathlib import Path
from typing import Any, Dict

from config import config


class StorageDict(dict):
    """dict subclass that stores its contents on the filesystem.

    Whenever you set or delete an item of an instance,
    the file specified in the constructor is updated.
    Thus, do not modify the potentially mutable objects
    retrieved from this class
    and always re-set them when modified.
    Or call .save().
    """
    __slots__ = ('path')
    _loading = False

    def __init__(self, path: Path) -> None:
        super().__init__()
        self.path = path
        self.load()

    def load(self) -> None:
        if not storage_path.is_file():
            logging.debug("Persistent storage not found, starting fresh")
            return

        with storage_path.open(encoding='utf-8') as fp:
            data = json.load(fp)
        if not isinstance(data, dict):
            logging.error("Storage file does not contain a mapping (%s)", type(data))
            return

        self._loading = True
        self.clear()
        self.update(data)
        self._loading = False

    def save(self) -> None:
        with storage_path.open('w',  encoding='utf-8') as fp:
            json.dump(self, fp, indent=2)

    def __setitem__(self, *args, **kwargs):
        super().__setitem__(*args, **kwargs)
        if not self._loading:
            self.save()

    def __delitem__(self, *args, **kwargs):
        super().__delitem__(*args, **kwargs)
        if not self._loading:
            self.save()


storage_path = Path(config.MAIN.storage_file)

storage: Dict[str, Any] = StorageDict(storage_path)
