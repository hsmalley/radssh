"""Example RadSSH plugin used by tests.

Implements a minimal `init`, `lookup`, and `star_commands` mapping so
`discover_plugin` and `load_plugin` can validate expected plugin shapes.
This file lives in the packaged `radssh/plugins` directory so discovery
via filesystem will pick it up during tests.
"""


def init(**kwargs):
    """Plugin initialization stub - record that init was called by setting
    an attribute on the module for test verification.
    """
    global initialized
    initialized = True


def lookup(arg):
    """Example lookup which accepts a single token 'localhost' and yields
    a single host tuple suitable for the shell's expectations.
    """
    if arg == "localhost":
        yield ("localhost", "127.0.0.1", None)
    else:
        return None


# Simple star command example: plain function will be wrapped by StarCommand
# by the core loader during discovery.


def my_star_handler(cluster, logdir, cmdline, *args):
    """Example *command"""
    print("sample_plugin: my_star_handler called")


star_commands = {"*sample": my_star_handler}
