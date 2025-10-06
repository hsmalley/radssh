"""Tests for the radssh.plugins module and filesystem discovery."""
from __future__ import annotations

import os
import tempfile

import radssh.plugins as plugins


def test_registry_register_and_clear():
    plugins.clear()
    plugins.register("x", object())
    assert "x" in plugins.get_plugins()
    plugins.clear()
    assert plugins.get_plugins() == {}


def test_load_plugin_from_registry():
    plugins.clear()
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
