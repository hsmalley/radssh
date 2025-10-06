"""Minimal plugin registry for radssh used by tests and core components.

This module provides a simple, in-memory registry for plugins and their
commands. It is designed to be lightweight and free of side-effects on import.

API:
- register(name, obj): Register a plugin object.
- get(name): Retrieve a plugin by name.
- get_plugins(): Get a dictionary of all registered plugins.
- clear(): Remove all registered plugins, primarily for test isolation.
- discover_plugin(src): Load a plugin from a source file and return its components.
- load_plugin(src): Load a plugin module from a source file.
- StarCommand: A wrapper for command handlers.
"""

import os
import importlib.util
import warnings

# Simple in-memory registry
_registry: dict[str, object] = {}


def register(name: str, obj: object) -> None:
    """Register a plugin by name."""
    _registry[name] = obj


def get(name: str):
    """Return a registered plugin or None."""
    return _registry.get(name)


def get_plugins() -> dict[str, object]:
    """Return a shallow copy of the registry dict."""
    return dict(_registry)


def clear() -> None:
    """Clear the registry - helpful in tests."""
    _registry.clear()


class StarCommand:
    """
    Compatibility wrapper for command handlers.
    
    Acts as a descriptor around a callable and stores optional metadata
    attributes expected by the rest of the codebase.
    """
    def __init__(self, handler, synopsis=None, help_text=None, **kwargs):
        self.handler = handler
        self.synopsis = synopsis or getattr(handler, "__doc__", "No synopsis available.")
        self.help_text = help_text or getattr(handler, "__doc__", "No help text available.")
        self.version = kwargs.get("version")
        self.min_args = kwargs.get("min_args", 0)
        self.max_args = kwargs.get("max_args")
        self.tab_completion = kwargs.get("tab_completion")
        self.auto_help = kwargs.get("auto_help", True)

    def __call__(self, *args, **kwargs):
        # This wrapper can also enforce arg counts before calling the handler
        num_args = len(args) - 3 # cluster, logdir, cmd are the first 3
        if num_args < self.min_args:
            print(f"Error: `{args[2].split()[0]}` requires at least {self.min_args} arguments.")
            return
        if self.max_args is not None and num_args > self.max_args:
            print(f"Error: `{args[2].split()[0]}` takes at most {self.max_args} arguments.")
            return
        return self.handler(*args, **kwargs)


def _unique_module_name(path: str) -> str:
    """Create a deterministic but safe module name from a file path."""
    basename = os.path.basename(path).replace(".py", "").replace("-", "_")
    # Sanitize basename to be a valid Python identifier
    safe_basename = "".join(c if c.isalnum() or c == "_" else "_" for c in basename)
    path_hash = abs(hash(os.path.abspath(path)))
    return f"radssh_plugin_{safe_basename}_{path_hash}"


def load_plugin(src: str):
    """
    Load a plugin module from a path or return a registered object.
    
    If `src` matches an in-memory registered plugin, it is returned. Otherwise,
    this function attempts to import the .py file at the given path.
    """
    plugin = get(src)
    if plugin is not None:
        return plugin

    path = os.path.abspath(os.path.expanduser(src))
    if not os.path.exists(path):
        raise ImportError(f"Plugin not found: {src}")
    if not path.endswith(".py"):
        raise RuntimeError(f"RadSSH Plugins must be .py files, but got: {src}")

    mod_name = _unique_module_name(path)
    spec = importlib.util.spec_from_file_location(mod_name, path)
    if not spec or not spec.loader:
        raise ImportError(f"Could not create module spec for plugin: {src}")

    module = importlib.util.module_from_spec(spec)
    try:
        spec.loader.exec_module(module)
    except Exception as e:
        warnings.warn(f"Failed to execute plugin module {src}: {e}")
        raise

    # Wrap plain functions in star_commands with the StarCommand class
    if hasattr(module, "star_commands"):
        sc = getattr(module, "star_commands")
        if isinstance(sc, dict):
            for name, cmd in list(sc.items()):
                if not isinstance(cmd, StarCommand):
                    sc[name] = StarCommand(cmd)
    return module


def discover_plugin(src: str):
    """
    Discover plugin entrypoints by loading the source file.
    
    Returns a tuple of (init_func, lookup_func, star_commands_dict).
    On failure, returns (None, None, {}).
    """
    try:
        plugin = load_plugin(src)
        init = getattr(plugin, "init", None)
        lookup = getattr(plugin, "lookup", None)
        star_commands = getattr(plugin, "star_commands", {})
        return init, lookup, star_commands
    except Exception:
        # Discovery should be non-fatal
        return None, None, {}