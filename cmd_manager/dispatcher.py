from typing import Callable, NamedTuple


class Command(NamedTuple):
    name: str
    func: Callable
    is_enabled: Callable = None

commands = {}


def register(name, func, is_enabled):
    commands[name] = Command(name, func, is_enabled)


async def handle(name, client, message, args):
    command = commands[name]
    if command.is_enabled and not command.is_enabled(message):
        # TODO command not enabled in this situation, do whatever here
        return
    else:
        await command.func(client, message, args)
