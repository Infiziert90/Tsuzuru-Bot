import os
import dicts
import logging
import configparser
from . import load_help

config = dicts.AttrDict()
def load_config():
    ini_conf = configparser.ConfigParser()
    ini_conf.read(["bot.ini"])

    for key, val in ini_conf.items():
        if isinstance(val, (dict, configparser.SectionProxy)):
            val = dicts.AttrDict(val)
        config[key] = val

    debug = int(config.MAIN.get("debug", 0))
    if debug:
        os.environ["PYTHONASYNCIODEBUG"] = "1"

    if debug >= 3:
        log_level = logging.DEBUG
    elif debug >= 2:
        log_level = logging.INFO
    else:
        log_level = logging.WARNING

    logging.basicConfig(level=log_level)
    logging.getLogger('').addHandler(logging.FileHandler("output.log"))


load_config()
help_text = load_help.get_help_text

__all__ = ['config', 'help_text']
