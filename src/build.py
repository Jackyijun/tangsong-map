# -*- coding: utf-8 -*-
"""唐宋之际形势图 · 数据构建。

读 content/ 的史料与 geodata/ 的底图，算出每个时间节点的疆域多边形，
写出 build/geo.json（几何）和 build/data.json（条目与说明）。

流程：
  1. 读州府种子（seeds.txt）
  2. 解析时间节点 DSL（snaps.txt），得到每个节点“州 → 藩镇 → 政权”的归属
  3. 把海陆栅格化
  4. 建通行代价栅格：山脉、大河处代价高
  5. 以全部州府为源点做多源最短路（Dijkstra），每个格子归最近的州
     ——这是一种“加权 Voronoi”，边界会自然沿山脊和河道走
  6. 每个节点按归属给格子上色，平滑后描出等值线，得到藩镇、政权多边形
  7. 给相邻单位挑低饱和、互相区分的颜色
  8. 整理底图（海岸、河湖、运河、山脉、荒漠）与点要素
"""
import json, re, sys, math
import numpy as np
from scipy import ndimage
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import dijkstra
from skimage import measure, draw
from shapely.geometry import shape, box, LineString, Polygon
from shapely.ops import unary_union

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
import config as C
sys.path.insert(0, str(C.CONTENT))
import units as UM
import items as IM

LON0, LON1, LAT0, LAT1 = C.EXTENT
RES = C.RES
NX = int(round((LON1 - LON0) / RES)); NY = int(round((LAT1 - LAT0) / RES))
lons = LON0 + np.arange(NX) * RES
lats = LAT0 + np.arange(NY) * RES
BB = box(LON0 - 1, LAT0 - 1, LON1 + 1, LAT1 + 1)

def to_rc(lon, lat): return (lat - LAT0) / RES, (lon - LON0) / RES

def enc_ring(coords):
    """坐标 ×100 取整后差分编码，大幅缩小 JSON 体积；前端 decode() 还原。"""
    out = []; px = py = 0
    for i, (x, y) in enumerate(coords):
        X, Y = int(round(x * 100)), int(round(y * 100))
        if i == 0: out += [X, Y]
        else:
            if X == px and Y == py: continue
            out += [X - px, Y - py]
        px, py = X, Y
    return out

def polys_of(g):
    if g.is_empty: return []
    if g.geom_type == "Polygon": return [g]
    if g.geom_type == "MultiPolygon": return list(g.geoms)
    if g.geom_type == "GeometryCollection": return [p for x in g.geoms for p in polys_of(x)]
    return []
def lines_of(g):
    if g.is_empty: return []
    if g.geom_type == "LineString": return [g]
    if g.geom_type == "MultiLineString": return list(g.geoms)
    if g.geom_type == "GeometryCollection": return [p for x in g.geoms for p in lines_of(x)]
    return []
def ne(name): return json.load(open(C.NE_DIR / f"{name}.geojson", encoding="utf8"))

# ======================================================================
# 1. 种子（州府、城邑、区域辅助点）
# ======================================================================
SEEDS = []
for line in open(C.CONTENT / "seeds.txt", encoding="utf8"):
    line = line.strip()
    if not line or line.startswith("#"): continue
    t = line.split()
    sid, lo, la, mod = t[0], float(t[1]), float(t[2]), t[3]
    typ, names = "z", None
    for x in t[4:]:
        if x in ("c", "r", "z"): typ = x
        elif x.startswith("N="):
            names = []
            for part in x[2:].split(","):
                y, n = part.split(":", 1); names.append([int(y), n])
    disp = sid.split("·")[0]   # “新州·岭南” 显示为 “新州”
    SEEDS.append(dict(id=sid, n=disp, lon=lo, lat=la, mod=mod, t=typ, names=names))
SID = {s["id"]: i for i, s in enumerate(SEEDS)}
assert len(SID) == len(SEEDS), "seeds.txt 中有重复的 ID"
print("seeds", len(SEEDS))

# ======================================================================
# 2. 单位与时间节点（解析 snaps.txt）
# ======================================================================
UNITS = UM.U
UK = {u["k"]: i for i, u in enumerate(UNITS)}
assert len(UK) == len(UNITS), "units.py 中有重复的键"

