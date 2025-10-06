import threading

# Ensure paramiko has __version_info__ for import-time checks in radssh.__main__
import paramiko

if not hasattr(paramiko, "__version_info__"):
    try:
        ver = tuple(int(x) for x in paramiko.__version__.split(".")[:2])
    except Exception:
        ver = (2, 0)
    setattr(paramiko, "__version_info__", ver)

from radssh import __main__ as mainmod


def test_open_file(tmp_path):
    p = tmp_path / "f.txt"
    p.write_text("hello")
    f = mainmod.open_file(str(p))
    assert f.read() == "hello"
    f.close()


def test_start_thread_runs_and_waits():
    ev = threading.Event()
    t = mainmod.start_thread(ev)
    # thread should be alive until event is set
    assert t.is_alive()
    ev.set()
    t.join(timeout=1)
    assert not t.is_alive()
