import importlib
import pathlib


def load_commands():
    path = pathlib.Path(__file__).parent

    for file_path in path.glob("*"):
        if file_path.name == "__init__.py":
            continue

        mod_name = file_path.stem
        if not file_path.is_file() or file_path.suffix != ".py":
            continue

        mod = importlib.import_module("." + mod_name, __package__)
