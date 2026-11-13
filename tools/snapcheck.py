# -*- coding: utf-8 -*-
"""检查时间节点（content/snaps.txt）解析后的归属，不必跑完整构建（一秒钟）。

  python tools/snapcheck.py                     列出每个节点：单位 → 州府
  python tools/snapcheck.py 820 851             只列这几个节点
  python tools/snapcheck.py --dump F.json       把各节点解析结果存成 JSON
  python tools/snapcheck.py --diff F.json       与存下的结果比对：两边都有的年份，归属、显示名、
                                                所属政权、治所、斜线有任何不同都列出来
                                                （补节点时用来确认原有节点没被插入的节点带偏）
"""
import json, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src")); sys.path.insert(0, str(ROOT / "content"))
import snapdsl, units as UM

def seeds():
    out = []
    for line in open(ROOT / "content" / "seeds.txt", encoding="utf8"):
        line = line.strip()
        if line and not line.startswith("#"): out.append(line.split()[0])
    return out

def resolved():
    S = seeds(); SID = {s: i for i, s in enumerate(S)}
    UK = {u["k"]: i for i, u in enumerate(UM.U)}
    snaps = snapdsl.parse(ROOT / "content" / "snaps.txt", SID, UK)
    out = {}
    for sn in snaps:
        st = sn["st"]
        present = {u for u in st["own"].values() if u}
        out[str(sn["y"])] = dict(
            own={s: st["own"].get(s) for s in S},
            lab={k: v for k, v in st["lab"].items() if k in present or k in {st["pol"].get(u) for u in present}},
            pol={u: st["pol"].get(u, UM.U[UK[u]]["pol"]) for u in sorted(present)},
            seat={k: v for k, v in st["seat"].items() if k in present},
            hatch=sorted(k for k in st["hatch"] if k in present))
    return out

def main():
    a = sys.argv[1:]
    R = resolved()
    if a[:1] == ["--dump"]:
        json.dump(R, open(a[1], "w", encoding="utf8"), ensure_ascii=False, indent=0); print("dumped", len(R)); return
    if a[:1] == ["--diff"]:
        B = json.load(open(a[1], encoding="utf8")); bad = 0
        for y in sorted(set(B) & set(R), key=int):
            for f in ("own", "lab", "pol", "seat", "hatch"):
                x, z = B[y][f], R[y][f]
                if x == z: continue
                bad += 1
                if isinstance(x, dict):
                    ks = sorted(set(x) | set(z), key=str)
                    print(y, f, "; ".join(f"{k}: {x.get(k)} → {z.get(k)}" for k in ks if x.get(k) != z.get(k)))
                else: print(y, f, x, "→", z)
        print("原有节点与基准" + ("一致" if not bad else f"有 {bad} 处不同"), "；比对年份", len(set(B) & set(R)), "；新增", sorted(set(R) - set(B), key=int))
        return
    ys = a or list(R)
    for y in ys:
        st = R[y]; by = {}
        for s, u in st["own"].items(): by.setdefault(u, []).append(s)
        print(f"@{y}  割据 {' '.join(st['hatch'])}")
        for u, ss in by.items():
            if u is None: continue
            lab = st["lab"].get(u); pol = st["pol"].get(u)
            print(f"  {u}{'[' + lab + ']' if lab else ''}{'>' + pol if pol and pol != u else ''}{'{' + st['seat'][u] + '}' if u in st['seat'] else ''}: {' '.join(ss)}")

if __name__ == "__main__":
    main()
