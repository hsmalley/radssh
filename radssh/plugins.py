"""Minimal plugin registry for radssh used by tests.

This module is intentionally lightweight and side-effect free so importing it
during test collection doesn't attempt to load external resources.

API:
- register(name, obj): register a plugin object under a name
- get(name): return plugin by name or None
- iter_plugins(): iterate (name, obj) pairs
- clear(): remove all registered plugins (useful for tests)
"""

# Simple in-memory registry
_registry: dict[str, object] = {}


def register(name: str, obj: object) -> None:
    """Register a plugin by name."""
    _registry[name] = obj


def get(name: str):
    """Return a registered plugin or None."""
    return _registry.get(name)


def iter_plugins():
    """Yield (name, plugin) pairs in registration order."""
    for k, v in _registry.items():
        yield k, v


def get_plugins():
    """Return a shallow copy of the registry dict."""
    return dict(_registry)


def clear() -> None:
    """Clear the registry - helpful in tests."""
    _registry.clear()


class StarCommand:
    """Compatibility wrapper used by `radssh.star_commands`.

    Acts as a small descriptor around a callable and stores optional
    metadata attributes expected by the rest of the codebase.
    """

    def __init__(self, func, **kwargs):
        self.func = func
        self.help_text = getattr(func, "__doc__", "")
        self.version = kwargs.get("version")
        self.synopsis = kwargs.get("synopsis", getattr(func, "__doc__", ""))
        # Allow plugins to declare argument limits; unused by registry
        self.min_args = kwargs.get("min_args")
        self.max_args = kwargs.get("max_args")

    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)


# If available, prefer the richer implementations from core_plugins which
# include filesystem-based discovery and loading. Fall back to safe no-op
# implementations if core_plugins cannot be imported (e.g., during trimmed
# test environments).
try:
    from .core_plugins import StarCommand as _CoreStarCommand
    from .core_plugins import discover_plugin as _core_discover_plugin
    from .core_plugins import load_plugin as _core_load_plugin

    # Prefer the core StarCommand so behavior is consistent with the rest
    # of the codebase. We still keep the in-memory registry functions above.
    StarCommand = _CoreStarCommand


    def discover_plugin(src):
        return _core_discover_plugin(src)


    def load_plugin(src):
        # If a plugin has been registered in the in-memory registry, return it
        # (useful for programmatic/plugin testing). Otherwise delegate to the
        # core loader which will import plugin source files from disk.
        plugin = _registry.get(src)
        if plugin is not None:
            return plugin
        return _core_load_plugin(src)

except Exception:
    # Graceful fallback to earlier minimal behaviors when core_plugins is not
    # importable for any reason.
    # `StarCommand` remains the lightweight wrapper defined above.

    import importlib.util
    import importlib.machinery
    import os
    import uuid


    def _unique_module_name(path: str) -> str:
        # Create a deterministic-ish but safe module name from the path
        # Include basename for better debugging while keeping uniqueness
        basename = os.path.basename(path).replace('.py', '').replace('-', '_')
        # Clean basename to be a valid Python identifier
        basename = ''.join(c if c.isalnum() or c == '_' else '_' for c in basename)
        path_hash = abs(hash(os.path.abspath(path)))
        return f"radssh_plugin_{basename}_{path_hash}"


    def load_plugin(src):
        """Load a plugin module from a path or return a registered object.

        If `src` matches an in-memory registered plugin, return it. Otherwise
        attempt to import the .py file located at `src` and return the module
        object. This implementation avoids the deprecated `imp` module and
        uses importlib utilities instead.
        """

        # honor in-memory registry first (useful for tests)
        plugin = _registry.get(src)
        if plugin is not None:
            return plugin

        path = os.path.abspath(os.path.expanduser(src))
        if not os.path.exists(path):
            raise ImportError(f"Plugin not found: {src}")
        if not path.endswith(".py"):
            raise RuntimeError("RadSSH Plugins must be .py files [%s]" % src)

        mod_name = _unique_module_name(path)
        spec = importlib.util.spec_from_file_location(mod_name, path)
        if spec is None or spec.loader is None:
            raise ImportError(f"Could not load plugin spec: {src}")
        module = importlib.util.module_from_spec(spec)
        loader = spec.loader
        assert hasattr(loader, "exec_module")
        try:
            loader.exec_module(module)  # type: ignore[attr-defined]
        except Exception:
            # Propagate exception to caller; discover_plugin will catch and
            # translate to warnings if needed.
            raise

        # If module defines plain callables in `star_commands`, wrap them
        # in our StarCommand compatibility wrapper so callers receive a
        # consistent object.
        if hasattr(module, "star_commands"):
            sc = getattr(module, "star_commands")
            try:
                for name, cmd in list(sc.items()):
                    if not isinstance(cmd, StarCommand):
                        sc[name] = StarCommand(cmd)
            except Exception:
                # If star_commands isn't a mapping, ignore silently and let
                # the calling code handle it.
                pass

        return module


    def discover_plugin(src):
        """Discover plugin entrypoints by attempting to load the source file.

        Returns (init, lookup, star_commands) on success; on failure returns
        (None, None, {}) as the core_plugins implementation does.
        """

        try:
            plugin = load_plugin(src)
        except Exception:
            # Keep discovery non-fatal; callers expect to handle failures
            return None, None, {}

        init = getattr(plugin, "init", None)
        lookup = getattr(plugin, "lookup", None)
        star_commands = getattr(plugin, "star_commands", {})
        return init, lookup, star_commands
