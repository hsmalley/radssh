import io
import sys
import types

# Create a proper module object for radssh.plugins so relative import works
plugin_mod = types.ModuleType("radssh.plugins")
class StarCommand:
    def __init__(self, func, **kwargs):
        self.func = func
        self.help_text = getattr(func, "__doc__", "")
        self.version = None
        self.synopsis = getattr(func, "__doc__", "")
    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)

plugin_mod.StarCommand = StarCommand
sys.modules["radssh.plugins"] = plugin_mod

from radssh import star_commands  # noqa: E402 (intentional plugin injection before import)


class DummyCluster:
    def __init__(self):
        self.output_mode = "stream"
        self.quota = type("Q", (), {"time_limit": 0, "byte_limit": 0, "line_limit": 0})()
        self.defaults = {"character_encoding": "utf-8"}
        self.user_vars = {}
        self.console = type("C", (), {"q": [], "join": lambda self, *a, **k: None})()
        self.connections = {}


def test_star_output_mode_valid_and_invalid():
    c = DummyCluster()
    # valid
    star_commands.star_output_mode(c, None, "", "ordered")
    assert c.output_mode == "ordered"
    # invalid should raise
    try:
        star_commands.star_output_mode(c, None, "", "bad")
        raised = False
    except ValueError:
        raised = True
    assert raised


def test_star_quota_prints_default(capsys=None):
    c = DummyCluster()
    # capture stdout
    old = sys.stdout
    sys.stdout = io.StringIO()
    try:
        star_commands.star_quota(c, None, "")
        out = sys.stdout.getvalue()
    finally:
        sys.stdout = old
    assert "Current Quota Settings" in out


def test_call_unknown_command_prints_help(capsys=None):
    c = DummyCluster()
    # calling unknown star command should return None (help printed)
    res = star_commands.call(c, None, "*nonexistent")
    assert res is None
