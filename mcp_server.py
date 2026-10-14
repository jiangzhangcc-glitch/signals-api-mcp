#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Signals API MCP server — AI signals data for agents (2026-10-14).

为什么做这个：我们三周的结论是"没人搜我们的内容，但机器会来拿我们的数据"
（公开数据集仓库 14 天被 clone 719 次 / 310 个独立来源）。
所以分发要走**机器能直接消费的形态**，而不是网页：
MCP 让 Claude / Cursor 这类 agent 直接把「今天的 AI 信号 / 什么在变化」当工具用。

设计：
  · **单文件、只用标准库** —— 别人一条命令就能跑，不需要装我们的任何东西。
  · 只读公开端点（data.jiangzhang.ca/signals4/api/*.json），**不需要密钥**即可用。
  · 免费档给"今天 4 条 + 变化 + 实体榜"；需要 8 源/更高频/全历史时给付费入口
    （付费入口是 URL，不在这里做鉴权 —— 别把付费逻辑塞进客户端）。
  · 任何网络失败都返回**明确错误**，不返回空数据（空数据会被 agent 当成"没有信号"）。

用法（stdio，MCP 标准）:
  python3 mcp_server.py
客户端配置示例:
  {"mcpServers": {"signals": {"command": "python3", "args": ["/path/to/mcp_server.py"]}}}
"""
from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request

API = "https://data.jiangzhang.ca/signals4/api"
DIGEST = "https://data.jiangzhang.ca/signals4/latest.html"
TIMEOUT = 25
# **必须带 User-Agent**（2026-10-14 实测）：Cloudflare 会拦掉裸的 `Python-urllib/…`
# 与空 UA（403，且在边缘就挡掉、连我们服务器都看不到）。urllib 默认 UA 正好是被拦的那种 ——
# 所以任何用标准库写的示例代码都会"看起来 API 坏了"。这里显式带上身份。
USER_AGENT = "SignalsAPI-MCP/1.0 (+https://data.jiangzhang.ca/signals4/; data feed client)"
# 付费入口（点击会被我们计数，`src=mcp` 用来归因是 agent 通道带来的）
MORE = "https://data.jiangzhang.ca/signals4/go?to=landing&src=mcp"
PROTOCOL = "2024-11-05"


def _get(path: str):
    """返回 (ok, obj_or_error)。失败必须有明确原因 —— 不返回空数据。"""
    url = f"{API}/{path}"
    req = urllib.request.Request(url)
    req.add_header("User-Agent", USER_AGENT)
    req.add_header("Accept", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            return True, json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        hint = ""
        if e.code == 403:
            hint = (" — HTTP 403 from the CDN usually means a missing/blocked User-Agent; "
                    "set one in your client (this server already sends: %s)" % USER_AGENT)
        return False, f"HTTP {e.code} fetching {url}{hint}"
    except Exception as e:
        return False, f"{type(e).__name__} fetching {url}: {e}"


def _text(s: str) -> dict:
    return {"content": [{"type": "text", "text": s}]}


def _err(s: str) -> dict:
    return {"content": [{"type": "text", "text": s}], "isError": True}


TOOLS = [
    {
        "name": "daily_signals",
        "description": ("Today's AI signals from Signals API: exactly 4 items, one from each core "
                        "source (GitHub, Hugging Face, YouTube, Silicon Valley news), each linking "
                        "to the original. Use when the user asks what's new in AI today."),
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "what_changed",
        "description": ("What changed in the AI landscape since the previous snapshot: new entries, "
                        "entities no longer seen, and rank movers. Use when the user asks what's "
                        "moving, rising, or different lately."),
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "top_models",
        "description": ("Hugging Face models we track, with rank, rank change and 7-day momentum. "
                        "Entries without a derivable number are marked 'not ranked' with a reason "
                        "instead of a guessed value."),
        "inputSchema": {"type": "object",
                        "properties": {"limit": {"type": "integer", "minimum": 1, "maximum": 50}},
                        "additionalProperties": False},
    },
    {
        "name": "top_repos",
        "description": ("GitHub repositories we track, with rank, rank change and momentum. "
                        "Use when the user asks which open-source AI projects are trending."),
        "inputSchema": {"type": "object",
                        "properties": {"limit": {"type": "integer", "minimum": 1, "maximum": 50}},
                        "additionalProperties": False},
    },
    {
        "name": "archive_days",
        "description": ("List the archived daily editions (dates) available from the free digest. "
                        "Use to find which dates can be cited."),
        "inputSchema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
]


def _fmt_picks(o: dict) -> str:
    """按 today.json 的**真实结构**渲染（2026-10-14 实测：字段是 signals 而不是 picks）。"""
    items = o.get("signals") or o.get("picks") or []
    lines = [f"# {o.get('date')} — {len(items)} signals", str(o.get("summary") or "").strip()]
    for p in items:
        lines.append(f"- [{p.get('source')}] {p.get('title')}\n  {p.get('url')}")
        note = (p.get("note") or "").strip()
        if note:
            lines.append(f"  note: {note}")
    if o.get("citation"):
        lines.append(f"\nCitation: {o['citation']}")
    lines.append(f"\nFree digest: {DIGEST}\nMore sources / 4x daily / full history: {MORE}")
    return "\n".join(lines)


def _fmt_ranked(o: dict, limit: int) -> str:
    """按 models.json / repos.json 的真实结构渲染（entries + value/metric/momentum）。"""
    ents = o.get("entries") or []
    ranked = [e for e in ents if e.get("rank")]
    ranked.sort(key=lambda e: e["rank"])
    lines = [f"# {o.get('endpoint', '').rsplit('/', 1)[-1]} — ranked by {o.get('metric')} "
             f"(as of {o.get('as_of')})",
             f"tracked {o.get('count')} · ranked {o.get('ranked_count')} · "
             f"unranked {o.get('unranked_count')} (number not derivable → published as-is)"]
    for e in ranked[:limit]:
        bits = [f"{e.get('metric')}={e.get('value')}"]
        if e.get("rank_change") not in (None, 0):
            bits.append(f"rank move {e['rank_change']:+d} since {e.get('rank_baseline_date')}")
        if e.get("value_change_pct") not in (None, ""):
            bits.append(f"value change {e['value_change_pct']}%")
        if e.get("momentum") not in (None, ""):
            bits.append(f"momentum={e['momentum']}")
        if e.get("days_tracked"):
            bits.append(f"tracked {e['days_tracked']}d")
        lines.append(f"- #{e['rank']} {e.get('name')} ({e.get('org')}) — " + ", ".join(bits))
        if e.get("citation"):
            lines.append(f"  cite: {e['citation']}")
    lines.append(f"\nSource: {o.get('endpoint')} · more history: {MORE}")
    return "\n".join(lines)


def _fmt_changes(o: dict) -> str:
    """changes.json 的真实结构：{as_of, changes:{models:{...}, repos:{...}, arena, indexation}}"""
    ch = o.get("changes") or {}
    lines = [f"# What changed (as of {o.get('as_of')})"]
    for area, d in ch.items():
        if not isinstance(d, dict):
            lines.append(f"- {area}: {d}")
            continue
        bits = []
        for k in ("previous_snapshot", "entered_count", "not_seen_today_count", "mover_count",
                  "as_of", "metric"):
            if d.get(k) not in (None, ""):
                bits.append(f"{k}={d[k]}")
        ex = d.get("examples") or d.get("entered_examples") or []
        if ex:
            names = [e.get("name") if isinstance(e, dict) else str(e) for e in ex[:5]]
            bits.append("examples=" + "; ".join(str(n) for n in names))
        lines.append(f"- **{area}**: " + (", ".join(bits) if bits else json.dumps(d, ensure_ascii=False)[:200]))
    lines.append(f"\nFull deltas: {API}/changes.json · more history: {MORE}")
    return "\n".join(lines)


def call(name: str, args: dict):
    if name == "daily_signals":
        ok, o = _get("today.json")
        return _text(_fmt_picks(o)) if ok else _err(f"Signals API unavailable: {o}")
    if name == "what_changed":
        ok, o = _get("changes.json")
        return _text(_fmt_changes(o)) if ok else _err(f"Signals API unavailable: {o}")
    if name == "top_models":
        ok, o = _get("models.json")
        return _text(_fmt_ranked(o, int(args.get("limit") or 10))) if ok else _err(f"unavailable: {o}")
    if name == "top_repos":
        ok, o = _get("repos.json")
        return _text(_fmt_ranked(o, int(args.get("limit") or 10))) if ok else _err(f"unavailable: {o}")
    if name == "archive_days":
        ok, o = _get("archive.json")
        if not ok:
            return _err(f"unavailable: {o}")
        eds = o.get("editions") or []
        days = [e.get("date") if isinstance(e, dict) else e for e in eds]
        # 2026-10-14（第 23 轮）：补上付费入口。
        # 逐面审计发现：5 个工具里只有 `archive_days` 的输出**没有**任何付费入口 ——
        # 其余四个都有 `MORE`，`initialize.instructions` 也明确写着 "is a paid feed"。
        # 一个工具漏掉，就等于"调用这个工具的人永远不知道还有付费层"，
        # 而这种不一致没有任何告警，只能靠逐个跑一遍才发现。
        return _text(f"Archived free editions ({o.get('count')}): " + ", ".join(map(str, days[-40:]))
                     + f"\n\nDigest archive: https://data.jiangzhang.ca/signals4/archive/"
                     + f"\nMore sources / 4x daily / full history: {MORE}")
    return _err(f"Unknown tool: {name}")


def handle(req: dict):
    """返回响应 dict，或 None（通知类消息不回复）。"""
    method = req.get("method")
    rid = req.get("id")
    if method == "initialize":
        want = ((req.get("params") or {}).get("protocolVersion")) or PROTOCOL
        return {"jsonrpc": "2.0", "id": rid, "result": {
            "protocolVersion": want,
            "capabilities": {"tools": {"listChanged": False}},
            "serverInfo": {"name": "signals-api", "version": "1.0.0"},
            "instructions": ("AI signals data: today's 4 signals, what changed, tracked models/repos. "
                             "Free tier covers one edition a day; 8 sources / 4x daily / full history "
                             f"is a paid feed: {MORE}")}}
    if method in ("notifications/initialized", "initialized"):
        return None
    if method == "tools/list":
        return {"jsonrpc": "2.0", "id": rid, "result": {"tools": TOOLS}}
    if method == "tools/call":
        p = req.get("params") or {}
        res = call(p.get("name") or "", p.get("arguments") or {})
        return {"jsonrpc": "2.0", "id": rid, "result": res}
    if method == "ping":
        return {"jsonrpc": "2.0", "id": rid, "result": {}}
    if rid is None:
        return None
    return {"jsonrpc": "2.0", "id": rid,
            "error": {"code": -32601, "message": f"Method not found: {method}"}}


def main() -> int:
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            req = json.loads(line)
        except Exception:
            continue
        resp = handle(req)
        if resp is not None:
            sys.stdout.write(json.dumps(resp, ensure_ascii=False) + "\n")
            sys.stdout.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
