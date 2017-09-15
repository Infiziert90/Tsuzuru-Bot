import argparse


class HelpException(Exception):
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
        raise HelpException(f'{self.format_usage()}\n{self.prog}: error: {message}')


parser = BotArgParse(prog=">>", formatter_class=lambda prog: argparse.HelpFormatter(prog, max_help_position=35, width=100))
subparsers = parser.add_subparsers(dest="command")
