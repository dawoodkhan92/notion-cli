# ntn — Notion CLI Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build `ntn`, a generic Python CLI that gives Claude and developers fast terminal access to any Notion workspace without MCP overhead.

**Architecture:** Single `ntn.py` entry point using `argparse` (stdlib) for subcommands and the official `notion-client` SDK. Config stored in `~/.ntn/config.json`. Fully generic — works with any workspace via `ntn setup`.

**Tech Stack:** Python 3.9+, `notion-client`, `python-dotenv`, `pytest` + `pytest-mock` (dev only)

---

### Task 1: Project Scaffold

**Files:**
- Create: `requirements.txt`
- Create: `requirements-dev.txt`
- Create: `.gitignore`
- Create: `.env.example`
- Create: `setup.py`
- Create: `tests/__init__.py`

**Step 1: Create requirements.txt**
```
notion-client>=2.2.1
python-dotenv>=1.0.0
```

**Step 2: Create requirements-dev.txt**
```
pytest>=7.0
pytest-mock>=3.10
```

**Step 3: Create .gitignore**
```
.env
__pycache__/
*.pyc
venv/
.venv/
dist/
*.egg-info/
.ntn/
```

**Step 4: Create .env.example**
```
NOTION_API_KEY=ntn_your_key_here
```

**Step 5: Create setup.py**
```python
from setuptools import setup

setup(
    name="ntn",
    version="0.1.0",
    py_modules=["ntn"],
    install_requires=[
        "notion-client>=2.2.1",
        "python-dotenv>=1.0.0",
    ],
    entry_points={
        "console_scripts": [
            "ntn=ntn:main",
        ],
    },
    python_requires=">=3.9",
)
```

**Step 6: Create tests/__init__.py** (empty file)

**Step 7: Install dev dependencies**
```bash
pip install -r requirements.txt -r requirements-dev.txt
```

**Step 8: Commit scaffold**
```bash
git add .
git commit -m "chore: project scaffold, requirements, .gitignore"
```

---

### Task 2: Config Management

**Files:**
- Create: `ntn.py` (skeleton — config functions only)
- Create: `tests/test_config.py`

**Step 1: Write failing tests**
```python
# tests/test_config.py
import os
import json
import pytest
from unittest.mock import patch

def test_load_config_from_env(tmp_path):
    """API key from env var loads correctly"""
    with patch.dict(os.environ, {"NOTION_API_KEY": "test_key_123"}):
        with patch("ntn.CONFIG_FILE", tmp_path / "config.json"):
            from ntn import load_config
            config = load_config()
    assert config["api_key"] == "test_key_123"

def test_load_config_from_file(tmp_path):
    """API key loaded from config file when env var absent"""
    config_data = {"api_key": "file_key_456", "databases": {}}
    config_file = tmp_path / "config.json"
    config_file.write_text(json.dumps(config_data))

    import importlib, ntn
    with patch.dict(os.environ, {}, clear=True):
        with patch("ntn.CONFIG_FILE", config_file):
            config = ntn.load_config()
    assert config["api_key"] == "file_key_456"

def test_load_config_missing_key_raises(tmp_path):
    """Raises ValueError when no API key found anywhere"""
    import ntn
    with patch.dict(os.environ, {}, clear=True):
        with patch("ntn.CONFIG_FILE", tmp_path / "nonexistent.json"):
            with pytest.raises(ValueError, match="No Notion API key"):
                ntn.load_config()

def test_save_config_creates_directory(tmp_path):
    """save_config creates ~/.ntn/ dir and writes file"""
    import ntn
    config = {"api_key": "test", "databases": {}}
    config_dir = tmp_path / ".ntn"
    config_file = config_dir / "config.json"

    with patch("ntn.CONFIG_DIR", config_dir):
        with patch("ntn.CONFIG_FILE", config_file):
            ntn.save_config(config)

    assert config_dir.exists()
    assert json.loads(config_file.read_text()) == config
```

