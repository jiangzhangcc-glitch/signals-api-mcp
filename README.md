# AI Signals MCP server

An [MCP](https://modelcontextprotocol.io) server that gives any MCP client
(Claude Desktop, Cursor, and other agent hosts) direct access to **AI Signals** —
a machine-written daily dataset and digest of AI signals: trending GitHub repos,
Hugging Face models, arXiv papers and more, one item per source per day.

Data source: **https://data.jiangzhang.ca/signals4/** — the daily digest is free,
no account and no card required.

## Quick start

1. Download `mcp_server.py` from this repository.
2. Point your MCP client at it (stdio transport):

```json
{"mcpServers": {"signals": {"command": "python3", "args": ["/path/to/mcp_server.py"]}}}
```

Requires Python 3.8+ and **no dependencies at all** (standard library only).

> Note for anyone writing their own client against the same API: send a
> `User-Agent` header. The CDN in front of the API rejects requests with a bare
> `Python-urllib/...` or empty User-Agent with HTTP 403 at the edge. This server
> already sends one.

## Tools

| Tool | What it returns |
|---|---|
| `daily_signals` | today's signals — the same 4 picks as the free daily digest |
| `what_changed` | what moved since the previous edition (rank changes, new entries) |
| `top_models` | tracked Hugging Face models with momentum and rank change |
| `top_repos` | tracked GitHub repositories with momentum and rank change |
| `archive_days` | previous editions by date |

Every tool answers with attributed text: each item links to the original source.

## Free tier

- 4 signals a day (one per core source), every edition archived
- Daily digest page: https://data.jiangzhang.ca/signals4/latest.html
- JSON API: https://data.jiangzhang.ca/signals4/api/today.json
- Dataset on GitHub and Hugging Face: CC BY 4.0, free for commercial use with attribution

## More than this (paid feed)

- **BASIC — CA$9.90/month** — Core 4 sources, 18 boards × Top 3 per board, one morning push email (08:00 Beijing).
  Subscribe: https://data.jiangzhang.ca/signals4/buy?plan=basic
- **PLUS — CA$29.90/month** — All 8 sources, choose push method and times (4×/day), Top 3 per board, plus API access to today's signals and stats.
  Subscribe: https://data.jiangzhang.ca/signals4/buy?plan=plus
- **BUSINESS — CA$129.90/month** — PLUS, plus your own content and quantity per board (3–10), searchable history and full export.
  Subscribe: https://data.jiangzhang.ca/signals4/buy?plan=business

All plans side by side: https://data.jiangzhang.ca/signals4/about.html

### No subscription

Prefer to pay once? There is a one-time option:
https://buy.stripe.com/00w28r4W08qq8CcecHgw008

## Attribution

If you republish this data, keep the attribution:

> AI Signals, *AI Signals Daily*, https://github.com/jiangzhangcc-glitch/ai-signals-daily (data) /
> https://data.jiangzhang.ca/signals4/archive/ (digest)

## License

Server code: use it freely. Data: CC BY 4.0 (attribution required). Each item links
to its original source; we do not rewrite it.
