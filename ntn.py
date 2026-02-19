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


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(prog="ntn", description="Fast Notion access from your terminal.")
    subparsers = parser.add_subparsers(dest="command")
    subparsers.required = True

    p_setup = subparsers.add_parser("setup", help="Connect your Notion workspace")
    p_setup.set_defaults(func=cmd_setup)

    p_dump = subparsers.add_parser("dump", help="Add to today's brain dump")
    p_dump.add_argument("text", help="Text to dump")
    p_dump.set_defaults(func=cmd_dump)

    p_today = subparsers.add_parser("today", help="Show today's brain dump")
    p_today.set_defaults(func=cmd_today)

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

    p_search = subparsers.add_parser("search", help="Search your Notion workspace")
    p_search.add_argument("query")
    p_search.set_defaults(func=cmd_search)

    p_read = subparsers.add_parser("read", help="Read a page by title")
    p_read.add_argument("title")
    p_read.set_defaults(func=cmd_read)

    args = parser.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
