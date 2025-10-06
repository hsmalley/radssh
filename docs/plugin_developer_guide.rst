Plugin developer guide
======================

This short guide explains how RadSSH discovers and loads plugin modules, and
outlines the minimal plugin API expected by the shell and the plugin manager.

Plugin discovery & loading
--------------------------

- The primary plugin loader is implemented in `radssh.core_plugins` and the
  `radssh.plugins` facade delegates to it when available. If `core_plugins`
  is not importable, `radssh.plugins` will fall back to a safe `importlib`-
  based loader that imports `.py` plugin files by absolute path.

- To inspect a plugin without making it fatal on failure, call
  ``radssh.plugins.discover_plugin(path)`` which returns a tuple:

  (init, lookup, star_commands)

  - ``init``: callable or ``None`` — plugin initialization function
  - ``lookup``: callable or ``None`` — function to resolve symbolic host names
  - ``star_commands``: mapping or ``{}`` — a dict mapping '*command' names to
    callables or ``StarCommand`` objects

- To load a plugin module, call ``radssh.plugins.load_plugin(src)`` where
  ``src`` is either a key previously registered via ``radssh.plugins.register``
  or an absolute filesystem path to a ``.py`` plugin. On success it returns the
  imported module object.

Plugin API minimal contract
---------------------------

Plugins may implement any of these:

- ``init(**kwargs)``: will be called by the shell when the plugin is loaded.
  Recommended signature: ``def init(**kwargs)`` to allow forwards compatibility.
  Common kwargs passed by the shell include: ``defaults``, ``auth``, ``plugins``,
  ``star_commands``, ``shell``.

- ``lookup(arg)``: a function that resolves a symbolic name into an iterator
  yielding ``(label, host, connection)`` tuples. Return ``None`` if the plugin
  does not match the given argument.

- ``star_commands``: a mapping of ``'*command'`` strings (like ``'*info'``) to
  either callable handlers or objects of type ``StarCommand``. Plain callables
  are wrapped into ``StarCommand`` automatically during loading.

Plugin API versioning
---------------------

Plugins should expose a module-level identifier to indicate the plugin API
version they were written for, for example::

    __radssh_plugin_api__ = "1.0"

When loading plugins, a future loader may check this value and warn or refuse
loading if the plugin API is incompatible with the running RadSSH version.

Security and notes
------------------

- Loading plugins executes their code; do not run untrusted plugins.
- Discovery uses importlib to perform dynamic imports and will execute top
  level code in the plugin module. Keep plugin imports lightweight and
  idempotent.

A small example plugin is included in the repository under
``radssh/plugins/sample_plugin.py`` for reference and testing.