import snapdsl
SNAPS = snapdsl.parse(C.CONTENT / "snaps.txt", SID, UK)
print("snaps", [s["y"] for s in SNAPS])

for sn in SNAPS:
    missing = [s["id"] for s in SEEDS if s["id"] not in sn["st"]["own"]]
    if missing: print("  unassigned at", sn["y"], missing)

def pol_of(st, uk): return st["pol"].get(uk, UNITS[UK[uk]]["pol"])

# ======================================================================
# 3. 海陆栅格
# ======================================================================
LANDG = []
for f in ne("ne_10m_land")["features"]:
    LANDG += polys_of(shape(f["geometry"]).intersection(BB))
for f in ne("ne_10m_minor_islands")["features"]:
    g = shape(f["geometry"])
    if g.intersects(BB): LANDG += polys_of(g.intersection(BB))
landU = unary_union(LANDG)
LAKEG = []
for f in ne("ne_10m_lakes")["features"]:
    if not f["geometry"]: continue
    g = shape(f["geometry"])
    if g.intersects(BB): LAKEG.append((f["properties"].get("name"), g.intersection(BB)))
for f in ne("ne_10m_lakes_historic")["features"]:
    if not f["geometry"]: continue
    g = shape(f["geometry"])
    if g.intersects(BB) and f["properties"].get("name") == "Lop Nur": LAKEG.append(("Lop Nur", g.intersection(BB)))

def rasterize(geoms):
    m = np.zeros((NY, NX), bool)
    for g in geoms:
        for p in polys_of(g):
            ext = np.array(p.exterior.coords)
            rr, cc = draw.polygon((ext[:, 1] - LAT0) / RES, (ext[:, 0] - LON0) / RES, shape=(NY, NX))
            m[rr, cc] = True
            for h in p.interiors:
                a = np.array(h.coords)
                rr, cc = draw.polygon((a[:, 1] - LAT0) / RES, (a[:, 0] - LON0) / RES, shape=(NY, NX))
                m[rr, cc] = False
    return m
LAND = rasterize([landU])
LAND &= ~rasterize([g for n, g in LAKEG if g.area > C.BIG_LAKE_AREA])
print("land cells", LAND.sum())

# ======================================================================
# 4. 通行代价栅格：山脉、大河
# ======================================================================
cost = np.ones((NY, NX))
def burn_lines(lines, amp, sig):
    m = np.zeros((NY, NX), bool)
    for pts in lines:
        ls = LineString(pts)
        n = max(2, int(ls.length / (RES / 3)))
        for i in range(n + 1):
            p = ls.interpolate(i / n, normalized=True)
            r, c = to_rc(p.x, p.y)
            r, c = int(round(r)), int(round(c))
            if 0 <= r < NY and 0 <= c < NX: m[r, c] = True
    d = ndimage.distance_transform_edt(~m) * RES
    return amp * np.exp(-(d / sig) ** 2)
cost += burn_lines([r[2] for r in IM.RANGES if r[4]], *C.COST_MAJOR_RANGE)
cost += burn_lines([r[2] for r in IM.RANGES if not r[4]], *C.COST_MINOR_RANGE)
RANGEPOLY = []
DESERTPOLY = {}
for f in ne("ne_10m_geography_regions_polys")["features"]:
    p = f["properties"]
    if not f["geometry"]: continue
    g = shape(f["geometry"])
    if not g.intersects(BB): continue
    if p.get("FEATURECLA") == "Range/mtn" and g.area < 60: RANGEPOLY.append(g)
    if p.get("FEATURECLA") == "Desert": DESERTPOLY[p.get("NAME")] = g
cost += C.COST_RANGE_POLY[0] * ndimage.gaussian_filter(rasterize(RANGEPOLY).astype(float), C.COST_RANGE_POLY[1])

NE_RV = []
for f in ne("ne_10m_rivers_lake_centerlines")["features"]:
    g = f["geometry"]
    if not g: continue
    gg = shape(g)
    if not gg.intersects(BB): continue
    p = f["properties"]
    for ls in lines_of(gg.intersection(BB)):
        NE_RV.append((p.get("name"), p.get("scalerank"), ls))
