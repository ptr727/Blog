"""Load a sibling script by its path, since a hyphenated file name cannot be imported by name.

A script run as `checks/<name>.py` has `checks/` on its path, and the suite runs from `checks/`, so
both import this module by name.
"""

import importlib.util
import pathlib
import types


def load(name: str, path: pathlib.Path) -> types.ModuleType:
    """The script at path, run once as a module called name."""
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path.name}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
