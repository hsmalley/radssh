from radssh.hostkey import CodeMap, printable_fingerprint, HostKeyVerifier, verify_mode


def test_codemap_forward_and_reverse():
    cm = CodeMap(alpha=1, beta=2)
    assert cm.code("alpha") == 1
    assert cm.name(2) == "beta"


class FakeKey:
    def get_fingerprint(self):
        return bytes([1, 2, 3])

    def get_name(self):
        return "ssh-rsa"


def test_printable_fingerprint_bytes():
    k = FakeKey()
    pf = printable_fingerprint(k)
    assert pf == "01:02:03"


def test_hostkey_verifier_ignore_mode(tmp_path):
    # In ignore mode, verifier should accept any key without touching filesystem
    v = HostKeyVerifier(mode="ignore", known_hosts_file=str(tmp_path / "nope"))
    assert v.mode == verify_mode.code("ignore")
    assert v.verify_host_key("somehost", FakeKey()) is True
