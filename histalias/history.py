"""Read shell history files into plain command strings.

Supports bash's plain-line format and zsh's extended format
(``: <epoch>:<duration>;<command>``). Anything that doesn't parse is
skipped quietly — a single corrupt line shouldn't kill the whole run.
"""

from __future__ import annotations

import os
import re
from pathlib import Path

# zsh extended history: ": 1690000000:0;git status"
_ZSH_EXTENDED = re.compile(r"^:\s*\d+:\d+;(.*)$")

# Lines we never want to alias even if frequent: the alias definition
# itself, and lines that are pure whitespace.
_SKIP_PREFIXES = ("alias ", "unalias ")


class HistoryError(Exception):
    """Raised when a history file can't be read."""


def default_history_file() -> Path:
    """Best guess at the current shell's history file."""
    shell = os.environ.get("SHELL", "")
    if "zsh" in shell:
        return Path.home() / ".zsh_history"
    # bash default; fish/etc. aren't supported yet (see README)
    env_file = os.environ.get("HISTFILE")
    if env_file:
        return Path(env_file)
    return Path.home() / ".bash_history"


def read_commands(path: Path) -> list[str]:
    """Return the commands stored in *path*, newest last.

    Raises HistoryError with a human-readable message when the file
    can't be read.
    """
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except FileNotFoundError:
        raise HistoryError(f"history file not found: {path}")
    except OSError as exc:
        raise HistoryError(f"couldn't read {path}: {exc.strerror or exc}")

    commands: list[str] = []
    for line in text.splitlines():
        cmd = _parse_line(line)
        if cmd:
            commands.append(cmd)
    return commands


def _parse_line(line: str) -> str | None:
    line = line.strip()
    if not line or line.startswith("#"):
        return None
    if line.startswith(_SKIP_PREFIXES):
        return None
    match = _ZSH_EXTENDED.match(line)
    if match:
        line = match.group(1).strip()
        if not line:
            return None
    return line
