import yaml


def get_help_text(category, name=None):
    with open("config/text_storage.yaml", "r") as stream:
        help_text = yaml.safe_load(stream)

    if name is not None:
        return help_text[category][name]
    else:
        return help_text[category]
