from radssh.ssh import Quota, Chunker, CommandResult


def test_quota_limits():
    q = Quota({"quota.time": "1", "quota.bytes": "10", "quota.lines": "2"})
    assert q.settings() == (1, 10, 2)
    assert q.time_exceeded(2) is True
    assert q.time_exceeded(0) is False
    assert q.bytes_exceeded(20) is True
    assert q.bytes_exceeded(5) is False
    assert q.lines_exceeded(3) is True
    assert q.lines_exceeded(1) is False


def test_chunker_grouping_and_iteration():
    c = Chunker(grouping=2, delay=0)
    c.add(1, 2, 3)
    # length should be total items
    assert len(c) == 3
    groups = list(iter(c))
    # grouping=2 should yield two groups: [1,2] and [3]
    assert groups[0] == [1, 2]
    assert groups[-1] == [3]


def test_commandresult_repr_and_attrs():
    cr = CommandResult(command='echo hi', status='ok', return_code=0)
    # __repr__ expects status and command present
    r = repr(cr)
    assert 'ok' in r
    assert 'echo hi' in r
