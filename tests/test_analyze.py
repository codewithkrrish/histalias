import pytest

from histalias.analyze import find_candidates


def test_finds_long_frequent_commands():
    cmds = ["git push origin main"] * 5 + ["ls"] * 100
    found = find_candidates(cmds)
    assert [s.command for s in found] == ["git push origin main"]


def test_short_commands_never_suggested():
    cmds = ["ls -la"] * 50
    assert find_candidates(cmds, min_length=12) == []


def test_rare_commands_never_suggested():
    cmds = ["docker compose up --build --force-recreate"]
    assert find_candidates(cmds, min_count=3) == []


def test_best_first_ordering():
    cmds = (
        ["aaaa bbbb cccc dddd"] * 4  # score 4*19 = 76
        + ["eeeeeeeeeeeeeeeeeeee ffff"] * 3  # score 3*24 = 72
    )
    found = find_candidates(cmds)
    assert found[0].command == "aaaa bbbb cccc dddd"


def test_whitespace_variants_count_together():
    cmds = ["git  status  --short"] * 3 + ["git status --short"] * 3
    found = find_candidates(cmds, min_length=10, min_count=5)
    assert len(found) == 1
    assert found[0].count == 6


def test_empty_history_gives_no_candidates():
    assert find_candidates([]) == []


def test_bad_thresholds_fail_loudly():
    with pytest.raises(ValueError, match="min-count"):
        find_candidates(["git status"], min_count=0)
    with pytest.raises(ValueError, match="min-length"):
        find_candidates(["git status"], min_length=0)
