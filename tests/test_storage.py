from storage import Storage, text_hash


def test_mark_seen_is_per_chat(tmp_path):
    s = Storage(str(tmp_path / "t.db"))
    assert s.mark_seen(1, 5)
    assert not s.mark_seen(1, 5)
    assert s.mark_seen(2, 5)


def test_text_hash_ignores_case_and_whitespace():
    assert text_hash("Python  Developer\nkerak") == text_hash("python developer kerak")
    assert text_hash("python developer") != text_hash("java developer")


def test_verdict_keeps_forwarded_flag(tmp_path):
    s = Storage(str(tmp_path / "t.db"))
    h = text_hash("python developer kerak")
    assert s.get_verdict(h) is None

    s.save_verdict(h, True)
    assert s.get_verdict(h) == (True, False)

    s.mark_forwarded(h)
    s.save_verdict(h, True)
    assert s.get_verdict(h) == (True, True)
