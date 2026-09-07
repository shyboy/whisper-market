"""A self-contained, read-only player journal. No server, trackers, or hidden facts."""
import base64
import html
import os
from pathlib import Path
import tempfile


def escape(value):
    return html.escape(str(value), quote=True)


def rows(values, empty):
    return "".join(f"<li>{escape(v)}</li>" for v in values) or f"<li class='muted'>{escape(empty)}</li>"


def render(game, slot):
    s = game.status(slot)
    root = Path(__file__).resolve().parents[1]
    picture = root / "assets" / s["scene"]["image"]
    image = "data:image/png;base64," + base64.b64encode(picture.read_bytes()).decode() if picture.is_file() else ""
    ending = s["ending_detail"]
    title = ending["title"] if ending else "失窃的账本"
    subtitle = ending["text"] if ending else "有人丢了一本账。有人丢不起自己的名字。"
    phase = "第一章 · 已完结" if s["epilogue"] else "第一章 · 待读尾声" if ending else "第一章 · 进行中"
    clues = "".join(f"<details open><summary>线索 {i + 1:02d}</summary><p>{escape(v)}</p></details>" for i, v in enumerate(s["clues"].values())) or "<p class='muted'>先观察身边的人。听见的传闻，也要亲自核对。</p>"
    page = TEMPLATE.replace("{{IMAGE}}", image).replace("{{PHASE}}", phase)
    replacements = {
        "TITLE": title, "SUBTITLE": subtitle, "SCENE": s["scene"]["name"],
        "SCENE_TEXT": s["scene"]["text"], "COINS": s["coins"], "TICK": s["tick"],
        "BACKUP": s["backup"], "SLOT": slot, "REV": s["revision"],
        "GUARD": f"{s['reputation']['guard']:+d}", "GUILD": f"{s['reputation']['guild']:+d}",
        "NEARBY": " · ".join(n["name"] for n in s["nearby"]),
    }
    for key, value in replacements.items():
        page = page.replace("{{" + key + "}}", escape(value))
    for key, value in {
        "CLUES": clues, "ITEMS": rows(s["items"], "行囊暂空"),
        "PROMISES": rows(s["promises"], "暂无未兑现承诺"),
        "NOTES": rows(s["notes"], "还没有记下想法。你可以明确表示：这句话只是心里想，没有说出口。"),
        "RECENT": rows(s["recent"], "此刻，一切尚未发生。"),
    }.items():
        page = page.replace("{{" + key + "}}", value)
    destination = game.home / "panels" / f"{slot}.html"
    destination.parent.mkdir(parents=True, exist_ok=True)
    fd, temp = tempfile.mkstemp(dir=destination.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            handle.write(page)
        os.replace(temp, destination)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)
    return destination


