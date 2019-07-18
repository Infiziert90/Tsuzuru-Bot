import importlib
import pathlib
import logging
from utils import HelperException


def load_commands():
    path = pathlib.Path(__file__).parent

    for file_path in path.glob("*"):
        if file_path.name == "__init__.py":
            continue

        mod_name = file_path.stem
        if not file_path.is_file() or file_path.suffix != ".py":
            continue
        try:
            mod = importlib.import_module("." + mod_name, __package__)
        except HelperException as err:
            logging.info(err)
