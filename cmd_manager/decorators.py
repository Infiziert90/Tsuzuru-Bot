from . import dispatcher
from .bot_args import subparsers


def register_command(name=None, *, is_enabled=None, is_admin=None, **kwargs):
    def decorator(func):
        nonlocal name
        if not name:
            name = func.__name__

        if "description" not in kwargs:
            raise RuntimeError(f"Missing description for bot command: {name}")

        if is_admin is not None:
            kwargs["description"] = f"[Admin] {kwargs['description']}"

        # TODO check if formatter_class needs to be provided here
        parser = subparsers.add_parser(name, **kwargs)
        if hasattr(func, "_cmd_args"):
            for arg_args, arg_kwargs in func._cmd_args:
                parser.add_argument(*arg_args, **arg_kwargs)

        if hasattr(func, "_cmd_group"):
            group = parser.add_mutually_exclusive_group(required=True)
            for arg_args, arg_kwargs in func._cmd_group:
                group.add_argument(*arg_args, **arg_kwargs)

        dispatcher.register(name, func, is_enabled, is_admin)
        return func

    return decorator


def add_argument(*args, **kwargs):
    def decorator(func):
        if not hasattr(func, "_cmd_args"):
            func._cmd_args = []

        if kwargs.get("default", None) is not None:
            kwargs["help"] += "(default: %(default)s)"
        func._cmd_args.insert(0, (args, kwargs))
        return func

    return decorator


def add_group(*args, **kwargs):
    def decorator(func):
        if not hasattr(func, "_cmd_group"):
            func._cmd_group = []

        func._cmd_group.insert(0, (args, kwargs))
        return func

    return decorator