**Step 2: Run to verify they fail**
```bash
pytest tests/test_config.py -v
```
Expected: `ModuleNotFoundError: No module named 'ntn'`

**Step 3: Create ntn.py**
```python
#!/usr/bin/env python3
"""ntn — Notion CLI: fast terminal access to any Notion workspace."""

import os
import json
import argparse
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from notion_client import Client
from notion_client.errors import APIResponseError

load_dotenv()

CONFIG_DIR = Path.home() / ".ntn"
CONFIG_FILE = CONFIG_DIR / "config.json"


# ── Config ───────────────────────────────────────────────────────────────────

def load_config() -> dict:
    config = {}
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE) as f:
            config = json.load(f)
    api_key = os.environ.get("NOTION_API_KEY") or config.get("api_key")
    if not api_key:
        raise ValueError(
            "No Notion API key found.\n"
            "Run 'ntn setup' or set NOTION_API_KEY environment variable."
        )
    config["api_key"] = api_key
    config.setdefault("databases", {})
    return config


def save_config(config: dict) -> None:
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w") as f:
        json.dump(config, f, indent=2)
    os.chmod(CONFIG_FILE, 0o600)


def get_client(config: dict) -> Client:
    return Client(auth=config["api_key"])


# ── Entry point (placeholder) ────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(prog="ntn", description="Fast Notion access from your terminal.")
    subparsers = parser.add_subparsers(dest="command")
    subparsers.required = True
    args = parser.parse_args()


if __name__ == "__main__":
    main()
```

**Step 4: Run tests — verify they pass**
```bash
pytest tests/test_config.py -v
```
Expected: 4 PASS

**Step 5: Commit**
```bash
git add ntn.py tests/test_config.py
git commit -m "feat: config load/save with env var and file support"
```

---

### Task 3: `ntn setup` Command

**Files:**
- Modify: `ntn.py`
- Create: `tests/test_setup.py`

**Step 1: Write failing test**
```python
# tests/test_setup.py
import json
from unittest.mock import patch

def test_setup_saves_api_key(tmp_path):
    import ntn
    inputs = iter(["ntn_testkey123", "", ""])
    with patch("builtins.input", side_effect=inputs):
        with patch("ntn.CONFIG_DIR", tmp_path / ".ntn"):
            with patch("ntn.CONFIG_FILE", tmp_path / ".ntn" / "config.json"):
                ntn.cmd_setup(None)
    config = json.loads((tmp_path / ".ntn" / "config.json").read_text())
    assert config["api_key"] == "ntn_testkey123"
```

**Step 2: Run to verify it fails**
```bash
pytest tests/test_setup.py -v
```
Expected: `AttributeError: module 'ntn' has no attribute 'cmd_setup'`

**Step 3: Add `cmd_setup` to ntn.py** (after `get_client`, before `main`):
```python
# ── Commands ─────────────────────────────────────────────────────────────────

def cmd_setup(args):
    print("ntn setup — connect your Notion workspace\n")
    print("Get your API key: https://www.notion.so/my-integrations")
    print("Create an Internal Integration and copy the token.\n")

    api_key = input("Notion API key (ntn_...): ").strip()
    if not api_key:
        print("No key entered. Aborting.")
        return

    config = {"api_key": api_key, "databases": {}}

    brain_dump_id = input("\nBrain dump parent page ID (Enter to skip): ").strip()
    if brain_dump_id:
        config["brain_dump_page_id"] = brain_dump_id

    posts_db_id = input("Posts database ID (Enter to skip): ").strip()
    if posts_db_id:
        config["databases"]["posts"] = posts_db_id

    save_config(config)
    print(f"\nSaved to {CONFIG_FILE}")
    print("Run 'ntn dump \"test\"' to verify.")
```

