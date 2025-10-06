"""Tests for the radssh.plugins module and filesystem discovery."""

from __future__ import annotations

import os

import radssh.plugins as plugins


def test_registry_register_and_clear():
    # plugins.clear()
    plugins.register("x", object())
    assert "x" in plugins.get_plugins()
    # plugins.clear()
    assert plugins.get_plugins() == {}


def test_load_plugin_from_registry():
    # plugins.clear()

    class Dummy:
        pass

    d = Dummy()
    plugins.register("dummy", d)
    found = plugins.load_plugin("dummy")
    assert found is d
    plugins.clear()


def test_discover_and_load_sample_plugin(tmp_path):
    # Ensure the packaged plugins directory exists and contains our sample
    # plugin file. The core discovery will use radssh.plugins.load_plugin which
    # delegates to core_plugins; we exercise discover_plugin by pointing at the
    # sample file we added to radssh/plugins/sample_plugin.py
    repo_root = os.path.dirname(os.path.dirname(__file__))
    sample_path = os.path.join(repo_root, "radssh", "plugins", "sample_plugin.py")
    assert os.path.exists(sample_path), "sample plugin not found"

    init, lookup, cmds = plugins.discover_plugin(sample_path)
    assert init is not None
    assert lookup is not None
    assert isinstance(cmds, dict)
    # verify that StarCommand wrapping happens in discover_plugin's loader: keys
    # should be present and callable
    assert "*sample" in cmds
    # Attempt to load via load_plugin by absolute path (should import module)
    mod = plugins.load_plugin(sample_path)
    assert hasattr(mod, "init")
    assert hasattr(mod, "lookup")
    assert hasattr(mod, "star_commands")


def test_load_nonexistent_plugin():
    """Test that loading a non-existent plugin raises ImportError."""
    import pytest

    with pytest.raises(ImportError, match="Plugin not found"):
        plugins.load_plugin("/path/to/nonexistent.py")


def test_load_non_python_file(tmp_path):
    """Test that loading a non-.py file raises RuntimeError."""
    import pytest

    not_python = tmp_path / "not_python.txt"
    not_python.write_text("This is not Python")
    with pytest.raises(RuntimeError, match="RadSSH Plugins must be .py files"):
        plugins.load_plugin(str(not_python))


def test_discover_malformed_plugin(tmp_path):
    """Test that discover_plugin returns empty tuple for malformed plugins."""
    bad_plugin = tmp_path / "bad.py"
    bad_plugin.write_text("import nonexistent_module\nraise RuntimeError('Bad plugin')")

    init, lookup, cmds = plugins.discover_plugin(str(bad_plugin))
    assert (init, lookup, cmds) == (None, None, {})


def test_discover_plugin_with_syntax_error(tmp_path):
    """Test that discover_plugin handles Python syntax errors gracefully."""
    bad_syntax = tmp_path / "syntax_error.py"
    bad_syntax.write_text("def broken_function(\n    # Missing closing parenthesis")

    init, lookup, cmds = plugins.discover_plugin(str(bad_syntax))
    assert (init, lookup, cmds) == (None, None, {})


def test_load_plugin_with_import_error(tmp_path):
    """Test that load_plugin propagates import errors from malformed plugins."""
    import pytest

    bad_plugin = tmp_path / "import_error.py"
    bad_plugin.write_text("import nonexistent_module")

    with pytest.raises((ImportError, ModuleNotFoundError)):
        plugins.load_plugin(str(bad_plugin))


def test_plugin_star_commands_wrapping(tmp_path):
    """Test that plain callables in star_commands get wrapped with StarCommand."""
    plugin_with_plain_cmd = tmp_path / "plain_cmd.py"
    plugin_with_plain_cmd.write_text("""
def my_handler(cluster, logdir, cmdline, *args):
    '''Test handler'''
    pass

star_commands = {'*test': my_handler}
""")

    mod = plugins.load_plugin(str(plugin_with_plain_cmd))
    assert hasattr(mod, "star_commands")
    assert "*test" in mod.star_commands
    # Should be wrapped in StarCommand
    wrapped_cmd = mod.star_commands["*test"]
    assert hasattr(wrapped_cmd, "handler")  # core_plugins.StarCommand uses 'handler'
    assert hasattr(wrapped_cmd, "help_text")
    assert callable(wrapped_cmd)
