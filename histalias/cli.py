"""histalias CLI: thin argparse layer over the real logic.

Exit codes: 0 = ok, 1 = nothing worth aliasing (not an error, just
boring history), 2 = bad flags (argparse default), 3 = couldn't read
the history file or write the rc file.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .analyze import DEFAULT_MIN_COUNT, DEFAULT_MIN_LENGTH, Suggestion, find_candidates
from .history import HistoryError, default_history_file, read_commands
from .rcfile import RcFileError, apply, default_rc_file, render_block
from .suggest import RESERVED, suggest_name


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="histalias",
        description=(
            "Find the long commands you keep retyping and suggest short "
            "aliases for them. Dry run by default — nothing is written "
            "unless you pass --apply."
        ),
    )
    p.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    p.add_argument(
        "--history-file",
        type=Path,
        default=None,
        help="history file to read (default: auto-detected from $SHELL)",
    )
    p.add_argument(
        "--min-count",
        type=int,
        default=DEFAULT_MIN_COUNT,
        help=f"minimum times a command must appear (default: {DEFAULT_MIN_COUNT})",
    )
    p.add_argument(
        "--min-length",
        type=int,
        default=DEFAULT_MIN_LENGTH,
        help=f"minimum command length to consider (default: {DEFAULT_MIN_LENGTH})",
    )
    p.add_argument(
        "--limit",
        type=int,
        default=20,
        help="max aliases to suggest (default: 20)",
    )
    p.add_argument(
        "--apply",
        action="store_true",
        help="append the aliases to your rc file (default: dry run, print only)",
    )
    p.add_argument(
        "--rc-file",
        type=Path,
        default=None,
        help="rc file to write with --apply (default: auto-detected from $SHELL)",
    )
    p.add_argument(
        "--force",
        action="store_true",
        help="with --apply, replace an existing histalias block instead of refusing",
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.limit < 1:
        print("histalias: --limit must be at least 1", file=sys.stderr)
        return 2

    history_file = args.history_file or default_history_file()
    try:
        commands = read_commands(history_file)
    except HistoryError as exc:
        print(f"histalias: {exc}", file=sys.stderr)
        return 3

    if not commands:
        print(f"histalias: no commands found in {history_file}")
        return 1

    try:
        candidates = find_candidates(commands, args.min_length, args.min_count)
    except ValueError as exc:
        print(f"histalias: {exc}", file=sys.stderr)
        return 2

    # name the best candidates; skip any we can't name cleanly
    taken = set(RESERVED)
    named: list[tuple[str, Suggestion]] = []
    for s in candidates:
        name = suggest_name(s.command, taken)
        if name is None:
            continue
        taken.add(name)
        s.saved_per_use = max(len(s.command) - len(name), 0)
        named.append((name, s))
        if len(named) >= args.limit:
            break

    if not named:
        print(
            f"histalias: analyzed {len(commands)} commands, "
            "nothing long + frequent enough to alias. "
            "Try --min-count 2 --min-length 8."
        )
        return 1

    names = {s.command: name for name, s in named}
    suggestions = [s for _, s in named]

    rc_file = args.rc_file or default_rc_file()
    print(f"Analyzed {len(commands)} commands from {history_file}\n")
    for name, s in named:
        print(
            f"  alias {name}='{s.command}'"
            f"   # {s.count}x · saves ~{s.count * s.saved_per_use} keystrokes"
        )

    if not args.apply:
        print(f"\nDry run — nothing written. Use --apply to add these to {rc_file}")
        return 0

    try:
        backup = apply(rc_file, render_block(suggestions, names), force=args.force)
    except RcFileError as exc:
        print(f"histalias: {exc}", file=sys.stderr)
        return 3
    except OSError as exc:
        print(f"histalias: couldn't write {rc_file}: {exc.strerror or exc}", file=sys.stderr)
        return 3

    print(f"\nAdded {len(named)} aliases to {rc_file} (backup: {backup})")
    print("Restart your shell or run: source " + str(rc_file))
    return 0


if __name__ == "__main__":
    sys.exit(main())