def rv_lines(names):
    return [list(ls.coords) for n, sr, ls in NE_RV if n in names]
cost += burn_lines(rv_lines({"Chang Jiang", "Yangtze"}), *C.COST_YANGTZE)
cost += burn_lines(rv_lines({"Huang"}) + [m[2] for m in IM.MANUAL_RIVERS if m[0] == "河"], *C.COST_HUANGHE)
cost += burn_lines(rv_lines({"Huai"}) + [m[2] for m in IM.MANUAL_RIVERS if m[0] == "淮水"], *C.COST_HUAI)
cost[~LAND] = np.inf
print("cost built")

# ======================================================================
# 5. 多源最短路：每个格子归代价距离最近的州
# ======================================================================
idx = np.arange(NY * NX).reshape(NY, NX)
coslat = np.cos(np.radians(lats))[:, None] * np.ones((1, NX))
rows, cols, ws = [], [], []
for dr, dc in [(0, 1), (1, 0), (1, 1), (1, -1)]:      # 8 邻接（每条边存两次）
    r0 = slice(0, NY - dr); r1 = slice(dr, NY)
    if dc >= 0: c0 = slice(0, NX - dc); c1 = slice(dc, NX)
    else: c0 = slice(-dc, NX); c1 = slice(0, NX + dc)
    a = idx[r0, c0].ravel(); b = idx[r1, c1].ravel()
    step = np.sqrt((dc * coslat[r0, c0]) ** 2 + dr ** 2).ravel() * RES   # 经向距离按纬度余弦缩短
    w = 0.5 * (cost[r0, c0].ravel() + cost[r1, c1].ravel()) * step
    ok = np.isfinite(w)
    rows += [a[ok], b[ok]]; cols += [b[ok], a[ok]]; ws += [w[ok], w[ok]]
G = coo_matrix((np.concatenate(ws), (np.concatenate(rows), np.concatenate(cols))), shape=(NY * NX, NY * NX)).tocsr()

taken = set()
sidx = []
for s in SEEDS:   # 把种子吸附到最近的、未被占用的陆地格
    r, c = to_rc(s["lon"], s["lat"]); r, c = int(round(r)), int(round(c))
    best = None
    for rad in range(0, 8):
        cands = []
        for dr in range(-rad, rad + 1):
            for dc in range(-rad, rad + 1):
                rr, cc = r + dr, c + dc
                if 0 <= rr < NY and 0 <= cc < NX and LAND[rr, cc] and idx[rr, cc] not in taken:
                    cands.append((dr * dr + dc * dc, rr, cc))
        if cands: best = min(cands); break
    if best is None: raise SystemExit("种子不在陆地上: " + s["id"])
    k = idx[best[1], best[2]]; taken.add(k); sidx.append(k)
dist, pred, src = dijkstra(G, indices=sidx, min_only=True, return_predecessors=True)
src = src.reshape(NY, NX); dist = dist.reshape(NY, NX)
seedpos = {v: i for i, v in enumerate(sidx)}
label = np.full((NY, NX), -1, int)
okm = src >= 0
label[okm] = np.vectorize(lambda v: seedpos.get(v, -1))(src[okm])
label[(dist > C.MAX_REACH) | ~LAND] = -1
print("labelled; reachable land", (label >= 0).sum(), "/", LAND.sum())

# ======================================================================
# 6. 各节点疆域多边形
# ======================================================================
def extend_to_sea(own):
    out = own.copy()
    dd, (jr, jc) = ndimage.distance_transform_edt(~(own >= 0), return_indices=True)
    fill = (~LAND) & (dd <= C.SEA_FILL_CELLS)
    out[fill] = own[jr[fill], jc[fill]]
    return out

