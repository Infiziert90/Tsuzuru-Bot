import os
import yaml
import dicts
import logging
import configparser

config = dicts.AttrDict()
def load_config():
    ini_conf = configparser.ConfigParser()
    ini_conf.read(["bot.ini", "bot_example.ini"])

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

    with open("config/text_storage.yaml", "r") as stream:
        help_text = yaml.load(stream)

    return help_text
help_text = load_config()

__all__ = ['config', 'help_text']
