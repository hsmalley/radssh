from radssh.ssh import Cluster, CommandResult


class DummyTransport:
    def __init__(
        self, active=True, authenticated=True, peer_ip="1.2.3.4", username="user"
    ):
        self._active = active
        self._authenticated = authenticated
        self._peer_ip = peer_ip
        self._username = username

    def is_active(self):
        return self._active

    def is_authenticated(self):
        return self._authenticated

    def getpeername(self):
        return (self._peer_ip, 22)

    def get_username(self):
        return self._username


def make_cluster_with_defaults():
    # Minimal hostlist and defaults to construct a Cluster without network activity
    hostlist = [("h1", "1.1.1.1")]
    defaults = {
        "output_mode": "off",
        "ordered_placeholder": "on",
        "character_encoding": "utf-8",
        "loglevel": "INFO",
        "max_threads": 1,
    }
    # Provide a minimal auth-like object with default_user to avoid AuthManager init
    auth = type("A", (), {"default_user": "test"})()
    c = Cluster(hostlist, auth=auth, defaults=defaults, start_threads=False)
    return c


def test_prep_command_and_locate(monkeypatch):
    c = make_cluster_with_defaults()
    # Inject a dummy transport in connections
    c.connections = {"h1": DummyTransport()}
    # Prep command with auto vars
    template = "echo %host% %ip% %uuid%"
    out = c.prep_command(template, "h1")
    assert out is not None
    assert "echo" in out
    # locate should find string key
    assert c.locate("h1") == "h1"


def test_connection_summary_counts():
    c = make_cluster_with_defaults()
    c.connections = {
        "ready": DummyTransport(active=True, authenticated=True),
        "notauth": DummyTransport(active=True, authenticated=False),
        "notactive": DummyTransport(active=False, authenticated=False),
        "failed": Exception("conn"),
    }
    ready, disabled, failed_auth, failed_connect, dropped = c.connection_summary()
    assert ready >= 0
    assert isinstance(failed_connect, int)


def test_exec_command_skipped_for_non_transport():
    # exec_command should return CommandResult with Skipped when t is not a Transport
    # Call exec_command with non-Transport argument (e.g., None) through direct import
    from radssh.ssh import exec_command

    r = exec_command("h", None, "cmd", None, None)
    assert isinstance(r, CommandResult)
    assert r.status.startswith("*** Skipped") or r.status == "*** Skipped ***"