**Step 4: Update `main()` to wire setup command:**
```python
def main():
    parser = argparse.ArgumentParser(prog="ntn", description="Fast Notion access from your terminal.")
    subparsers = parser.add_subparsers(dest="command")
    subparsers.required = True

    p_setup = subparsers.add_parser("setup", help="Connect your Notion workspace")
    p_setup.set_defaults(func=cmd_setup)

    args = parser.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()
```

**Step 5: Run all tests**
```bash
pytest tests/ -v
```
Expected: all PASS

**Step 6: Commit**
```bash
git add ntn.py tests/test_setup.py
git commit -m "feat: ntn setup interactive wizard"
```

---

### Task 4: `ntn dump` Command

**Files:**
- Modify: `ntn.py`
- Create: `tests/test_dump.py`

**Step 1: Write failing tests**
```python
# tests/test_dump.py
from unittest.mock import patch, MagicMock

def test_dump_creates_today_page_if_missing():
    import ntn
    mock_client = MagicMock()
    mock_config = {"api_key": "test", "brain_dump_page_id": "parent-id-123", "databases": {}}
    mock_client.search.return_value = {"results": []}
    mock_client.pages.create.return_value = {"id": "new-page-id"}

    args = MagicMock()
    args.text = "Test thought"

    with patch("ntn.load_config", return_value=mock_config):
        with patch("ntn.get_client", return_value=mock_client):
            ntn.cmd_dump(args)

    mock_client.pages.create.assert_called_once()
    kwargs = mock_client.pages.create.call_args[1]
    assert kwargs["parent"]["page_id"] == "parent-id-123"

def test_dump_appends_to_existing_page():
    import ntn
    from datetime import datetime
    mock_client = MagicMock()
    mock_config = {"api_key": "test", "brain_dump_page_id": "parent-id-123", "databases": {}}
    today = datetime.now().strftime("%d-%m-%Y")
    mock_client.search.return_value = {
        "results": [{"id": "existing-id", "parent": {"page_id": "parent-id-123"},
                     "properties": {"title": {"title": [{"plain_text": today}]}}}]
    }

    args = MagicMock()
    args.text = "Appending this"

    with patch("ntn.load_config", return_value=mock_config):
        with patch("ntn.get_client", return_value=mock_client):
            ntn.cmd_dump(args)

    mock_client.pages.create.assert_not_called()
    mock_client.blocks.children.append.assert_called_once()
```

**Step 2: Run to verify they fail**
```bash
pytest tests/test_dump.py -v
```
Expected: `AttributeError: module 'ntn' has no attribute 'cmd_dump'`

**Step 3: Add helpers and `cmd_dump` to ntn.py:**
```python
def _get_today_str() -> str:
    return datetime.now().strftime("%d-%m-%Y")


def _find_today_page(client: Client, parent_id: str):
    today = _get_today_str()
    results = client.search(query=today, filter={"property": "object", "value": "page"})
    for page in results.get("results", []):
        title = "".join(t.get("plain_text", "") for t in
                        page.get("properties", {}).get("title", {}).get("title", []))
        pid = page.get("parent", {}).get("page_id", "").replace("-", "")
        if title == today and pid == parent_id.replace("-", ""):
            return page["id"]
    return None


def _append_text(client: Client, page_id: str, text: str) -> None:
    client.blocks.children.append(
        block_id=page_id,
        children=[{"object": "block", "type": "paragraph",
                   "paragraph": {"rich_text": [{"type": "text", "text": {"content": text}}]}}]
    )


def cmd_dump(args):
    config = load_config()
    parent_id = config.get("brain_dump_page_id")
    if not parent_id:
        print("No brain dump page configured. Run 'ntn setup'.")
        return
    client = get_client(config)
    try:
        page_id = _find_today_page(client, parent_id)
        if not page_id:
            today = _get_today_str()
            page = client.pages.create(
                parent={"page_id": parent_id},
                properties={"title": {"title": [{"text": {"content": today}}]}}
            )
            page_id = page["id"]
            print(f"Created page: {today}")
        _append_text(client, page_id, args.text)
        print(f"Dumped to {_get_today_str()}")
    except APIResponseError as e:
        print(f"Notion API error: {e}")
```