def shapes_for(own, key_ids):
    shapes, labs = {}, {}
    for k in key_ids:
        m = own == k
        if not m.any(): continue
        sm = ndimage.gaussian_filter(m.astype(float), C.SMOOTH_SIGMA)
        pad = np.pad(sm, 1)
        rings = []
        for cnt in measure.find_contours(pad, 0.5):   # marching squares 等值线
            cnt = cnt - 1
            pts = [(LON0 + c * RES, LAT0 + r * RES) for r, c in cnt]
            if len(pts) < 4: continue
            ls = LineString(pts).simplify(C.SIMPLIFY_TERR)
            if len(ls.coords) < 4 or Polygon(ls.coords).area < C.MIN_RING_AREA: continue
            rings.append(enc_ring(list(ls.coords)))
        if not rings: continue
        shapes[k] = rings
        # 注记点：最大连通块内离边界最远的格子（“不可达极点”）
        ml = m & LAND
        if not ml.any(): ml = m
        lab, n = ndimage.label(ml)
        sizes = ndimage.sum(ml, lab, range(1, n + 1))
        big = lab == (int(np.argmax(sizes)) + 1)
        dt = ndimage.distance_transform_edt(np.pad(big, 1))[1:-1, 1:-1]
        r, c = np.unravel_index(np.argmax(dt), dt.shape)
        area = float(ml.sum()) * RES * RES
        labs[k] = [round(LON0 + c * RES, 2), round(LAT0 + r * RES, 2), round(area, 2), round(float(dt[r, c]) * RES, 2)]
    return shapes, labs

ADJ_Z, ADJ_P = set(), set()
def adj_pairs(own, S):
    for a, b in [(own[:, :-1], own[:, 1:]), (own[:-1, :], own[1:, :])]:
        m = (a != b) & (a >= 0) & (b >= 0)
        for x, y in set(zip(a[m].tolist(), b[m].tolist())):
            S.add((min(x, y), max(x, y)))

OUTSN = []
for sn in SNAPS:
    st = sn["st"]
    own_seed = np.full(len(SEEDS), -1, int)
    for sid, uk in st["own"].items():
        if uk is not None: own_seed[SID[sid]] = UK[uk]
    zr = np.where(label >= 0, own_seed[np.clip(label, 0, None)], -1)   # 藩镇级
    zr[label < 0] = -1
    present = sorted(set(own_seed[own_seed >= 0].tolist()))
    polmap = {u: UK[pol_of(st, UNITS[u]["k"])] for u in present}
    pr = zr.copy()                                                      # 政权级
    for u, p in polmap.items(): pr[zr == u] = p
    adj_pairs(zr, ADJ_Z); adj_pairs(pr, ADJ_P)
    zsh, zlab = shapes_for(extend_to_sea(zr), present)
    multi = sorted({p for u, p in polmap.items() if p != u or list(polmap.values()).count(p) > 1})
    psh, plab = shapes_for(extend_to_sea(pr), multi)
    OUTSN.append(dict(y=sn["y"], era=sn["era"], t=sn["t"], d=sn["d"],
             z={str(k): v for k, v in zsh.items()}, lz={str(k): v for k, v in zlab.items()},
             p={str(k): v for k, v in psh.items()}, lp={str(k): v for k, v in plab.items()},
             own=own_seed.tolist(),
             pol={str(u): p for u, p in polmap.items()},
             lab={str(UK[k]): v for k, v in st["lab"].items() if UK[k] in polmap or UK[k] in polmap.values()},
             seat={str(UK[k]): SID[v] for k, v in st["seat"].items() if UK[k] in polmap},
             h=sorted(UK[k] for k in st["hatch"] if UK[k] in polmap)))
    print("snap", sn["y"], "units", len(present), "polities", len(set(polmap.values())), "multi", [UNITS[p]["k"] for p in multi])

# ======================================================================
# 7. 配色：低饱和度，相邻单位尽量区分（OKLCH 空间贪心着色）
# ======================================================================
def oklch_to_rgb(L, Cc, h):
    a = Cc * math.cos(math.radians(h)); b = Cc * math.sin(math.radians(h))
    l_ = L + 0.3963377774 * a + 0.2158037573 * b
    m_ = L - 0.1055613458 * a - 0.0638541728 * b
    s_ = L - 0.0894841775 * a - 1.2914855480 * b
    l, m, s = l_ ** 3, m_ ** 3, s_ ** 3
    r = 4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s
    g = -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s
    bb = -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s
    def gam(x):
        x = max(0, min(1, x))
        return 12.92 * x if x <= 0.0031308 else 1.055 * x ** (1 / 2.4) - 0.055
    return "#%02X%02X%02X" % tuple(int(round(gam(v) * 255)) for v in (r, g, bb))
