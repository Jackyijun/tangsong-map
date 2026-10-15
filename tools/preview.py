# -*- coding: utf-8 -*-
"""用 matplotlib 快速画出若干时间节点的藩镇疆域，检查归属有没有填错。

  python tools/preview.py 755,820                         全图
  python tools/preview.py 895,907 100,125,20,42           指定范围：经度min,max,纬度min,max
  python tools/preview.py 895,907 100,125,20,42 out.png   指定输出文件
粗黑线是“多藩镇政权”的外轮廓（如唐）。
"""
import json, sys
from pathlib import Path
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import PathPatch
from matplotlib.path import Path as MPath
from matplotlib import font_manager

ROOT = Path(__file__).resolve().parent.parent
FONTS = ["/System/Library/Fonts/PingFang.ttc", "/System/Library/Fonts/STHeiti Medium.ttc",
         "C:/Windows/Fonts/msyh.ttc", "C:/Windows/Fonts/simhei.ttf",
         "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc", "/usr/share/fonts/noto-cjk/NotoSansCJK-Regular.ttc"]
fp = next((font_manager.FontProperties(fname=f) for f in FONTS if Path(f).exists()), None)

G = json.load(open(ROOT / "build" / "geo.json", encoding="utf8"))
D = json.load(open(ROOT / "build" / "data.json", encoding="utf8"))
U = D["units"]
def dec(f):
    x = y = 0; out = []
    for i in range(0, len(f), 2): x += f[i]; y += f[i + 1]; out.append((x / 100, y / 100))
    return out
def patch(rings, **kw):
    verts, codes = [], []
    for r in rings:
        pts = dec(r); verts += pts + [pts[0]]; codes += [MPath.MOVETO] + [MPath.LINETO] * (len(pts) - 1) + [MPath.CLOSEPOLY]
    return PathPatch(MPath(verts, codes), **kw)

ys = [int(a) for a in sys.argv[1].split(",")] if len(sys.argv) > 1 else [755, 820, 907, 979]
bbox = [float(a) for a in sys.argv[2].split(",")] if len(sys.argv) > 2 else G["ext"]
out = sys.argv[3] if len(sys.argv) > 3 else str(ROOT / "build" / "preview.png")
n = len(ys); cols = 2 if n > 1 else 1; rows = (n + cols - 1) // cols
fig, axs = plt.subplots(rows, cols, figsize=(11 * cols, 8 * rows), squeeze=False)
axs = axs.ravel()
for ax in axs[n:]: ax.axis("off")
for ax, y in zip(axs, ys):
    sn = next(s for s in G["snaps"] if s["y"] == y)
    for poly in G["land"]:
        pts = dec(poly[0]); ax.fill([p[0] for p in pts], [p[1] for p in pts], color="#eee", zorder=0)
    for k, rings in sn["z"].items():
        ax.add_patch(patch(rings, facecolor=U[int(k)]["cl"], edgecolor="#555", lw=0.4, alpha=0.85, zorder=1))
    for k, rings in sn["p"].items():
        ax.add_patch(patch(rings, facecolor="none", edgecolor="#000", lw=1.4, zorder=2))
    for k, (lo, la, a, r) in sn["lz"].items():
        if not (bbox[0] < lo < bbox[1] and bbox[2] < la < bbox[3]): continue
        ax.text(lo, la, sn["lab"].get(k, U[int(k)]["n"]), fontproperties=fp, fontsize=7 if a < 20 else 9, ha="center", va="center", zorder=3)
    ax.set_xlim(bbox[0], bbox[1]); ax.set_ylim(bbox[2], bbox[3]); ax.set_aspect(1.2)
    ax.set_title(f"{y} {sn['t']}", fontproperties=fp)
plt.tight_layout(); plt.savefig(out, dpi=70)
print("wrote", out)
