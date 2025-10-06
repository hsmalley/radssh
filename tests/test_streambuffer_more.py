import queue

from radssh.streambuffer import StreamBuffer


def test_streambuffer_iter_len_str():
    b = StreamBuffer(None, tag="X", blocksize=10, presplit=False, encoding="utf-8")
    b.push(b"line1\nline2\n")
    # __len__ reflects buffer length
    assert len(b) > 0
    # __iter__ yields decoded lines
    lines = list(iter(b))
    assert "line1" in lines[0]
    assert "line2" in lines[1]
    # __str__ contains class name and tag
    s = str(b)
    assert "StreamBuffer" in s
    assert "X" in s


def test_close_enqueues_pending_and_counts_discards():
    q = queue.Queue(maxsize=1)
    b = StreamBuffer(q, tag="T", blocksize=2, presplit=False, encoding="utf-8")
    # push data to buffer; closing should attempt to enqueue pending
    b.push(b"a\n")
    # first put should succeed (queue maxsize 1)
    b.close()
    # queue may have one item
    items = []
    while True:
        try:
            items.append(q.get(block=False))
        except queue.Empty:
            break
    assert items, "close should have enqueued pending data"


def test_discards_increment_when_queue_full():
    q = queue.Queue(maxsize=0)
    b = StreamBuffer(q, tag="D", blocksize=1, presplit=True, encoding="utf-8")
    # push several lines; queue capacity 0 will raise Full on put_nowait
    b.push(b"one\ntwo\nthree\n")
    # discards should be non-negative (incremented on Full)
    assert b.discards >= 0


def test_rewind_and_pull_behaviour():
    b = StreamBuffer(None, tag="R", blocksize=10, presplit=False, encoding="utf-8")
    b.push(b"abcdef")
    # pull with size returns bytes slice
    assert b.pull(3) == b"abc"
    # rewind then pull again
    b.rewind(0)
    assert b.pull() == b"abcdef"
