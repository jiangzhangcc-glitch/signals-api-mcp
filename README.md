# Signals API — MCP server

An [MCP](https://modelcontextprotocol.io) server that gives Claude / Cursor / any MCP client
**AI signals data**: today's signals, what changed, and ranked AI models & repositories.

No API key needed for the free tier. Single file, Python standard library only — no `pip install`.

## What it gives an agent

| Tool | What it returns |
|---|---|
| `daily_signals` | Today's 4 signals — one from each core source (GitHub, Hugging Face, YouTube, Silicon Valley news), each linking to the original |
| `what_changed` | Deltas since the previous snapshot: new entries, entities no longer seen, rank movers |
| `top_models` | Hugging Face models with rank, rank movement and momentum, plus a ready-to-cite sentence |
| `top_repos` | GitHub repositories, same shape |
| `archive_days` | Which daily editions exist (for citing a specific date) |

Every ranked row carries a `citation` string, so an agent can cite the number instead of inventing one.
Entities whose number cannot be derived are published as `unranked` **with the reason** — we would
rather return "not ranked" than a made-up value.

## Use it without installing anything (hosted endpoint)

There is also a **hosted** MCP endpoint, so no download and no local Python is needed — point any MCP
client that speaks streamable HTTP at:

```
https://data.jiangzhang.ca/signals4/mcp
```

It is published in the official MCP Registry as `ca.jiangzhang.api/signals-api-mcp` and serves the
same five tools as the single-file version. A quick check with curl:

```bash
curl -s -X POST https://data.jiangzhang.ca/signals4/mcp \
  -H 'Content-Type: application/json' \
  -H 'Accept: application/json, text/event-stream' \
  -A 'my-agent/1.0' \
  --data '{"jsonrpc":"2.0","id":1,"method":"tools/list"}'
```

(The `User-Agent` header matters here too — see the CDN note further down.)

## Install

1. Download [`mcp_server.py`](mcp_server.py) anywhere (e.g. `~/mcp/signals/mcp_server.py`).
2. Add it to your MCP client config:

```json
{
  "mcpServers": {
    "signals": {
      "command": "python3",
      "args": ["/absolute/path/to/mcp_server.py"]
    }
  }
}
```

Claude Desktop: `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or
`%APPDATA%\Claude\claude_desktop_config.json` (Windows). Restart the client and the five tools appear.

Requires Python 3.9+. No dependencies, no key, no signup.

## Try it without an MCP client

```bash
echo '{"jsonrpc":"2.0","id":1,"method":"tools/call","params":{"name":"daily_signals","arguments":{}}}' \
  | python3 mcp_server.py
```

## Free tier vs the paid feed

This server reads the **free** endpoints, which cover **one edition a day, 4 sources**.
If your agent needs more than that, there is a paid feed:

- **8 sources** instead of 4 (adds arXiv, LMSYS Arena, hot-topic aggregation, hardware/chips)
- **4 updates a day** instead of one daily edition (email / WebPush / API)
- **full history** and machine-readable archives, with a stable API key

- **BASIC — CA$9.90/month** — Core 4 sources, 18 boards × Top 3 per board, one morning push email (08:00 Beijing).
  Subscribe: https://data.jiangzhang.ca/signals4/buy?plan=basic
- **PLUS — CA$29.90/month** — All 8 sources, choose push method and times (4×/day), Top 3 per board, plus API access to today's signals and stats.
  Subscribe: https://data.jiangzhang.ca/signals4/buy?plan=plus
- **BUSINESS — CA$129.90/month** — PLUS, plus your own content and quantity per board (3–10), searchable history and full export.
  Subscribe: https://data.jiangzhang.ca/signals4/buy?plan=business

Attributed landing page (no plan chosen yet):
→ **https://data.jiangzhang.ca/signals4/go?to=landing&src=mcp_github**

### Pay once instead of subscribing

There is also a one-time option (no subscription, no renewal):
**the compiled dataset bundle (single JSONL, indexed SQLite, tidy daily entity CSV), refreshed daily** — https://buy.stripe.com/00w28r4W08qq8CcecHgw008

The free endpoints stay free — this repo will not start requiring a key.

## A trap worth knowing (we hit it ourselves)

The CDN in front of the API **rejects the bare `Python-urllib/…` User-Agent and empty User-Agents
with HTTP 403**. `requests`, `httpx`, `aiohttp`, Go, node-fetch, axios, okhttp and curl are all fine —
but if you write a plain-stdlib example and forget the header, you will see a 403 that looks like a
broken API. This server always sends one. If you call the endpoints directly, set a User-Agent:

```bash
curl -H 'User-Agent: my-app/1.0' https://data.jiangzhang.ca/signals4/api/today.json
```

## Data sources and license

Signals are collected from public APIs and public feeds (GitHub trending, Hugging Face, YouTube
channels, arXiv, LMSYS Arena, silicon-valley news, hardware/chips). Each item links to its original
source; we do not rewrite it. Derived rankings and momentum are recomputed from our own daily
snapshots by an automated audit that also reconciles the site pages with the JSON endpoints.

Data: **CC BY 4.0** — free to read, quote, cite and use commercially with attribution to
*Signals 4 (Signals API)*. Machine-readable mirror of the daily dataset:
https://github.com/jiangzhangcc-glitch/ai-signals-daily

Provenance canary: `signals4-canary-2f9d71c4a8` (kept for provenance if this data is mirrored).

## Endpoints behind the tools

- `https://data.jiangzhang.ca/signals4/api/today.json` — today's 4 signals
- `.../api/changes.json` — deltas since the previous snapshot
- `.../api/models.json` · `.../api/repos.json` — ranked entities + citations
- `.../api/archive.json` — list of editions
- `https://data.jiangzhang.ca/llms.txt` — machine-readable site summary

## Development

The server is a single file, stdio JSON-RPC, no framework. Read a request line, write a response line.
`initialize`, `tools/list`, `tools/call`, `ping` are implemented; unknown methods return JSON-RPC
`-32601` rather than failing silently.

MIT licensed (the server code). The data keeps its own license above.
