# ntn — Notion CLI Tool: Design Document
**Date:** 2026-02-19
**Status:** Approved

---

## What We're Building

A lightweight Python CLI called `ntn` that gives anyone (and AI assistants like Claude) fast, direct access to their Notion workspace from the terminal — without MCP overhead.

The core idea: MCP tools for Notion cost ~23k tokens just to be loaded into context, add latency on every call, and require a running server. A simple Bash call to `ntn` costs nothing to have available and returns results instantly.

---

## Target Users

1. **Founders and operators** who use Notion as their second brain and want Claude to access it without friction
2. **Developers** building AI workflows who need programmatic Notion access from scripts
3. **Anyone** frustrated by Notion's lack of a proper CLI

---

## Architecture

**Language:** Python 3.9+
**SDK:** `notion-client` (official Notion Python SDK)
**CLI framework:** `argparse` (zero extra dependencies)
**Config:** `~/.ntn/config.json` — stored in user's home, not project dir
**Auth:** `NOTION_API_KEY` environment variable OR stored in config

No hardcoded workspace IDs. Everything configured via `ntn setup`.

---

## Commands (MVP)

```bash
# Setup
ntn setup                              # interactive wizard: API key + page/db mapping

# Brain dumps
ntn dump "thought or idea here"        # appends to today's dated page (creates if needed)
ntn today                              # prints today's brain dump to terminal

# Content collection (LinkedIn posts, articles, anything)
ntn post add <url> [--note "..."]      # saves a URL + note to configured posts database
ntn post list [--limit N]              # lists recent saved posts

# General
ntn search <query>                     # full-text search across workspace
ntn read <title-or-page-id>            # reads a page, outputs clean text
ntn db query <db-name> [--filter "..."] # queries any configured database
```

---

## GitHub Project Structure

```
notion-cli/
├── ntn.py              # single entry point, all commands
├── requirements.txt    # notion-client only
├── setup.py            # makes it pip-installable: pip install -e .
├── .env.example        # NOTION_API_KEY=your_key_here
├── .gitignore          # .env, __pycache__, venv, ~/.ntn/
├── README.md           # clear docs + Claude angle
└── docs/
    └── plans/
        └── 2026-02-19-notion-cli-design.md
```

---

## The Claude Angle (key differentiator for README)

```bash
# Claude can call this directly via Bash — no MCP, no token overhead
python ntn.py search "marketing agency pain points"
python ntn.py today
python ntn.py post list --limit 20
```

The README will show this explicitly: "Designed so AI assistants can access your Notion
via a single Bash call — faster and cheaper than running an MCP server."

---

## Config Design (~/.ntn/config.json)

```json
{
  "api_key": "ntn_...",
  "brain_dump_page_id": "xxx",
  "posts_database_id": "xxx",
  "databases": {
    "posts": "xxx",
    "leads": "xxx"
  }
}
```

`ntn setup` walks the user through finding and setting these values interactively.

---

## What Makes It Generic (not just for one person)

- No hardcoded IDs anywhere in the code
- `ntn setup` works for any Notion workspace
- Database names are user-defined aliases, not fixed
- API key via env var (CI/CD friendly) OR config file (local friendly)
- Works without `ntn setup` if env vars are set (scriptable from day one)

---

## Out of Scope (v1)

- GUI or web interface
- Syncing or two-way sync
- Notion to Markdown export (separate tool territory)
- Multi-workspace support (v2)
