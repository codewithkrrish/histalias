"""Find the commands worth aliasing and score them.

A command is worth an alias when it is BOTH long and frequent —
``git push origin main`` typed 40 times saves real keystrokes, while
``ls -la`` typed 200 times is already short enough. The score is
frequency × length so long+often beats either alone.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

# Commands shorter than this are never suggested, no matter how frequent.
DEFAULT_MIN_LENGTH = 12
# Commands run fewer times than this are never suggested.
DEFAULT_MIN_COUNT = 3


@dataclass
class Suggestion:
    command: str
    count: int
    saved_per_use: int = 0  # filled in once the alias name is known


def find_candidates(
    commands: list[str],
    min_length: int = DEFAULT_MIN_LENGTH,
    min_count: int = DEFAULT_MIN_COUNT,
) -> list[Suggestion]:
    """Return the repeated long commands, best first.

    ``min_length``/``min_count`` are validated here so bad CLI flags
    fail with a clear message instead of silently returning nothing.
    """
    if min_length < 1:
        raise ValueError("--min-length must be at least 1")
    if min_count < 1:
        raise ValueError("--min-count must be at least 1")

    counts = Counter(_normalize(cmd) for cmd in commands)
    suggestions = [
        Suggestion(command=cmd, count=n)
        for cmd, n in counts.items()
        if len(cmd) >= min_length and n >= min_count
    ]
    # long + frequent first; ties broken alphabetically for stable output
    suggestions.sort(key=lambda s: (-(s.count * len(s.command)), s.command))
    return suggestions


def _normalize(command: str) -> str:
    # collapse runs of whitespace so "git  status" and "git status"
    # count as the same command
    return " ".join(command.split())
