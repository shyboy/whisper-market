#!/usr/bin/env python3
"""Whisper Market v0.1. SQLite transactions own game facts; Codex owns narration."""
from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import sqlite3
import sys
import uuid

from story import CARDS, ENDINGS, FACTS, NAMES, SCENES

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_HOME = Path(os.environ.get("LOCALAPPDATA", str(Path.home() / ".local/share"))) / "WhisperMarket"
ACTIONS = {
    "observe": "观察／免费听传闻", "buy_tip": "向老滑头买线索（5 金币）",
    "sell_chip": "卖掉失效晶片（收入 15）", "visit": "移动：to=inn/alley/guard",
    "talk": "对当前 NPC 说话：npc、said、reply（谈话不自动成交）",
    "note": "私密笔记：text", "listen": "主动留意或回应脑内杂音", "inspect": "免费验看账本和收据",
    "acquire": "与李签约：mode=buy/consign/partner（35 买断／35 底款／对半分账）",
    "copy": "制作匿名摘录", "backup": "请老滑头保管真实摘录",
    "shelter": "以匿名摘录交换李的藏身安排", "public_permission": "请李同意公开",
    "meet_iron": "请老滑头安排铁手来客栈", "return": "归还原件（总赏金 50）",
    "sell": "卖工团（总价 200）", "extort": "向队长要求封口费：amount=1..500",
    "publish": "在客栈公开匿名摘录（无赏金）", "destroy": "烧毁自己买断的原件",
    "leave": "退出本章并结清托管关系", "wait": "等待一个场景时段",
    "epilogue": "回客栈读后果回响与尾声",
}
PARAMS = {"visit": {"to"}, "talk": {"npc", "said", "reply"}, "note": {"text"},
          "acquire": {"mode"}, "extort": {"amount"}, "restore": {"checkpoint"}}


class RuleError(Exception):
    pass


def need(condition, message):
    if not condition:
        raise RuleError(message)


