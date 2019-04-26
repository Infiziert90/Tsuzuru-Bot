from typing import Callable, NamedTuple


class Command(NamedTuple):
    name: str
    func: Callable
    is_enabled: Callable = None
    is_admin: Callable = None

commands = {}


def register(name, func, is_enabled, is_admin):
    commands[name] = Command(name, func, is_enabled, is_admin)


async def handle(name, client, message, args):
    command = commands[name]
    if command.is_admin and not command.is_admin(client, message):
        return
    elif command.is_enabled and not command.is_enabled(message):
        return
    else:
        await command.func(client, message, args)