PAL = [(L, Cc, (i * C.PALETTE_HUE_STEP + off) % 360) for L, Cc, off in C.PALETTE_LEVELS for i in range(360 // C.PALETTE_HUE_STEP)]
def lab_of_pal(p):
    L, Cc, h = p
    return np.array([L, Cc * math.cos(math.radians(h)), Cc * math.sin(math.radians(h))])
PL = [lab_of_pal(p) for p in PAL]
nbr = {i: set() for i in range(len(UNITS))}
for a, b in ADJ_Z | ADJ_P:
    nbr[a].add(b); nbr[b].add(a)
color = {UK[k]: v for k, v in C.PRESET_COLORS.items()}
# 已发布单位的颜色锁定在 content/colors.lock.json：补节点、加单位不会改动原有颜色（与宋元 979 衔接的颜色也因此不变）
LOCKED = json.load(open(C.COLOR_LOCK, encoding="utf8")) if C.COLOR_LOCK.exists() else {}
for k, v in LOCKED.items():
    if k in UK: color[UK[k]] = tuple(v)
usage = {}
for u in sorted(range(len(UNITS)), key=lambda u: -len(nbr[u])):   # 邻居多的先挑
    if u in color: continue
    best, bs = None, -1
    for j, p in enumerate(PAL):
        dmin = min([np.linalg.norm(PL[j] - lab_of_pal(color[n])) for n in nbr[u] if n in color] + [1.0])
        score = dmin - C.REUSE_PENALTY * usage.get(j, 0)
        if score > bs: bs, best = score, j
    color[u] = PAL[best]; usage[best] = usage.get(best, 0) + 1
FALLBACK = (0.75, 0.03, 90)
LIGHT = {u: oklch_to_rgb(*color.get(u, FALLBACK)) for u in range(len(UNITS))}
DARK = {}
for u in range(len(UNITS)):
    L, Cc, h = color.get(u, FALLBACK)
    DARK[u] = oklch_to_rgb(min(C.DARK_L_MAX, L + C.DARK_L_LIFT), Cc + C.DARK_C_LIFT, h)
json.dump({UNITS[u]["k"]: [round(x, 6) for x in color[u]] for u in sorted(color)}, open(C.BUILD / "colors.json", "w", encoding="utf8"), ensure_ascii=False, indent=0)
mind = min([np.linalg.norm(lab_of_pal(color[a]) - lab_of_pal(color[b])) for a, b in ADJ_Z] or [0])
print("min neighbour colour distance", round(mind, 3))

# ======================================================================
# 8. 底图要素与条目
# ======================================================================
LAND_OUT = []
for p in polys_of(landU.intersection(box(LON0 - 0.5, LAT0 - 0.5, LON1 + 0.5, LAT1 + 0.5))):
    p = p.simplify(C.SIMPLIFY_LAND)
    if p.is_empty or p.area < C.LAND_MIN_AREA: continue
    for q in polys_of(p):
        rings = [enc_ring(list(q.exterior.coords))] + [enc_ring(list(h.coords)) for h in q.interiors if Polygon(h).area > C.LAND_HOLE_MIN_AREA]
        LAND_OUT.append(rings)
print("land polys", len(LAND_OUT))

BORDER = []
for f in ne("ne_10m_admin_0_boundary_lines_land")["features"]:
    g = shape(f["geometry"])
    if not g.intersects(BB): continue
    for ls in lines_of(g.intersection(box(LON0, LAT0, LON1, LAT1))):
        ls = ls.simplify(C.SIMPLIFY_BORDER)
        if ls.length > 0.05: BORDER.append(enc_ring(list(ls.coords)))

PROV = json.load(open(C.PROV_JSON, encoding="utf8"))

ITEMS = []
def add_item(d): d["i"] = len(ITEMS); ITEMS.append(d); return d["i"]

# 河流：Natural Earth 河道 + 手绘古河道，按古名合并为条目
RIVERS = []
river_item = {}
# 同一古名的河分几段时，条目的今名与说明取 NE_RIVERS 里写在最前的那一段（而不是底图里先遇到的那段）
RIVER_PRIMARY = {}
for _k, _v in IM.NE_RIVERS.items(): RIVER_PRIMARY.setdefault(_v[0], _v)
for n, sr, ls in NE_RV:
    if n == "Hudi": continue
    pts = list(ls.simplify(C.SIMPLIFY_RIVER).coords)
    if len(pts) < 2: continue
    xs = [x for x, y in pts]
    name = n
    if n == "Han" and min(xs) > 120: name = "Han_kr"
    if n == "Min" and min(xs) > 110: info = ("闽江", "闽江", "建溪、富屯溪汇合后经福州入海。", 0)
    else: info = IM.NE_RIVERS.get(name)
    kind = "faint"
    if sr is not None and sr <= 6: kind = "minor"
    if info: kind = "major" if info[3] else "minor"
    if n == "Huang" and min(xs) > 110:     # 今黄河下游：郑州以西照画，以东改成虚线“今河道”
        west = [(x, y) for x, y in pts if x <= 113.65]
        east = [(x, y) for x, y in pts if x >= 113.55]
        if len(west) > 1: RIVERS.append(dict(k="major", p=enc_ring(west), it=None, nm="河"))
        if len(east) > 1: RIVERS.append(dict(k="modern", p=enc_ring(east), it=None, nm=None))
        continue
    if sr is not None and sr >= 9 and not info: continue
    RIVERS.append(dict(k=kind, p=enc_ring(pts), nm=(info[0] if info else None), info=info))
for nm, mod, pts, note, major in IM.MANUAL_RIVERS:
    RIVERS.append(dict(k="major" if major else "minor", p=enc_ring(pts), nm=nm, info=(nm, mod, note, major), manual=True))
for r in RIVERS:
    if not r.get("nm"): r["it"] = None; continue
    info = r.get("info")
    key = r["nm"]
    if key not in river_item:
        if info is None: info = IM.NE_RIVERS["Huang"]
        if not r.get("manual"): info = RIVER_PRIMARY.get(key, info)
        mod = info[1]; note = info[2]
        if key == "河": mod, note = "黄河", IM.MANUAL_RIVERS[0][3]
        if key == "淮水": mod, note = "淮河", "淮水。958 年以前，后周与南唐以淮为界，此后以长江为界。唐至北宋时淮河经泗州、楚州独流入海（1194 年后黄河夺淮，下游淤塞形成洪泽湖）。"
        river_item[key] = add_item(dict(c="river", sub="river", old=key, mod=mod, note=note, major=bool(info[3])))
    r["it"] = river_item[key]
seglen = {}   # 注记锚点：每条河最长一段的中点
for r in RIVERS:
    if r.get("it") is None: continue
    x = y = 0; pts = []
    for i in range(0, len(r["p"]), 2): x += r["p"][i]; y += r["p"][i + 1]; pts.append((x / 100, y / 100))
    if len(pts) < 2: continue
    L = LineString(pts).length
    if L > seglen.get(r["it"], (0, None))[0]:
        mid = LineString(pts).interpolate(0.5, normalized=True)
        seglen[r["it"]] = (L, [round(mid.x, 3), round(mid.y, 3)])
for it, (L, a) in seglen.items(): ITEMS[it]["anc"] = a
RIV_OUT = [dict(k=r["k"], p=r["p"], **({"it": r["it"]} if r.get("it") is not None else {})) for r in RIVERS]
print("rivers", len(RIV_OUT), "named", len(river_item))

LAKES = []
for n, g in LAKEG:
    info = IM.NE_LAKES.get(n)
    if not info and g.area < 0.03: continue
    for p in polys_of(g.simplify(C.SIMPLIFY_LAKE)):
        if p.area < 0.004: continue
        it = None
        if info:
            ex = [x for x in ITEMS if x["c"] == "river" and x.get("sub") == "lake" and x["old"] == info[0] and x["mod"] == info[1]]
            if ex: it = ex[0]["i"]
            else:
                c = p.representative_point()
                it = add_item(dict(c="river", sub="lake", old=info[0], mod=info[1], note=info[2], anc=[round(c.x, 2), round(c.y, 2)]))
        LAKES.append(dict(r=enc_ring(list(p.exterior.coords)), **({"it": it} if it is not None else {})))
for nm, mod, lo, la, rx, ry, note in IM.MARSHES:
    add_item(dict(c="river", sub="marsh", old=nm, mod=mod, note=note, lon=lo, lat=la, rx=rx, ry=ry, anc=[lo, la]))
CAN = []
for nm, mod, pts, note in IM.CANALS:
    it = add_item(dict(c="canal", old=nm, mod=mod, note=note, anc=list(LineString(pts).interpolate(0.5, normalized=True).coords[0])))
    CAN.append(dict(p=enc_ring(pts), it=it))
for nm, mod, pts, note, major in IM.RANGES:
    a = LineString(pts).interpolate(0.5, normalized=True)
    add_item(dict(c="range", old=nm, mod=mod, note=note, geo=pts, anc=[round(a.x, 3), round(a.y, 3)], major=bool(major)))
DES = []
for nm, mod, nename, note in IM.DESERTS:
    g = DESERTPOLY.get(nename)
    if g is None: print("no desert", nename); continue
    c = g.representative_point()
    it = add_item(dict(c="desert", old=nm, mod=mod, note=note, anc=[round(c.x, 2), round(c.y, 2)]))
    for p in polys_of(g.simplify(0.05)):
        DES.append(dict(r=enc_ring(list(p.exterior.coords)), it=it))

for nm, mod, lo, la, st, yrs, note, at in IM.CAPITALS:
    assert st in UK, ("都城所属政权不存在", st)
    add_item(dict(c="capital", old=nm, mod=mod, lon=lo, lat=la, st=UK[st], yrs=yrs, note=note, at=SID.get(at) if at else None))
for nm, mod, lo, la, y, yt, sides, cmd, note in IM.BATTLES:
    add_item(dict(c="battle", old=nm, mod=mod, lon=lo, lat=la, y=y, yt=yt, sides=sides, cmd=cmd, note=note))
for nm, mod, lo, la, note in IM.PASSES:
    add_item(dict(c="pass", old=nm, mod=mod, lon=lo, lat=la, note=note))
EVENT_END = getattr(IM, "EVENT_END", {})
for nm, mod, lo, la, y, yt, note in IM.EVENTS:
    d = dict(c="event", old=nm, mod=mod, lon=lo, lat=la, y=y, yt=yt, note=note)
    if nm in EVENT_END: d["y1"] = EVENT_END[nm]
    add_item(d)
for nm, lo, la, y0, y1, note in IM.PEOPLES:
    add_item(dict(c="people", old=nm, mod="", lon=lo, lat=la, y0=y0, y1=y1, note=note))

# 行军路线：每条一组 [经, 纬, 到达年, 地名]，前端按节点年份画出已走过的一段
ROUTES = []
for R in getattr(IM, "ROUTES", []):
    pts = [list(p) for p in R["pts"]]
    it = add_item(dict(c="route", old=R["name"], mod=R["mod"], note=R["note"], y=pts[0][2], y1=pts[-1][2],
                       yt=R.get("yt", f"{pts[0][2]}—{pts[-1][2]}"), anc=pts[len(pts) // 2][:2]))
    ROUTES.append(dict(it=it, pts=pts))

# 重要地域（如燕云十六州）：由成员州的栅格并集描出范围线，分区之间画分界线
from scipy.ndimage import map_coordinates
REG_OUT = []
for R in getattr(IM, "REGIONS", []):
    ids = lambda names: [SID[n] for n in names]
    for n in R["members"] + R.get("extra", []): assert n in SID, ("地域成员不在 seeds.txt", n)
    allm = np.isin(label, ids(R["members"] + R.get("extra", [])))
    rsh, rlab = shapes_for(extend_to_sea(np.where(allm, 1, -1)), [1])
    su = ndimage.gaussian_filter(allm.astype(float), C.SMOOTH_SIGMA)
    groups = []
    for g in R.get("groups", []):
        gm = np.isin(label, ids(g["members"] + g.get("extra", [])))
        _, glab = shapes_for(np.where(gm, 1, -1), [1])
        # 分区注记避开地域总名：离总名不足 1.2° 的格子不参与选点
        ml = gm & LAND
        lab_, n_ = ndimage.label(ml)
        if n_:
            big = lab_ == (int(np.argmax(ndimage.sum(ml, lab_, range(1, n_ + 1)))) + 1)
            dt = ndimage.distance_transform_edt(np.pad(big, 1))[1:-1, 1:-1]
            lo0, la0 = rlab[1][0], rlab[1][1]
            near = np.hypot((lons[None, :] - lo0) * np.cos(np.radians(la0)), lats[:, None] - la0) < 1.2
            dt2 = np.where(near, 0, dt)
            if dt2.max() > 0:
                r_, c_ = np.unravel_index(np.argmax(dt2), dt2.shape)
                glab[1] = [round(LON0 + c_ * RES, 2), round(LAT0 + r_ * RES, 2), glab[1][2], round(float(dt2[r_, c_]) * RES, 2)]
        lines = []
        if g.get("line"):
            sg = ndimage.gaussian_filter(gm.astype(float), C.SMOOTH_SIGMA)
            for cnt in measure.find_contours(sg, 0.5):
                inside = map_coordinates(su, cnt.T, order=1) > 0.8   # 只保留并集内部的那段，即两区分界
                run = []
                for (r, c), ok in zip(cnt, inside):
                    if ok: run.append((LON0 + c * RES, LAT0 + r * RES))
                    elif run:
                        if len(run) > 3: lines.append(run)
                        run = []
                if len(run) > 3: lines.append(run)
            lines = [enc_ring(list(LineString(l).simplify(C.SIMPLIFY_TERR).coords)) for l in lines]
        groups.append(dict(n=g["name"], y0=g.get("y0", R["y0"]), lab=glab.get(1), lines=lines))
    it = add_item(dict(c="region", old=R["name"], mod=R["mod"], note=R["note"], y0=R["y0"],
                       members=ids(R["members"]), anc=rlab[1][:2], lab=rlab[1]))
    REG_OUT.append(dict(it=it, y0=R["y0"], rings=rsh[1], groups=groups))
print("regions", [(ITEMS[r["it"]]["old"], len(r["rings"]), [(g["n"], len(g["lines"])) for g in r["groups"]]) for r in REG_OUT])

# ======================================================================
# 输出
# ======================================================================
GEO = dict(land=LAND_OUT, prov=PROV, border=BORDER, rivers=RIV_OUT, lakes=LAKES, canals=CAN, deserts=DES, snaps=OUTSN, regions=REG_OUT, routes=ROUTES,
           ext=[LON0, LON1, LAT0, LAT1], first=C.FIRST)
UOUT = [dict(k=u["k"], n=u["n"], kind=u["kind"], note=u["note"], cl=LIGHT[i], cd=DARK[i]) for i, u in enumerate(UNITS)]
SOUT = [dict(id=s["id"], n=s["n"], mod=s["mod"], lon=s["lon"], lat=s["lat"], t=s["t"], **({"nm": s["names"]} if s["names"] else {})) for s in SEEDS]
DATA = dict(units=UOUT, seeds=SOUT, items=ITEMS)
C.BUILD.mkdir(exist_ok=True)
json.dump(GEO, open(C.BUILD / "geo.json", "w", encoding="utf8"), ensure_ascii=False, separators=(",", ":"))
json.dump(DATA, open(C.BUILD / "data.json", "w", encoding="utf8"), ensure_ascii=False, separators=(",", ":"))
np.save(C.BUILD / "label.npy", label)   # 每个格子归哪个州，供调试
print("geo.json", (C.BUILD / "geo.json").stat().st_size // 1024, "KB; data.json", (C.BUILD / "data.json").stat().st_size // 1024, "KB")
