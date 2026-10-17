import pytest

from histalias.history import HistoryError, _parse_line, read_commands


def test_bash_lines_pass_through(tmp_path):
    f = tmp_path / "hist"
    f.write_text("git status\ndocker compose up -d\n")
    assert read_commands(f) == ["git status", "docker compose up -d"]


def test_zsh_extended_format_parsed(tmp_path):
    f = tmp_path / "hist"
    f.write_text(": 1729000000:0;git push origin main\n: 1729000001:12;ls\n")
    assert read_commands(f) == ["git push origin main", "ls"]


def test_blank_and_comment_lines_skipped(tmp_path):
    f = tmp_path / "hist"
    f.write_text("\n# a comment\ngit status\n\n")
    assert read_commands(f) == ["git status"]


def test_alias_definitions_are_not_commands(tmp_path):
    f = tmp_path / "hist"
    f.write_text("alias gp='git push'\ngit status\n")
    assert read_commands(f) == ["git status"]


def test_corrupt_lines_dont_kill_the_run(tmp_path):
    f = tmp_path / "hist"
    # zsh line with empty command after the semicolon, plus binary garbage
    f.write_text(": 1729000000:0;\ngit status\n\x00\xff broken\n")
    cmds = read_commands(f)
    assert "git status" in cmds


def test_missing_file_raises_human_error(tmp_path):
    with pytest.raises(HistoryError, match="not found"):
        read_commands(tmp_path / "nope")


def test_parse_line_unit():
    assert _parse_line("  git log --oneline  ") == "git log --oneline"
    assert _parse_line("") is None
    assert _parse_line(": 1:2;echo hi") == "echo hi"
