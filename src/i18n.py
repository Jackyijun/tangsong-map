# -*- coding: utf-8 -*-
"""英文版：把 content/en/ 下的译文并入构建结果，并检查缺译与过期。

中文是源文本。每一条要显示的中文都有一个“键/字段”，英文按同样的键写在 content/en/*.json 里：

  units.json    政权、藩镇、部族         {"魏博": {"n": 全称, "s": 地图短名（可省）, "note": 说明}}
  labels.json   节点里的当年别名         {"魏博（罗弘信）": "Weibo (Luo Hongxin)"}
  seeds.json    州府城邑                 {"汴州": {"mod": 今地, "n": {"汴州": …, "开封府": …}}}
  items.json    条目（键为 类别:古名）    {"battle:高梁河之战": {"old", "mod", "note", "yt", "sides", "cmd", "g": {分区名: …}, "p": {路线地名: …}}}
                同名条目（如两次太原之战）在键后加 @年份 或 @今名 区分：battle:太原之战@757
  snaps.json    时间节点（键为年份）      {"979": {"era": 年号, "t": 标题, "d": 说明}}
  misc.json     今省名                   {"prov": {"河南": …}}

zh.lock.json 记着每条英文写成时对应中文的指纹。中文改了而英文没改，就是“过期”。
改完英文后运行 `python tools/i18n.py lock` 更新指纹。
"""
import hashlib, json
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
EN = ROOT / "content" / "en"
FILES = ["units", "labels", "seeds", "items", "snaps", "misc"]
LOCK = EN / "zh.lock.json"
ITEM_FIELDS = ("old", "mod", "note", "yt", "sides", "cmd")


def fp(zh):
    return hashlib.sha1(zh.encode("utf8")).hexdigest()[:10]


def load_en():
    out = {}
    for f in FILES:
        p = EN / f"{f}.json"
        out[f] = json.load(open(p, encoding="utf8")) if p.exists() else {}
    return out


def load_lock():
    return json.load(open(LOCK, encoding="utf8")) if LOCK.exists() else {}


def _disc(it):
    """同名条目的区分标记：年份优先，其次今名。"""
    if it.get("y") is not None: return str(it["y"])
    if it.get("yrs"): return str(it["yrs"][0][0])
    if it.get("y0") is not None: return str(it["y0"])
    return it.get("mod") or str(it["i"])


def item_keys(data):
    """每个条目的英文键，按 data["items"] 的顺序。"""
    base = [f"{it['c']}:{it['old']}" for it in data["items"]]
    dup = {k for k, n in Counter(base).items() if n > 1}
    keys = [k + "@" + _disc(it) if k in dup else k for k, it in zip(base, data["items"])]
    assert len(set(keys)) == len(keys), "条目英文键重复：" + ", ".join(k for k, n in Counter(keys).items() if n > 1)
    return keys


def required(geo, data):
    """列出全部需要英文的 (文件, 路径, 中文)。路径是键名组成的元组。"""
    req = []
    for u in data["units"]:
        req.append(("units", (u["k"], "n"), u["n"]))
        if u.get("note"): req.append(("units", (u["k"], "note"), u["note"]))
    labs = sorted({v for s in geo["snaps"] for v in s["lab"].values()})
    for v in labs: req.append(("labels", (v,), v))
    for s in data["seeds"]:
        if s["t"] == "r": continue
        if s.get("mod"): req.append(("seeds", (s["id"], "mod"), s["mod"]))
        names = [s["n"]] + [n for _, n in (s.get("nm") or [])]
        for n in dict.fromkeys(names): req.append(("seeds", (s["id"], "n", n), n))
    keys = item_keys(data)
    for k, it in zip(keys, data["items"]):
        for f in ITEM_FIELDS:
            if it.get(f): req.append(("items", (k, f), it[f]))
    for R in geo.get("regions", []):
        k = keys[R["it"]]
        for g in R["groups"]: req.append(("items", (k, "g", g["n"]), g["n"]))
    for R in geo.get("routes", []):
        k = keys[R["it"]]
        for p in dict.fromkeys(p[3] for p in R["pts"]): req.append(("items", (k, "p", p), p))
    for s in geo["snaps"]:
        y = str(s["y"])
        for f in ("era", "t", "d"):
            if s.get(f): req.append(("snaps", (y, f), s[f]))
    for p in geo.get("prov", []): req.append(("misc", ("prov", p["n"]), p["n"]))
    return req


def get(en, f, path):
    v = en.get(f, {})
    for k in path:
        if not isinstance(v, dict) or k not in v: return None
        v = v[k]
    return v if isinstance(v, str) and v.strip() else None


def lock_key(f, path):
    return f + "/" + "/".join(path)


def check(geo, data, en=None, lock=None):
    en = en if en is not None else load_en()
    lock = lock if lock is not None else load_lock()
    missing, stale, unlocked = [], [], []
    for f, path, zh in required(geo, data):
        if get(en, f, path) is None: missing.append((f, path, zh)); continue
        lk = lock.get(lock_key(f, path))
        if lk is None: unlocked.append((f, path, zh))
        elif lk != fp(zh): stale.append((f, path, zh))
    return missing, stale, unlocked


def attach(geo, data, en=None):
    """把英文写进 geo/data（缺译时退回中文），返回 (geo, data)。"""
    en = en if en is not None else load_en()
    g = lambda f, *path: get(en, f, path)
    for u in data["units"]:
        u["ne"] = g("units", u["k"], "n") or u["n"]
        s = g("units", u["k"], "s")
        if s: u["se"] = s
        u["notee"] = g("units", u["k"], "note") or u.get("note", "")
    for s in data["seeds"]:
        if s["t"] == "r": continue
        s["ne"] = g("seeds", s["id"], "n", s["n"]) or s["n"]
        if s.get("nm"): s["nme"] = [g("seeds", s["id"], "n", n) or n for _, n in s["nm"]]
        s["mode"] = g("seeds", s["id"], "mod") or s.get("mod", "")
    keys = item_keys(data)
    for k, it in zip(keys, data["items"]):
        it["e"] = {f: (g("items", k, f) or it[f]) for f in ITEM_FIELDS if it.get(f)}
    for R in geo.get("regions", []):
        k = keys[R["it"]]
        for gr in R["groups"]: gr["ne"] = g("items", k, "g", gr["n"]) or gr["n"]
    for R in geo.get("routes", []):
        k = keys[R["it"]]
        R["pe"] = [g("items", k, "p", p[3]) or p[3] for p in R["pts"]]
    for s in geo["snaps"]:
        y = str(s["y"])
        s["erae"] = g("snaps", y, "era") or s.get("era", "")
        s["te"] = g("snaps", y, "t") or s["t"]
        s["de"] = g("snaps", y, "d") or s.get("d", "")
        s["labe"] = {u: (g("labels", v) or v) for u, v in s["lab"].items()}
    for p in geo.get("prov", []): p["ne"] = g("misc", "prov", p["n"]) or p["n"]
    return geo, data
