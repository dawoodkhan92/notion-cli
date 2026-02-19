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


# ── Entry point ───────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(prog="ntn", description="Fast Notion access from your terminal.")
    subparsers = parser.add_subparsers(dest="command")
    subparsers.required = True
    args = parser.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