TEMPLATE = """<!doctype html>
<html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>窃语黑市 · {{TITLE}}</title>
<style>
:root{color-scheme:dark;--paper:#101a1a;--line:#334241;--gold:#d6bb84;--ink:#f2ecdf;--muted:#aab5af}
*{box-sizing:border-box}body{margin:0;background:#0b1213;color:var(--ink);font:16px/1.75 'Microsoft YaHei','PingFang SC',sans-serif}button,a{font:inherit}button{cursor:pointer;border:1px solid #647269;color:var(--ink);background:#172223;padding:8px 18px;border-radius:5px}button:hover{border-color:var(--gold)}button:focus-visible,summary:focus-visible{outline:3px solid var(--gold);outline-offset:4px}header{height:78px;border-bottom:1px solid var(--line);display:flex;align-items:center;justify-content:space-between;padding:0 max(5vw,22px);gap:20px}.brand{letter-spacing:.2em;font-size:22px}.eyebrow{color:var(--gold);font-size:12px;letter-spacing:.15em}.muted,small{color:var(--muted)}main{max-width:1320px;margin:auto;padding:32px max(3vw,20px) 56px}.hero{position:relative;min-height:475px;border:1px solid #42504a;border-radius:10px;overflow:hidden;background:#203533}.hero img{position:absolute;width:100%;height:100%;object-fit:cover;opacity:.83}.hero:after{content:'';position:absolute;inset:0;background:linear-gradient(0deg,#0b1213 0%,#0b121370 44%,transparent 80%)}.hero-text{position:relative;z-index:1;padding:190px 40px 35px;max-width:770px}h1{font:46px/1.2 'Songti SC','SimSun',serif;letter-spacing:.1em;margin:16px 0}h2{font-size:18px;margin:0 0 14px;color:var(--gold);font-weight:500}p{margin:10px 0}.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:1px;background:var(--line);border:1px solid var(--line);border-radius:8px;overflow:hidden;margin:22px 0}.stat{padding:17px 23px;background:var(--paper)}.stat strong{display:block;font-size:24px;font-weight:500}.columns{display:grid;grid-template-columns:1.55fr 1fr;gap:22px}.card{background:var(--paper);padding:25px;border:1px solid var(--line);border-radius:8px;margin-bottom:22px}.card ul{padding-left:20px;margin:0}.card li{margin:9px 0}details{border-top:1px solid var(--line);padding:12px 0}summary{cursor:pointer;color:var(--gold)}details p{color:#d5ded6}nav{display:flex;gap:10px;margin-bottom:16px;flex-wrap:wrap}nav button[aria-pressed=true]{color:#101a1a;background:var(--gold);border-color:var(--gold)}[hidden]{display:none!important}.place{font-size:20px}.footer{display:flex;justify-content:space-between;gap:20px;font-size:12px;color:var(--muted);border-top:1px solid var(--line);padding-top:18px}.help{background:#20302c;border-left:3px solid var(--gold);padding:15px 20px;margin-top:16px}.seal{font-family:serif;font-size:16px;border:1px solid #7c7053;padding:3px 10px;color:var(--gold)}
@media(max-width:740px){header{height:auto;padding:18px 20px;align-items:flex-start}.brand{font-size:18px}.seal{display:none}.hero{min-height:410px}.hero-text{padding:170px 24px 25px}h1{font-size:36px}.stats{grid-template-columns:repeat(2,1fr)}.stat{padding:13px 18px}.columns{grid-template-columns:1fr}.footer{display:block}.card{padding:20px}}
</style>
<header><div><div class="brand">窃语黑市</div><div class="eyebrow">WHISPER MARKET / SHARDFALL</div></div><span class="seal">每句话都有价</span><button onclick="location.reload()" aria-label="重新载入最新情报面板">刷新情报</button></header>
<main><section class="hero" aria-label="当前章节"><img src="{{IMAGE}}" alt="{{SCENE}}的氛围插画，物品归属以行囊记录为准"><div class="hero-text"><div class="eyebrow">{{PHASE}}</div><h1>{{TITLE}}</h1><p>{{SUBTITLE}}</p><small>在 Codex 对话里行动；这里替你记住已经发生的事。</small></div></section>
<section class="stats" aria-label="角色状态"><div class="stat"><small>随身金币</small><strong>{{COINS}}</strong></div><div class="stat"><small>已过场景时段</small><strong>{{TICK}}</strong></div><div class="stat"><small>卫队关系 · 已知后果</small><strong>{{GUARD}}</strong></div><div class="stat"><small>工团关系 · 已知后果</small><strong>{{GUILD}}</strong></div></section>
<div class="columns"><div><nav aria-label="情报分类"><button aria-pressed="true" data-tab="clues">已知线索</button><button aria-pressed="false" data-tab="recent">近期经历</button><button aria-pressed="false" data-tab="notes">私密笔记</button></nav><section class="card" id="clues"><h2>情报簿</h2>{{CLUES}}</section><section class="card" id="recent" hidden><h2>发生过的事</h2><ul>{{RECENT}}</ul></section><section class="card" id="notes" hidden><h2>没有说出口的想法</h2><ul>{{NOTES}}</ul></section></div>
<aside><section class="card"><h2>此刻所在</h2><p class="place">{{SCENE}}</p><p class="muted">{{SCENE_TEXT}}</p><small>在场：{{NEARBY}}</small></section><section class="card"><h2>行囊与凭据</h2><ul>{{ITEMS}}</ul><p class="muted">外存备份：{{BACKUP}}</p></section><section class="card"><h2>尚在身上的承诺</h2><ul>{{PROMISES}}</ul></section></aside></div>
<div class="help">在 Codex 对话中，用自己的话描述行动即可。</div><p class="muted"><small>插画只表现氛围；场景、物品与关系以本页文字记录为准。面板是本地快照；操作后刷新查看。分享游戏包不会分享你的存档。</small></p>
<footer class="footer"><span>《失窃的账本》 · v0.1.0</span><span>存档 {{SLOT}} · 记录 {{REV}} · 本地保存</span></footer></main>
<script>document.querySelectorAll('[data-tab]').forEach(b=>b.addEventListener('click',()=>{document.querySelectorAll('[data-tab]').forEach(x=>{const active=x===b;x.setAttribute('aria-pressed',String(active));document.getElementById(x.dataset.tab).hidden=!active;});}));</script></html>"""
