"""End-to-end CLI tests using a fake HOME so nothing real is touched."""

import os
from pathlib import Path

import pytest

from histalias.cli import main


@pytest.fixture()
def fake_home(tmp_path, monkeypatch):
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("SHELL", "/bin/bash")
    # Path.home() caches nothing, but os.path.expanduser does on some
    # platforms — point both at the fake home
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: home))
    return home


def _write_history(home: Path, lines: list[str]) -> Path:
    hist = home / ".bash_history"
    hist.write_text("\n".join(lines) + "\n")
    return hist


def test_dry_run_prints_suggestions_and_writes_nothing(fake_home, capsys):
    _write_history(fake_home, ["git push origin main"] * 6 + ["ls"] * 50)
    rc = 0
    code = main(["--min-count", "3"])
    out = capsys.readouterr().out
    assert code == 0
    assert "alias gpom='git push origin main'" in out
    assert "Dry run" in out
    assert not (fake_home / ".bashrc").exists()


def test_apply_writes_aliases_to_rc(fake_home, capsys):
    _write_history(fake_home, ["docker compose up -d"] * 4)
    code = main(["--apply", "--min-count", "3"])
    out = capsys.readouterr().out
    assert code == 0
    rc = (fake_home / ".bashrc").read_text()
    assert "alias dcu='docker compose up -d'" in rc
    assert "source" in out  # tells the user how to activate


def test_empty_history_is_not_an_error(fake_home, capsys):
    _write_history(fake_home, ["ls", "cd /tmp"])
    code = main([])
    assert code == 1
    assert "nothing long + frequent enough" in capsys.readouterr().out


def test_missing_history_file_reports_cleanly(fake_home, capsys):
    code = main(["--history-file", "/does/not/exist"])
    err = capsys.readouterr().err
    assert code == 3
    assert "not found" in err
    assert "Traceback" not in err


def test_bad_flag_value_exits_2(fake_home, capsys):
    _write_history(fake_home, ["git status"] * 3)
    assert main(["--limit", "0"]) == 2
    assert main(["--min-count", "0"]) == 2


def test_explicit_history_file_is_used(fake_home, capsys, tmp_path):
    custom = tmp_path / "myhist"
    custom.write_text("kubectl get pods --all-namespaces\n" * 5)
    code = main(["--history-file", str(custom), "--min-count", "3"])
    out = capsys.readouterr().out
    assert code == 0
    assert "kubectl get pods --all-namespaces" in out
