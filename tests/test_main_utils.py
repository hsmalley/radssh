import threading

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