**Step 4: Add to `main()` before `args = parser.parse_args()`:**
```python
p_dump = subparsers.add_parser("dump", help="Add to today's brain dump")
p_dump.add_argument("text", help="Text to dump")
p_dump.set_defaults(func=cmd_dump)
```

**Step 5: Run all tests**
```bash
pytest tests/ -v
```
Expected: all PASS

**Step 6: Commit**
```bash
git add ntn.py tests/test_dump.py
git commit -m "feat: ntn dump — append to today's brain dump page"
```

---

### Task 5: `ntn today` Command

**Files:**
- Modify: `ntn.py`
- Create: `tests/test_today.py`

**Step 1: Write failing tests**
```python
# tests/test_today.py
from unittest.mock import patch, MagicMock
from datetime import datetime

def test_today_prints_content(capsys):
    import ntn
    mock_client = MagicMock()
    mock_config = {"api_key": "test", "brain_dump_page_id": "parent-id", "databases": {}}
    today = datetime.now().strftime("%d-%m-%Y")
    mock_client.search.return_value = {
        "results": [{"id": "page-id", "parent": {"page_id": "parent-id"},
                     "properties": {"title": {"title": [{"plain_text": today}]}}}]
    }
    mock_client.blocks.children.list.return_value = {
        "results": [{"type": "paragraph", "paragraph": {"rich_text": [{"plain_text": "My thought"}]}}]
    }
    args = MagicMock()
    with patch("ntn.load_config", return_value=mock_config):
        with patch("ntn.get_client", return_value=mock_client):
            ntn.cmd_today(args)
    assert "My thought" in capsys.readouterr().out

def test_today_no_page_message(capsys):
    import ntn
    mock_client = MagicMock()
    mock_config = {"api_key": "test", "brain_dump_page_id": "parent-id", "databases": {}}
    mock_client.search.return_value = {"results": []}
    args = MagicMock()
    with patch("ntn.load_config", return_value=mock_config):
        with patch("ntn.get_client", return_value=mock_client):
            ntn.cmd_today(args)
    assert "No dump yet today" in capsys.readouterr().out
```

**Step 2: Verify they fail**
```bash
pytest tests/test_today.py -v
```

**Step 3: Add `_blocks_to_text` and `cmd_today` to ntn.py:**
```python
def _blocks_to_text(client: Client, page_id: str) -> str:
    blocks = client.blocks.children.list(block_id=page_id)
    lines = []
    for block in blocks.get("results", []):
        btype = block.get("type", "")
        if btype in ("paragraph", "heading_1", "heading_2", "heading_3",
                     "bulleted_list_item", "numbered_list_item", "quote", "callout"):
            text = "".join(t.get("plain_text", "")
                           for t in block.get(btype, {}).get("rich_text", []))
            if text:
                lines.append(text)
    return "\n".join(lines)


def cmd_today(args):
    config = load_config()
    parent_id = config.get("brain_dump_page_id")
    if not parent_id:
        print("No brain dump page configured. Run 'ntn setup'.")
        return
    client = get_client(config)
    try:
        page_id = _find_today_page(client, parent_id)
        if not page_id:
            print(f"No dump yet today ({_get_today_str()}). Use 'ntn dump \"...\"' to start.")
            return
        print(f"── {_get_today_str()} ──")
        print(_blocks_to_text(client, page_id))
    except APIResponseError as e:
        print(f"Notion API error: {e}")
```

**Step 4: Add to `main()`:**
```python
p_today = subparsers.add_parser("today", help="Show today's brain dump")
p_today.set_defaults(func=cmd_today)
```

