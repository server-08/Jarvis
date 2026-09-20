# JARVIS AI

A safe, terminal-based Python personal assistant designed to run on Termux and ordinary Python installations.

## Features

- Friendly terminal UI
- Command normalization and routing
- Safe arithmetic calculator (no `eval` or arbitrary code execution)
- SQLite long-term memory
- Date and time commands
- Graceful handling of empty input, Ctrl-C, and EOF
- Placeholders for Gemini, search, and weather integrations
- Zero third-party dependencies

## Run

Requires Python 3.10 or newer:

```bash
python3 jarvis.py
```

On Termux:

```bash
pkg update
pkg install python
python jarvis.py
```

The SQLite database is stored at `~/.jarvis/jarvis.db`. Set `JARVIS_DB` to use another path.

## Commands

```text
help
hello
calculate 25 * 48
remember My preferred language is Python
memory
time
date
search latest AI news
weather Lucknow
ask explain neural networks
clear
exit
```

## Roadmap

1. Add a provider interface for Gemini with environment-based credentials.
2. Add search and weather adapters with timeout and error handling.
3. Split the application into `ui`, `router`, `tools`, and `storage` modules as integrations grow.
4. Add tests and optional voice input/output without making them required for the core assistant.

Never execute shell commands from model output without explicit user confirmation and an allowlist.
