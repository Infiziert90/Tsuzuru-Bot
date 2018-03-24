import yaml


def get_help_text(category, name):
    with open("config/text_storage.yaml", "r") as stream:
        help_text = yaml.load(stream)

    return help_text[category][name]
