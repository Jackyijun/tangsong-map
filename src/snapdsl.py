# -*- coding: utf-8 -*-
"""解析 content/snaps.txt（时间节点小语言），build.py 与 tools/snapcheck.py 共用。

每个节点继承上一节点结束时的全部归属，再按行覆盖：

  @年份 | 年号 | 标题 | 概述
  单位键[本节点显示名]{治所}>所属政权: 州府 @单位 @单位@年份
  ·: 州府 …        这些州府无主
  割据: 单位 …     本节点不受朝命的单位（加斜线）；写了这一行就整体替换上一节点的名单

  [显示名] 写空 []，表示删去此前设的显示名，恢复单位默认名称。
  @单位      取本节点开始时该单位的全部州；@单位@年份 取该年节点结束时该单位的州。
"""
import re


def parse(path, SID, UK, warn=print):
    snaps = []
    state = dict(own={}, lab={}, pol={}, seat={}, hatch=set())
    cur = None
    history = {}
    start = None

    def snapshot():
        return dict(own=dict(state["own"]), lab=dict(state["lab"]), pol=dict(state["pol"]),
                    seat=dict(state["seat"]), hatch=set(state["hatch"]))

    for raw in open(path, encoding="utf8"):
        line = raw.rstrip("\n")
        if not line.strip() or line.lstrip().startswith("#"): continue
        if line.startswith("@"):
            if cur: history[cur["y"]] = snapshot(); snaps.append(dict(cur, st=history[cur["y"]]))
            parts = [p.strip() for p in line[1:].split("|")]
            cur = dict(y=int(parts[0]), era=parts[1], t=parts[2], d=parts[3])
            assert not snaps or cur["y"] > snaps[-1]["y"], ("节点年份须递增", cur["y"])
            start = dict(own=dict(state["own"]))      # @单位 引用的是“本节点开始时”的归属
            continue
        head, _, body = line.partition(":")
        head = head.strip(); toks = body.split()
        if head == "割据":
            state["hatch"] = set(toks)
            for k in toks: assert k in UK, ("割据行里的单位不存在", k, cur["y"])
            continue
        if head == "·":
            for tk in toks:
                assert tk in SID, ("未知州府", tk, cur["y"]); state["own"][tk] = None
            continue
        m = re.match(r"^([^\[\]{}>]+)(?:\[([^\]]*)\])?(?:\{([^}]*)\})?(?:>(.+))?$", head)
        assert m, ("无法解析的行", head)
        uk, lab, seat, pol = m.group(1).strip(), m.group(2), m.group(3), m.group(4)
        assert uk in UK, ("units.py 里没有这个单位", uk, cur["y"])
        if lab is not None:
            if lab == "": state["lab"].pop(uk, None)
            else: state["lab"][uk] = lab
        if seat is not None:
            assert seat in SID, ("治所不在 seeds.txt", seat, cur["y"]); state["seat"][uk] = seat
        if pol is not None:
            assert pol.strip() in UK, ("所属政权不存在", pol, cur["y"]); state["pol"][uk] = pol.strip()
        for tk in toks:
            if tk.startswith("@"):
                ref = tk[1:]
                if "@" in ref:   # @单位@年份：取该年节点结束时该单位的州
                    rk, ry = ref.split("@"); src = history[int(ry)]["own"]
                    lst = [s for s, u in src.items() if u == rk]
                else:
                    rk = ref; lst = [s for s, u in start["own"].items() if u == rk]
                assert rk in UK, ("引用的单位不存在", rk, cur["y"])
                if not lst: warn(f"  WARN empty ref {tk} in {cur['y']}")
                for s in lst: state["own"][s] = uk
            else:
                assert tk in SID, ("未知州府", tk, cur["y"], uk); state["own"][tk] = uk
    history[cur["y"]] = snapshot()
    snaps.append(dict(cur, st=history[cur["y"]]))
    return snaps
