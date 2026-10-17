# histalias

Stop retyping the same long commands. histalias reads your shell history, finds the long commands you type over and over, and suggests short aliases for them. Dry run by default — it never touches your rc file unless you say `--apply`.

## Why I built this

I kept typing `git push origin main` and `docker compose up -d` dozens of times a day and kept telling myself "I should alias these" — then never doing it. So I made the computer do the boring part: scan history, rank by frequency x length, and hand me the alias lines ready to paste.

```
$ histalias
Analyzed 4218 commands from /home/krrish/.zsh_history

  alias gpom='git push origin main'        # 38x · saves ~570 keystrokes
  alias dcu='docker compose up -d'         # 21x · saves ~315 keystrokes
  alias kga='kubectl get pods --all-namespaces'  # 14x · saves ~392 keystrokes

Dry run — nothing written. Use --apply to add these to /home/krrish/.zshrc
```

```
$ histalias --apply
Added 3 aliases to /home/krrish/.zshrc (backup: /home/krrish/.zshrc.histalias.bak)
Restart your shell or run: source /home/krrish/.zshrc
```

## Install

Zero dependencies, Python 3.9+.

```bash
git clone https://github.com/codewithkrrish/histalias
cd histalias
pip install .
```

Or just run it directly without installing:

```bash
python3 -m histalias
```

## Usage

```bash
histalias                          # dry run: print suggestions
histalias --apply                   # append aliases to ~/.bashrc or ~/.zshrc
histalias --apply --force           # replace a previously applied block

# tune what counts as "worth aliasing"
histalias --min-count 5 --min-length 15 --limit 10

# point at a specific history file
histalias --history-file ~/.bash_history
histalias --apply --rc-file ~/.zshrc
```

### How it picks aliases

1. Parses bash history and zsh extended history (`: epoch:duration;cmd`).
2. Keeps commands that are both long enough (`--min-length`, default 12) and frequent enough (`--min-count`, default 3).
3. Ranks by frequency x length, so long-and-often beats either alone.
4. Names each alias from the first letters of the significant words (`git push origin main` -> `gpom`), skipping names that collide with shell builtins or common existing aliases. Commands it can't name cleanly are skipped, not forced.

### Safety

- **Dry run by default.** Nothing is written without `--apply`.
- Aliases go into a marked block (`# >>> histalias >>>` ... `# <<< histalias <<<`), so your own rc lines are never touched. Applying twice without `--force` is refused, not duplicated.
- Your rc file is backed up (`~/.zshrc.histalias.bak`) before the first apply, and rewritten atomically (temp file + rename) so a crash can't corrupt it.

## Limitations

- bash and zsh only. fish history format isn't supported yet.
- It can't see aliases you already have — if `gp` is already yours, histalias might suggest it again. It does avoid common builtins (`ls`, `cd`, `rm`, ...).
- Suggestions are only as good as your history: a fresh machine with 50 commands in history won't produce much. Lower `--min-count` if you want.
- Single quotes in a command are handled, but genuinely weird quoting (nested quotes, command substitution) may produce an alias that needs a manual tweak. Check the block before sourcing.

## Project structure

```
histalias/
  __init__.py    version
  cli.py         argparse layer + exit codes (no business logic here)
  history.py     bash/zsh history parsing
  analyze.py     frequency x length scoring
  suggest.py     alias name generation
  rcfile.py      marked-block rc file writes (atomic, with backup)
tests/           pytest, 33 tests
```

## License

MIT — see [LICENSE](LICENSE).

Built by [Krrish](https://github.com/codewithkrrish).