def encoded(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def initial():
    return {
        "schema": 1, "scene": "inn", "tick": 0, "coins": 20, "energy": 0,
        "ledger_owner": "li", "ledger_holder": "li", "contract": None,
        "chip": True, "extract": False, "flags": [], "clues": {}, "notes": [],
        "knowledge": {n: [] for n in NAMES}, "conversations": {n: [] for n in NAMES},
        "reputation": {"guard": 0, "guild": 0}, "li_paid": 0, "heat": 0,
        "promises": [], "pending": [], "ending": None, "epilogue": False,
        "journal": ["你猛地回过神，发现自己坐在一间陌生客栈里。衣袋沉甸甸的，窗外的雨泛着异样的微光。一阵短促的杂音掠过脑海，随即消失。"],
    }


def present(s, npc):
    return npc in ({"inn": ["lao"] + (["iron"] if "iron_here" in s["flags"] else []),
                    "alley": ["li"], "guard": ["captain"]}[s["scene"]])


def learn(s, npc, text):
    if text not in s["knowledge"][npc]:
        s["knowledge"][npc].append(text)


def flag(s, name):
    need(name not in s["flags"], "这件事已经完成，没有新变化，也不会再次扣款或发奖。")
    s["flags"].append(name)


def clue(s, name):
    s["clues"][name] = FACTS[name]
    return FACTS[name]


def location(s, scene):
    need(s["scene"] == scene, f"请先到{SCENES[scene]['name']}。")


def ledger_access(s):
    return s["ledger_holder"] == "player" or (s["ledger_holder"] == "li" and s["scene"] == "alley")


def deliverable(s):
    need(s["ledger_holder"] == "player", "你没有携带原件。声称持有、摘录和原件不是同一件事。")
    need(s["contract"] is not None, "尚未取得处置权。")
    need("verified" in s["clues"], "请先免费检查原件及夹页收据。")


def settle(s, total, recipient):
    due = {"buy": 0, "consign": 35, "partner": (total + 1) // 2}[s["contract"]]
    need(total >= due, f"成交价不能覆盖已约定的 {due} 金币分账。")
    s["coins"] += total - due
    s["li_paid"] += due
    if due:
        learn(s, "li", f"买家通过约定交割人直接向你支付 {due} 金币，你的分账已结清。")
    s["ledger_owner"] = s["ledger_holder"] = recipient
    s["promises"] = [p for p in s["promises"] if not p.startswith("交割时")]
    return f"总价 {total}；买家直接付瘸腿李 {due}；你收到 {total - due} 金币。原件交给{NAMES[recipient]}。"


def ending(s, name):
    s["ending"] = name
    return ENDINGS[name]["text"] + " 本章主要选择已结算；回客栈可读尾声。"


def spread(s):
    remaining, messages = [], []
    for p in s["pending"]:
        if p["due"] > s["tick"]:
            remaining.append(p)
        else:
            learn(s, p["npc"], p["text"])
            s["reputation"][p["faction"]] += p["delta"]
            messages.append("消息传开：" + p["text"])
    s["pending"] = remaining
    return messages


def apply(s, action, a):
    need(action in ACTIONS, "未知行动。请用 help 查看支持的行动；自由表达可以通过 talk 协商。")
    if s["ending"]:
        need(action in {"visit", "epilogue", "note", "wait", "talk"}, "本章主要选择已经结算。请读尾声、恢复检查点或另开一局。")
        if action == "visit":
            need(a.get("to") == "inn", "本章已经收束，只能返回客栈读尾声。")
    timed = action not in {"talk", "note", "listen"}
    event = ""
    if action == "observe":
        if s["scene"] == "inn":
            flag(s, "heard_rumor")
            event = clue(s, "rumor")
        elif s["scene"] == "alley":
            flag(s, "seen_ledger")
            event = clue(s, "ledger")
        else:
            flag(s, "seen_guard")
            event = "接待厅告示写着：失物有赏，账本原件五十金币；须当面核验。"
    elif action in {"buy_tip", "sell_chip"}:
        location(s, "inn")
        if action == "buy_tip":
            need(s["coins"] >= 5, "金币不足。你仍可免费观察客栈，听到接头线索。")
            flag(s, "paid_tip")
            s["coins"] -= 5
            event = clue(s, "tip")
            learn(s, "lao", "你向玩家收五金币，提供了瘸腿李在后巷断灯下的线索。")
        else:
            need(s["chip"], "失效晶片已不在你身上，不能重复出售。")
            s["chip"] = False
            s["coins"] += 15
            event = "老滑头检查后收下失效晶片，付给你十五金币。它只是旧材料，没有隐藏的首章必需用途。"
            learn(s, "lao", event)
    elif action == "visit":
        to = a.get("to")
        need(to in SCENES, "第一章可到客栈、接头巷道或卫队接待厅。")
        need(to != s["scene"], "你已经在这里，位置没有变化。")
        need(to == "inn" or {"rumor", "tip"} & s["clues"].keys(), "先在客栈观察或打听，取得接头线索。")
        s["scene"] = to
        event = SCENES[to]["text"]
    elif action == "talk":
        npc, said, reply = a.get("npc"), a.get("said", "").strip(), a.get("reply", "").strip()
        need(npc in NAMES and present(s, npc), "对方不在当前场景。私密笔记应使用 note。")
        need(0 < len(said) <= 2000 and len(reply) <= 2000, "谈话须为 1 至 2000 字，回复不超过 2000 字。")
        entry = {"player_claim": said, "npc_speech": reply}
        need(not s["conversations"][npc] or s["conversations"][npc][-1] != entry, "相同谈话已记下，不会重复推进。")
        s["conversations"][npc].append(entry)
        event = f"与{NAMES[npc]}交谈已记下。谈话中的声称和意向不改变物品、金币或客观事实。"
    elif action == "listen":
        flag(s, "inner_voice_contact")
        event = "你把注意力转向那阵杂音。断续的声音再次浮现：‘……连接……中断……’它很快沉寂。吧台后的人仍低头擦拭手里的东西，没有抬头。你还无法判断声音的来处。"
    elif action == "note":
        value = a.get("text", "").strip()
        need(0 < len(value) <= 2000, "笔记须为 1 至 2000 字。")
        need(value not in s["notes"], "相同私密笔记已存在。")
        s["notes"].append(value)
        event = "你在心里记下这件事，没有说出口。"
        if "inner_voice_contact" in s["flags"]:
            event += " 那个断续的声音忽然回应：‘……已记录。’随后又没了声息。"
    elif action == "inspect":
        need(ledger_access(s), "需要携带原件，或到巷道当面请瘸腿李出示。")
        flag(s, "inspected")
        event = clue(s, "verified")
        if s["scene"] == "alley":
            learn(s, "li", "玩家当面核验了第七页与夹页收据。")
    elif action == "acquire":
        location(s, "alley")
        need(s["ledger_holder"] == "li" and s["contract"] is None, "原件已签约或不在李手上，不能重复取得。")
        mode = a.get("mode")
        need(mode in {"buy", "consign", "partner"}, "可买断、寄售或对半分账。")
        if mode == "buy":
            need(s["coins"] >= 35, "买断需三十五金币。可卖失效晶片补款，或改用无需本金的寄售／合伙。")
            s["coins"] -= 35
            s["li_paid"] += 35
            s["ledger_owner"] = "player"
            terms = "三十五金币买断，李当面点清钱。"
        else:
            terms = "交割时买家直接给李三十五金币底款" if mode == "consign" else "交割时买家直接分给李总价的一半（奇数向上取整）"
            s["promises"].append(terms)
        s["contract"] = mode
        s["ledger_holder"] = "player"
        event = terms + " 李让你带走原件。托管期间不得私毁或擅自公开；实际买家按约分账。"
        if mode == "buy":
            event = terms + " 原件所有权与处置权归你。"
        learn(s, "li", event)
    elif action == "copy":
        need(ledger_access(s), "没有原件可抄；空口声称复制不能生成物品。")
        need("verified" in s["clues"], "先核验第七页及收据。")
        flag(s, "made_copy")
        s["extract"] = True
        event = clue(s, "copy")
    elif action in {"backup", "shelter", "meet_iron"}:
        location(s, "inn")
        need("verified" in s["clues"], "先核实账本内容，老滑头才肯用渠道担保。")
        if action == "meet_iron":
            flag(s, "iron_here")
            event = "老滑头带来口信，铁手在下一个时段抵达客栈侧桌。他只听说你有可核验的账本，尚未知道内容。现在可以与他会面。"
            learn(s, "lao", "你替玩家约了工团主管在客栈会面。")
            learn(s, "iron", "老滑头口信：玩家想谈一份可核验的卫队账本。内容尚未提供。")
        else:
            need(s["extract"] or "backup" in s["flags"], "需要实际制作的匿名摘录。")
            flag(s, action)
            if action == "backup":
                s["extract"] = False
            event = clue(s, action)
            learn(s, "lao", event + " 你看到第七页的检修费差额及收据编号。")
            if action == "shelter":
                if "backup" not in s["flags"]:
                    s["flags"].append("backup")
                    s["extract"] = False
                    clue(s, "backup")
                    event += " 摘录实际留在老滑头手中，作为可宣读的外存备份。"
                s["promises"].append("允许老滑头保留匿名摘录，换取李在客栈一夜的庇护。")
    elif action == "public_permission":
        location(s, "alley")
        need("shelter" in s["flags"], "李要的是已经落实的藏身安排；先去客栈用匿名摘录换庇护。")
        need(s["contract"] in {"consign", "partner"}, "这项补充许可适用于托管原件；买断原件由你决定。")
        flag(s, "public_permission")
        event = clue(s, "public_permission")
        learn(s, "li", event)
    elif action in {"return", "sell", "extort"}:
        location(s, "inn" if action == "sell" else "guard")
        deliverable(s)
        if action == "sell":
            need("iron_here" in s["flags"], "铁手还没来。请先安排会面。")
            event = settle(s, 200, "iron")
            s["reputation"]["guild"] += 20
            learn(s, "iron", "你核验原件并买下账本，知道了第七队长收取差额的条目。")
            learn(s, "lao", "你看见玩家与铁手在侧桌完成原件交易，但没有听清全部价款。")
            s["pending"].append({"due": s["tick"] + 3, "npc": "captain", "faction": "guard", "delta": -25,
                                 "text": "工团交割员向第七队发出附收据编号的核账通知，队长由此得知账本已流入工团。"})
            event += " " + ending(s, "sold")
        elif action == "return":
            event = settle(s, 50, "captain")
            s["reputation"]["guard"] += 15
            learn(s, "captain", "玩家归还了你当面核验的原件，你支付五十金币赏金并出具收条。")
            s["pending"].append({"due": s["tick"] + 3, "npc": "iron", "faction": "guild", "delta": -5,
                                 "text": "卫队张贴失物领回告示，工团联络员据此得知原件已经回到队长手上。"})
            event += " " + ending(s, "returned")
        else:
            try:
                amount = int(a.get("amount", "500"))
            except (ValueError, TypeError):
                raise RuleError("封口费须为整数。")
            need(1 <= amount <= 500, "本次可要求 1 至 500 金币；不能把一句加价变成已到账。")
            if "backup" not in s["flags"]:
                flag(s, "empty_threat")
                s["heat"] += 1
                learn(s, "captain", "玩家威胁公开，但没能出示可信的外存备份交付凭据；你拒绝付封口费。")
                event = "队长敲了敲桌子：‘副本在哪，谁会送出去？’你的空口威胁未换来金币，他提高戒心。原件仍在你手上，可归还、找工团或补足筹码。"
            else:
                event = settle(s, amount, "captain")
                s["heat"] += 2
                s["reputation"]["guard"] -= 30
                s["promises"].append("已收封口费，承诺暂缓公开；老滑头保管的备份仍在。")
                learn(s, "captain", "你看过原件与外存凭据，付封口费换回原件；知道客栈有备份，尚未公开。")
                event += " " + ending(s, "extorted")
    elif action == "publish":
        location(s, "inn")
        deliverable(s)
        need(s["extract"] or "backup" in s["flags"], "先制作匿名摘录，不能把原件持有权当成已经向公众传播。")
        need(s["contract"] == "buy" or "public_permission" in s["flags"], "李尚未同意公开托管账本。先落实藏身安排，再回巷道取得许可。")
        s["ledger_owner"] = s["ledger_holder"] = "public"
        s["promises"] = [p for p in s["promises"] if not p.startswith("交割时")]
        for npc in NAMES:
            if present(s, npc):
                learn(s, npc, "你亲耳听到客栈公开宣读第七页差额和收据编号，来源已隐去。")
        s["pending"].extend([
            {"due": s["tick"] + 2, "npc": "captain", "faction": "guard", "delta": -25, "text": "卫队耳目把客栈宣读的条目和收据编号送到队长桌上。"},
            {"due": s["tick"] + 2, "npc": "iron", "faction": "guild", "delta": 10, "text": "听众把公开摘录抄给工团联络员，铁手收到可复核的编号。"},
        ])
        event = "老滑头主持匿名宣读，并把原件封存供听众当面核对。没有支付金币。 " + ending(s, "published")
    elif action == "destroy":
        location(s, "inn")
        need(s["ledger_holder"] == "player" and s["ledger_owner"] == "player", "只能处置自己买断并实际携带的原件，不能烧掉托管物。")
        s["ledger_owner"] = s["ledger_holder"] = "destroyed"
        learn(s, "lao", "你亲眼看见玩家烧毁蓝线缝脊的账本原件。")
        event = ending(s, "destroyed")
    elif action == "leave":
        if s["ledger_holder"] == "player" and s["ledger_owner"] == "li":
            s["ledger_holder"] = "li"
            learn(s, "li", "玩家按托管条款由客栈交割人退回原件，未成交，无分账。")
            s["promises"] = [p for p in s["promises"] if not p.startswith("交割时")]
        event = ending(s, "left")
    elif action == "wait":
        event = "晶雨又敲过一阵。一个场景时段过去了。"
    elif action == "epilogue":
        location(s, "inn")
        need(s["ending"], "账本去向尚未决定；你也可以明确退出本章。")
        need(not s["epilogue"], "尾声已记录，可在状态面板重读，不会再次推进。")
        s["tick"] += 2
        s["epilogue"] = True
        event = "老滑头推来一杯温水：‘货可以转手，话可不好收回。’桌脚下，一枚无人碰过的旧罗盘轻轻偏向城外。第一章完。下一章尚未开放；你的账目、承诺和后果留在本地。"
    if timed:
        s["tick"] += 1
    events = [event] + spread(s)
    s["journal"].extend(events)
    return "\n".join(events)


def public(s, slot, revision):
    items = (["失效晶片"] if s["chip"] else []) + (["账本匿名摘录"] if s["extract"] else [])
    if s["ledger_holder"] == "player":
        items.append("账本原件（买断）" if s["ledger_owner"] == "player" else "账本原件（托管）")
    result = {k: copy.deepcopy(s[k]) for k in ("tick", "coins", "energy", "clues", "notes", "reputation", "promises", "heat", "ending", "epilogue", "li_paid")}
    result.update(slot=slot, revision=revision, scene=SCENES[s["scene"]], items=items,
                  inner_voice="heard_fragment" if "inner_voice_contact" in s["flags"] else "unidentified",
                  nearby=[{"id": n, "name": NAMES[n]} for n in NAMES if present(s, n)],
                  recent=s["journal"][-6:], backup="老滑头代存" if "backup" in s["flags"] else "无",
                  ending_detail=ENDINGS.get(s["ending"]))
    return result


class Game:
    def __init__(self, home=DEFAULT_HOME):
        self.home = Path(home).expanduser().resolve()
        self.home.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(self.home / "saves.sqlite3", timeout=15)
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS runs(slot TEXT PRIMARY KEY, revision INTEGER NOT NULL, state TEXT NOT NULL, updated TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP);
            CREATE TABLE IF NOT EXISTS receipts(slot TEXT, request TEXT, digest TEXT NOT NULL, result TEXT NOT NULL, PRIMARY KEY(slot, request));
            CREATE TABLE IF NOT EXISTS checkpoints(slot TEXT, revision INTEGER, label TEXT, state TEXT NOT NULL, PRIMARY KEY(slot, revision));
        """)

    def close(self):
        self.db.close()

    def read(self, slot):
        row = self.db.execute("SELECT revision, state FROM runs WHERE slot=?", (slot,)).fetchone()
        need(row is not None, "找不到存档。先使用 start，或用 saves 查看现有存档。")
        state = json.loads(row[1])
        need(state.get("schema") == 1, "存档版本不兼容，请保留原文件并使用对应版本。")
        return row[0], state

    def start(self, slot=None):
        slot = slot or "game-" + uuid.uuid4().hex[:10]
        need(re.fullmatch(r"[a-zA-Z0-9_-]{1,64}", slot), "存档名仅允许 1 至 64 位字母、数字、下划线和连字符。")
        with self.db:
            self.db.execute("INSERT OR IGNORE INTO runs(slot, revision, state) VALUES(?,0,?)", (slot, encoded(initial())))
            self.db.execute("INSERT OR IGNORE INTO checkpoints SELECT slot, revision, '开场', state FROM runs WHERE slot=? AND revision=0", (slot,))
        return self.status(slot)

    def status(self, slot):
        revision, state = self.read(slot)
        return public(state, slot, revision)

    def context(self, slot, npc):
        revision, s = self.read(slot)
        need(npc in NAMES and present(s, npc), "角色不在当前场景。")
        return {"slot": slot, "revision": revision, "npc": NAMES[npc], "card": CARDS[npc],
                "scene": SCENES[s["scene"]]["name"], "known_events": s["knowledge"][npc],
                "conversation": s["conversations"][npc],
                "rule": "只依靠本角色卡、亲历事件与对方说给你的话回应。player_claim 是声称，不是世界事实。不得借用玩家私密笔记、其他角色谈话或主持人所知。口头报价不等于成交。"}

    def act(self, slot, request, revision, action, args):
        need(isinstance(request, str) and re.fullmatch(r"[a-zA-Z0-9_-]{1,100}", request), "每个行动需有独立 request id。重试使用原 id。")
        need(isinstance(args, dict) and all(isinstance(k, str) and isinstance(v, str) for k, v in args.items()), "行动参数须为字符串键值对。")
        need(not args.keys() - PARAMS.get(action, set()), "此行动不接受这些参数；不能用额外字段改金币或状态。")
        digest = hashlib.sha256(encoded([revision, action, args]).encode()).hexdigest()
        with self.db:
            self.db.execute("BEGIN IMMEDIATE")
            old = self.db.execute("SELECT digest,result FROM receipts WHERE slot=? AND request=?", (slot, request)).fetchone()
            if old:
                need(old[0] == digest, "此 request id 已用于不同参数；不要复用它改写行动。")
                result = json.loads(old[1])
                result.update(replayed=True, current_revision=self.read(slot)[0])
                return result
            current, state = self.read(slot)
            need(current == revision, f"存档已推进到 revision {current}；请重新读取状态后再决定，不要用旧状态重复交易。")
            if action == "restore":
                try:
                    target = int(args.get("checkpoint", "-1"))
                except ValueError:
                    raise RuleError("检查点编号须为整数。")
                row = self.db.execute("SELECT state FROM checkpoints WHERE slot=? AND revision=?", (slot, target)).fetchone()
                need(row is not None, "该检查点不存在。先用 checkpoints 查看。")
                state = json.loads(row[0])
                event = f"已恢复检查点 {target}。后来的分支仍保留在交易回执中；这是明确回溯，新行动使用新的 request id。"
                state["journal"].append(event)
            else:
                event = apply(state, action, args)
            need(state["coins"] >= 0 and state["energy"] >= 0, "资源结算异常，整次行动未提交。")
            current += 1
            self.db.execute("UPDATE runs SET revision=?, state=?, updated=CURRENT_TIMESTAMP WHERE slot=?", (current, encoded(state), slot))
            result = {"ok": True, "replayed": False, "event": event, "view": public(state, slot, current)}
            self.db.execute("INSERT INTO receipts VALUES(?,?,?,?)", (slot, request, digest, encoded(result)))
            if action not in {"talk", "note", "wait", "observe", "visit"}:
                self.db.execute("INSERT INTO checkpoints VALUES(?,?,?,?)", (slot, current, ACTIONS.get(action, "恢复检查点"), encoded(state)))
            return result

    def saves(self):
        return [{"slot": x[0], "revision": x[1], "updated": x[2], "ending": json.loads(x[3])["ending"]}
                for x in self.db.execute("SELECT slot,revision,updated,state FROM runs ORDER BY updated DESC, rowid DESC")]

    def checkpoints(self, slot):
        self.read(slot)
        return [{"revision": r, "label": l} for r, l in self.db.execute("SELECT revision,label FROM checkpoints WHERE slot=? ORDER BY revision", (slot,))]


def main():
    parser = argparse.ArgumentParser(description="窃语黑市 · 第一章。由 Codex 操作的本地规则与存档工具。")
    parser.add_argument("--home", type=Path, default=DEFAULT_HOME)
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("help")
    sub.add_parser("saves")
    sub.add_parser("start").add_argument("--slot")
    for command in ("status", "context", "act", "checkpoints", "panel"):
        p = sub.add_parser(command)
        p.add_argument("--slot", required=True)
        if command == "context":
            p.add_argument("--npc", required=True, choices=list(NAMES))
        if command == "act":
            p.add_argument("--id", required=True)
            p.add_argument("--revision", required=True, type=int)
            p.add_argument("--action", required=True)
            p.add_argument("--arg", action="append", default=[], metavar="KEY=VALUE")
            p.add_argument("--args-file", type=Path)
    options = parser.parse_args()
    game = None
    try:
        if options.command == "help":
            output = {"actions": ACTIONS, "home": str(options.home), "version": "0.1.0", "resource_rule": "基础系统帮助免费；游戏金币为虚构资源。"}
        else:
            game = Game(options.home)
            cmd = options.command
            if cmd == "start":
                output = game.start(options.slot)
            elif cmd == "saves":
                output = game.saves()
            elif cmd == "status":
                output = game.status(options.slot)
            elif cmd == "context":
                output = game.context(options.slot, options.npc)
            elif cmd == "checkpoints":
                output = game.checkpoints(options.slot)
            elif cmd == "act":
                args = json.loads(options.args_file.read_text(encoding="utf-8-sig")) if options.args_file else {}
                need(isinstance(args, dict), "参数文件须为 JSON 对象。")
                for item in options.arg:
                    need("=" in item, "--arg 使用 KEY=VALUE 格式。")
                    k, v = item.split("=", 1)
                    args[k] = v
                output = game.act(options.slot, options.id, options.revision, options.action, args)
            else:
                from panel import render
                output = {"panel": str(render(game, options.slot))}
            if cmd in {"start", "act"}:
                try:
                    from panel import render
                    slot = output.get("slot") or output["view"]["slot"]
                    output["panel"] = str(render(game, slot))
                except (OSError, ImportError) as error:
                    output["panel_warning"] = "存档已保存，但面板生成失败：" + str(error)
        print(json.dumps(output, ensure_ascii=False, indent=2))
    except (RuleError, sqlite3.Error, OSError, json.JSONDecodeError) as error:
        print(json.dumps({"ok": False, "error": str(error), "hint": "未确认的结算请用同一 request id 重试或读取 status；不要直接修改存档。"}, ensure_ascii=False))
        return 2
    finally:
        if game:
            game.close()
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