**Step 5: Run all tests**
```bash
pytest tests/ -v
```
Expected: all PASS

**Step 6: Commit**
```bash
git add ntn.py tests/test_today.py
git commit -m "feat: ntn today — print today's brain dump"
```

---

### Task 6: `ntn post add` and `ntn post list`

**Files:**
- Modify: `ntn.py`
- Create: `tests/test_posts.py`

**Step 1: Write failing tests**
```python
# tests/test_posts.py
from unittest.mock import patch, MagicMock

def test_post_add_creates_row():
    import ntn
    mock_client = MagicMock()
    mock_config = {"api_key": "test", "databases": {"posts": "posts-db-id"}}
    mock_client.pages.create.return_value = {"id": "new-row"}

    args = MagicMock()
    args.url = "https://linkedin.com/posts/example"
    args.note = "Great hook"
    args.source = "LinkedIn"

    with patch("ntn.load_config", return_value=mock_config):
        with patch("ntn.get_client", return_value=mock_client):
            ntn.cmd_post_add(args)

    kwargs = mock_client.pages.create.call_args[1]
    assert kwargs["parent"]["database_id"] == "posts-db-id"

def test_post_add_no_db_configured(capsys):
    import ntn
    args = MagicMock()
    args.url = "https://linkedin.com/posts/example"
    args.note = ""
    args.source = "LinkedIn"
    with patch("ntn.load_config", return_value={"api_key": "t", "databases": {}}):
        with patch("ntn.get_client", return_value=MagicMock()):
            ntn.cmd_post_add(args)
    assert "No posts database configured" in capsys.readouterr().out

def test_post_list_prints_results(capsys):
    import ntn
    mock_client = MagicMock()
    mock_config = {"api_key": "test", "databases": {"posts": "posts-db-id"}}
    mock_client.databases.query.return_value = {
        "results": [{
            "properties": {
                "URL": {"url": "https://linkedin.com/posts/foo"},
                "Notes": {"rich_text": [{"plain_text": "Good post"}]},
                "Source": {"select": {"name": "LinkedIn"}},
                "Date": {"date": {"start": "2026-02-19"}}
            }
        }]
    }
    args = MagicMock()
    args.limit = 10
    with patch("ntn.load_config", return_value=mock_config):
        with patch("ntn.get_client", return_value=mock_client):
            ntn.cmd_post_list(args)
    assert "linkedin.com/posts/foo" in capsys.readouterr().out
```

**Step 2: Verify they fail**
```bash
pytest tests/test_posts.py -v
```

**Step 3: Add `cmd_post_add` and `cmd_post_list` to ntn.py:**
```python
def cmd_post_add(args):
    config = load_config()
    db_id = config.get("databases", {}).get("posts")
    if not db_id:
        print("No posts database configured. Run 'ntn setup'.")
        return
    client = get_client(config)
    try:
        props = {
            "URL": {"url": args.url},
            "Date": {"date": {"start": datetime.now().strftime("%Y-%m-%d")}},
            "Source": {"select": {"name": getattr(args, "source", "LinkedIn")}},
        }
        if args.note:
            props["Notes"] = {"rich_text": [{"text": {"content": args.note}}]}
        client.pages.create(parent={"database_id": db_id}, properties=props)
        print(f"Saved: {args.url}")
    except APIResponseError as e:
        print(f"Notion API error: {e}")


def cmd_post_list(args):
    config = load_config()
    db_id = config.get("databases", {}).get("posts")
    if not db_id:
        print("No posts database configured. Run 'ntn setup'.")
        return
    client = get_client(config)
    try:
        results = client.databases.query(
            database_id=db_id,
            page_size=args.limit,
            sorts=[{"property": "Date", "direction": "descending"}]
        )
        rows = results.get("results", [])
        if not rows:
            print("No posts saved yet.")
            return
        print(f"{'Date':<12} {'Source':<12} URL")
        print("-" * 80)
        for row in rows:
            p = row["properties"]
            date = (p.get("Date", {}).get("date") or {}).get("start", "—")[:10]
            source = ((p.get("Source", {}).get("select")) or {}).get("name", "—")
            url = p.get("URL", {}).get("url", "—")
            notes_rt = p.get("Notes", {}).get("rich_text", [])
            notes = "".join(t.get("plain_text", "") for t in notes_rt)[:40]
            print(f"{date:<12} {source:<12} {url[:50]}")
            if notes:
                print(f"{'':>26} {notes}")
    except APIResponseError as e:
        print(f"Notion API error: {e}")
```

