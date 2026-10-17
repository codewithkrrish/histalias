"""Turn a command into a short, memorable alias name.

The scheme: first letters of the significant words, so
``git push origin main`` becomes ``gpom``. It's not clever, but it's
predictable — after a week you can guess an alias before looking it up.
On collisions we try progressively shorter initial sets, then fall back
to a 3-letter prefix of the first word plus initials.
"""

from __future__ import annotations

import re

_TOKEN = re.compile(r"[A-Za-z0-9]+")

# filler words that add noise to an alias name
_STOPWORDS = frozenset(
    {"the", "a", "an", "to", "of", "in", "on", "and", "or", "for", "with"}
)

# names we must never generate: common builtins and things people
# usually already alias. Generating `ls` would shadow the real one.
RESERVED = frozenset(
    {
        "ls", "cd", "cp", "mv", "rm", "cat", "echo", "mkdir", "rmdir",
        "git", "py", "python", "python3", "pip", "ssh", "scp", "vim",
        "nano", "code", "node", "npm", "docker", "kubectl", "alias",
    }
)


def suggest_name(command: str, taken: set[str]) -> str | None:
    """Pick an unused alias name for *command*, or None if we can't.

    *taken* holds names already suggested this run plus RESERVED.
    Returns None instead of emitting something unreadable — a bad alias
    is worse than no alias.
    """
    words = _significant_words(command)
    if not words:
        return None

    for candidate in _candidates(words):
        if candidate not in taken and candidate not in RESERVED:
            return candidate
    return None


def _significant_words(command: str) -> list[str]:
    words = [w.lower() for w in _TOKEN.findall(command)]
    # single letters are almost always flags (-f, -rf): they make
    # terrible alias letters, so drop them
    # (kept TODO: multi-letter flags like --force could seed longer names)
    return [w for w in words if len(w) > 1 and w not in _STOPWORDS]


def _candidates(words: list[str]) -> list[str]:
    initials = [w[0] for w in words]
    out: list[str] = []
    for k in (4, 3, 2):
        if len(initials) >= k:
            out.append("".join(initials[:k]))
    # fallback: 3-letter head + initials, e.g. "gipom" for
    # "git push origin main" if gpom/gpo/gp were all taken
    if len(words[0]) >= 3:
        out.append(words[0][:3] + "".join(initials[1:3]))
    # last resort: the whole first word if it's short and sane
    if 2 <= len(words[0]) <= 6:
        out.append(words[0])
    return out
