import argparse
import discord


class HelpException(Exception):
    def __init__(self, message):
        self.message = message

    def __repr__(self):
        return self.message


class UnkownCommandException(Exception):
    def __init__(self, message):
        self.message = message

    def __repr__(self):
        return self.message


class BotArgParse(argparse.ArgumentParser):
    def print_help(self, file=None):
        raise HelpException(self.format_help())

    def exit(self, status=0, message=None):
        raise HelpException(message)

    def error(self, message=None):
        raise UnkownCommandException(f'Error: {message}')


def build_custom_help():
    help_string = "Usage: >>COMMAND [ARGS]\n"

    # https://stackoverflow.com/questions/20094215/argparse-subparser-monolithic-help-output
    subparsers_actions = [
        action for action in parser._actions
        if isinstance(action, argparse._SubParsersAction)]
    # there will probably only be one subparser_action,
    # but better save than sorry
    categories = {
        "normal": ["\nnormal commands:"],
        "admin": ["\nadmin commands (yields punishment for non-privileged user):"],
        "link": ["\npost links for:"],
        "image": ["\npost image:"],
    }
    admin_commands = []
    for subparsers_action in subparsers_actions:
        # get all subparsers and print help
        for dest, choice in subparsers_action.choices.items():
            if choice.description.startswith("[Admin]"):
                categories["admin"].append(f"    {dest:<19} {choice.description[8:]}")
            elif choice.description.startswith("[Image]"):
                categories["image"].append(f"    {dest}")
            elif choice.description.startswith("[Link]"):
                categories["link"].append(f"    {dest}")
            else:
                categories["normal"].append(f"    {dest:<19} {choice.description}")

    help_string += '\n'.join([command for commands in categories.values() for command in commands])
    return help_string


parser = BotArgParse(prog=">>", usage=">>", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
subparsers = parser.add_subparsers(dest="command")
