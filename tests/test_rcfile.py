import pytest

from histalias.analyze import Suggestion
from histalias.rcfile import BLOCK_END, BLOCK_START, RcFileError, apply, render_block


def _sugg(cmd="git push origin main", count=5):
    s = Suggestion(command=cmd, count=count)
    s.saved_per_use = len(cmd) - 4
    return s


def test_render_block_is_valid_shell():
    block = render_block([_sugg()], {"git push origin main": "gpom"})
    assert block.startswith(BLOCK_START)
    assert block.rstrip().endswith(BLOCK_END)
    assert "alias gpom='git push origin main'" in block


def test_commands_with_single_quotes_use_double_quotes():
    s = _sugg(cmd="echo 'hi there friend'")
    block = render_block([s], {s.command: "eht"})
    assert 'alias eht="echo \'hi there friend\'"' in block


def test_apply_appends_and_backs_up(tmp_path):
    rc = tmp_path / ".bashrc"
    rc.write_text("export EDITOR=vim\n")
    backup = apply(rc, BLOCK_START + "\n" + BLOCK_END + "\n")
    assert backup.exists()
    text = rc.read_text()
    assert "export EDITOR=vim" in text  # user's own lines untouched
    assert BLOCK_START in text


def test_apply_twice_refuses_without_force(tmp_path):
    rc = tmp_path / ".bashrc"
    rc.write_text("")
    apply(rc, BLOCK_START + "\n" + BLOCK_END + "\n")
    with pytest.raises(RcFileError, match="--force"):
        apply(rc, BLOCK_START + "\n" + BLOCK_END + "\n")


def test_apply_with_force_replaces_block(tmp_path):
    rc = tmp_path / ".bashrc"
    rc.write_text("line1\n")
    apply(rc, BLOCK_START + "\nalias a='x'\n" + BLOCK_END + "\n")
    apply(rc, BLOCK_START + "\nalias b='y'\n" + BLOCK_END + "\n", force=True)
    text = rc.read_text()
    assert text.count(BLOCK_START) == 1
    assert "alias b='y'" in text
    assert "alias a='x'" not in text
    assert "line1" in text


def test_apply_creates_missing_rc_file(tmp_path):
    rc = tmp_path / ".zshrc"  # doesn't exist yet
    apply(rc, BLOCK_START + "\n" + BLOCK_END + "\n")
    assert BLOCK_START in rc.read_text()


def test_apply_is_atomic_on_failure(tmp_path, monkeypatch):
    rc = tmp_path / ".bashrc"
    rc.write_text("precious=user stuff\n")
    import histalias.rcfile as rcfile

    def boom(*a, **k):
        raise OSError("disk exploded")

    monkeypatch.setattr(rcfile.os, "replace", boom)
    with pytest.raises(OSError):
        apply(rc, BLOCK_START + "\n" + BLOCK_END + "\n")
    # original untouched, no half-written file
    assert rc.read_text() == "precious=user stuff\n"
