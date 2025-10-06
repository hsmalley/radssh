import queue

from radssh.streambuffer import StreamBuffer


def test_streambuffer_presplit_and_pull():
    q = queue.Queue()
    b = StreamBuffer(q, tag="T1:", blocksize=10, presplit=True, encoding="utf-8")

    # push several lines; presplit should enqueue lines
    b.push(b"one\ntwo\nthree\n")
    # collect queued lines
    items = []
    while True:
        try:
            items.append(q.get(block=False))
        except queue.Empty:
            break

    assert any("one" in text for (_tag, text) in items)
    assert any("two" in text for (_tag, text) in items)
    assert any("three" in text for (_tag, text) in items)

    # Test pull returns remaining bytes as bytes
    b2 = StreamBuffer(None, tag="T2:", blocksize=10, presplit=False, encoding="utf-8")
    b2.push("abc")
    assert b2.pull() == b"abc"
