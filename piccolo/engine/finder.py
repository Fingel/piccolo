from importlib import import_module
import os
from types import ModuleType
import typing as t
import warnings

from .base import Engine


DEFAULT_MODULE_NAME = "piccolo_conf"
ENVIRONMENT_VARIABLE = "PICCOLO_CONF"
ENGINE_VAR = "DB"


def engine_finder(module_name: t.Optional[str] = None) -> t.Optional[Engine]:
    """
    An example module name is `my_piccolo_conf`.

    The value used is determined by:
    module_name argument > environment variable > default.

    The module must be available on the path, so Python can import it.
    """
    env_module_name = os.environ.get(ENVIRONMENT_VARIABLE, None)

    if not module_name and env_module_name:
        module_name = env_module_name

    if not module_name:
        module_name = DEFAULT_MODULE_NAME

    module: t.Optional[ModuleType] = None
    engine: t.Optional[Engine] = None

    try:
        module = import_module(module_name)
    except ModuleNotFoundError:
        warnings.warn(f"{module_name} doesn't exist.")
    else:
        engine = getattr(module, ENGINE_VAR, None)

    if module:
        if not engine:
            warnings.warn(
                f"{module_name} doesn't define a {ENGINE_VAR} variable."
            )
        elif not isinstance(engine, Engine):
            warnings.warn(
                f"{module_name} contains a {ENGINE_VAR} variable of the wrong "
                "type - it should be an Engine subclass."
            )

    return engine