**Step 4: Add to `main()`:**
```python
p_post = subparsers.add_parser("post", help="Manage saved posts")
post_sub = p_post.add_subparsers(dest="post_command")
post_sub.required = True

p_post_add = post_sub.add_parser("add", help="Save a post URL")
p_post_add.add_argument("url", help="URL of the post")
p_post_add.add_argument("--note", default="", help="Your note about this post")
p_post_add.add_argument("--source", default="LinkedIn", help="Source platform")
p_post_add.set_defaults(func=cmd_post_add)

p_post_list = post_sub.add_parser("list", help="List saved posts")
p_post_list.add_argument("--limit", type=int, default=10)
p_post_list.set_defaults(func=cmd_post_list)
```

**Step 5: Run all tests**
```bash
pytest tests/ -v
```
Expected: all PASS

**Step 6: Commit**
```bash
git add ntn.py tests/test_posts.py
git commit -m "feat: ntn post add/list — save and browse posts"
```

---

### Task 7: `ntn search` and `ntn read`

**Files:**
- Modify: `ntn.py`
- Create: `tests/test_search.py`

**Step 1: Write failing tests**
```python
# tests/test_search.py
from unittest.mock import patch, MagicMock

def test_search_prints_results(capsys):
    import ntn
    mock_client = MagicMock()
    mock_client.search.return_value = {
        "results": [{"id": "p1", "object": "page", "url": "https://notion.so/test",
                     "properties": {"title": {"title": [{"plain_text": "My Test Page"}]}}}]
    }
    args = MagicMock()
    args.query = "test"
    with patch("ntn.load_config", return_value={"api_key": "t", "databases": {}}):
        with patch("ntn.get_client", return_value=mock_client):
            ntn.cmd_search(args)
    assert "My Test Page" in capsys.readouterr().out

def test_read_prints_content(capsys):
    import ntn
    mock_client = MagicMock()
    mock_client.search.return_value = {
        "results": [{"id": "p1", "properties": {"title": {"title": [{"plain_text": "My Page"}]}}}]
    }
    mock_client.blocks.children.list.return_value = {
        "results": [{"type": "paragraph", "paragraph": {"rich_text": [{"plain_text": "Content here"}]}}]
    }
    args = MagicMock()
    args.title = "My Page"
    with patch("ntn.load_config", return_value={"api_key": "t", "databases": {}}):
        with patch("ntn.get_client", return_value=mock_client):
            ntn.cmd_read(args)
    assert "Content here" in capsys.readouterr().out
```

**Step 2: Verify they fail**
```bash
pytest tests/test_search.py -v
```

