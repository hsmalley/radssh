from radssh.ssh import filter_tty_attrs


def test_filter_tty_attrs_removes_ansi():
    s = b"hello\x1b[31mred\x1b[0mworld"
    cleaned = filter_tty_attrs(s)
    assert b"\x1b[31m" not in cleaned
    assert b"\x1b[0m" not in cleaned
    assert b"hello" in cleaned
    assert b"red" in cleaned
