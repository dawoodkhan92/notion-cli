# ntn — Notion CLI

> Fast terminal access to any Notion workspace. Built for AI-assisted workflows.

## Why this exists

Running Notion's MCP server costs ~23k tokens in context just to be *available* — before a single call. `ntn` lets Claude (or you) access Notion with a single Bash command. Zero token overhead. No MCP server running.

## Install

```bash
git clone https://github.com/dawoodkhan92/notion-cli.git
cd notion-cli
pip install -e .
```

## Setup

Get a free API key at [notion.so/my-integrations](https://notion.so/my-integrations) — create an Internal Integration and share your pages with it.

```bash
ntn setup
```

Or skip setup and use an environment variable directly:
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

Claude can call `ntn` directly via Bash — no MCP, no round-trips, zero token overhead:

```
User: What did I write in my brain dump today?
Claude: [runs: ntn today] → reads output → responds
```

```
User: Save this LinkedIn post I liked: linkedin.com/posts/xyz
Claude: [runs: ntn post add "linkedin.com/posts/xyz" --note "good framework"]
```

```
User: Search my Notion for notes on marketing agency pain points
Claude: [runs: ntn search "marketing agency pain points"] → reads output → responds
```

## Contributing

PRs welcome. Keep it simple — this is a utility tool, not a framework.

Open an issue first if you want to add a new command.