**Step 3: Add `cmd_search` and `cmd_read` to ntn.py:**
```python
def cmd_search(args):
    config = load_config()
    client = get_client(config)
    try:
        results = client.search(query=args.query)
        items = results.get("results", [])
        if not items:
            print("No results.")
            return
        for item in items[:20]:
            obj = item.get("object", "")
            if obj == "page":
                title = "".join(t.get("plain_text", "") for t in
                                item.get("properties", {}).get("title", {}).get("title", [])) or "Untitled"
            elif obj == "database":
                title = "".join(t.get("plain_text", "") for t in item.get("title", [])) or "Untitled DB"
            else:
                continue
            print(f"[{obj}] {title}\n       {item.get('url', '')}\n")
    except APIResponseError as e:
        print(f"Notion API error: {e}")


def cmd_read(args):
    config = load_config()
    client = get_client(config)
    try:
        results = client.search(query=args.title, filter={"property": "object", "value": "page"})
        pages = results.get("results", [])
        if not pages:
            print(f"No page found: {args.title}")
            return
        page = pages[0]
        title = "".join(t.get("plain_text", "") for t in
                        page.get("properties", {}).get("title", {}).get("title", [])) or "Untitled"
        print(f"── {title} ──")
        print(_blocks_to_text(client, page["id"]))
    except APIResponseError as e:
        print(f"Notion API error: {e}")
```

**Step 4: Add to `main()`:**
```python
p_search = subparsers.add_parser("search", help="Search your Notion workspace")
p_search.add_argument("query")
p_search.set_defaults(func=cmd_search)

p_read = subparsers.add_parser("read", help="Read a page by title")
p_read.add_argument("title")
p_read.set_defaults(func=cmd_read)
```

**Step 5: Run all tests**
```bash
pytest tests/ -v
```
Expected: all PASS

**Step 6: Commit**
```bash
git add ntn.py tests/test_search.py
git commit -m "feat: ntn search and ntn read commands"
```

---

### Task 8: README

**Files:**
- Create: `README.md`

**Step 1: Create README.md with the following content:**

```markdown
# ntn — Notion CLI

> Fast terminal access to any Notion workspace. Built for AI-assisted workflows.

## Why this exists

Running Notion's MCP server costs ~23k tokens in context just to be *available* — before a single call. `ntn` lets Claude (or you) access Notion with a single Bash command. Zero token overhead. No MCP server running.

## Install

```bash
git clone https://github.com/YOUR_USERNAME/notion-cli.git
cd notion-cli
pip install -e .
```

## Setup

Get a free API key at [notion.so/my-integrations](https://notion.so/my-integrations) — create an Internal Integration.

```bash
ntn setup
```

Or use environment variable directly:
```bash
export NOTION_API_KEY=ntn_your_key_here
```

## Commands

### Brain dumps
```bash
ntn dump "had a great call today, the client wants..."
ntn today
```

### Save posts (LinkedIn, articles, anything)
```bash
ntn post add "https://linkedin.com/posts/..." --note "love the hook"
ntn post list
ntn post list --limit 20
```

### Search & read
```bash
ntn search "marketing agency pain points"
ntn read "19-02-2026"
```

### Query databases
```bash
ntn db query leads
ntn db query posts
```

## Using with Claude

Claude can call `ntn` directly via Bash — no MCP, no round-trips:

```
User: What did I write in my brain dump today?
Claude: [runs: ntn today] → reads output → responds
```

```
User: Save this LinkedIn post I liked: linkedin.com/posts/xyz
Claude: [runs: ntn post add "linkedin.com/posts/xyz" --note "good framework"]
```

## Contributing

PRs welcome. Keep it simple — this is a utility tool, not a framework.
```

**Step 2: Commit**
```bash
git add README.md
git commit -m "docs: README with install, usage, and Claude angle"
```

---

### Task 9: GitHub Push

**Step 1: Create public GitHub repo**
```bash
gh repo create notion-cli --public \
  --description "Fast Notion CLI for AI-assisted workflows — designed for Claude and LLMs"
```

**Step 2: Add remote and push**
```bash
git remote add origin https://github.com/dawoodkhan92/notion-cli.git
git push -u origin main
```

**Step 3: Verify**
```bash
gh repo view dawoodkhan92/notion-cli --web
```

---

## Done

All commands working, all tests passing, live on GitHub.

To use immediately:
```bash
export NOTION_API_KEY=ntn_YOUR_KEY_HERE
ntn setup   # configure your brain dump page and posts database
ntn dump "first test dump from the CLI"
```
