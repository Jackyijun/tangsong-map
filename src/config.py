# -*- coding: utf-8 -*-
"""唐宋之际形势图 · 构建参数。

改这里会影响疆域的形状、配色和底图精度；史料内容（州府、归属、战役等）在 content/ 目录。
改完参数后重新运行 `python run.py`。
"""
from pathlib import Path

# ---------------------------------------------------------------- 路径
ROOT = Path(__file__).resolve().parent.parent
CONTENT = ROOT / "content"          # 手写的史料内容
GEODATA = ROOT / "geodata"          # 底图数据
NE_DIR = GEODATA / "ne"             # Natural Earth 1:10m GeoJSON
PROV_JSON = GEODATA / "prov.json"   # 今省界（简化）
BUILD = ROOT / "build"              # 中间产物 geo.json / data.json
DIST = ROOT / "docs"                # 成品：docs/index.html（GitHub Pages 可直接从 /docs 发布）
TEMPLATE = ROOT / "src" / "template.html"

# ---------------------------------------------------------------- 底图来源
# Natural Earth 矢量数据（公有领域），固定到一个提交，保证可复现。
NE_COMMIT = "ca96624a56bd078437bca8184e78163e5039ad19"
NE_BASE = f"https://raw.githubusercontent.com/nvkelso/natural-earth-vector/{NE_COMMIT}/geojson"
NE_FILES = [
    "ne_10m_land",                        # 海陆
    "ne_10m_minor_islands",               # 小岛
    "ne_10m_lakes",                       # 湖泊
    "ne_10m_lakes_historic",              # 历史湖泊（罗布泊）
    "ne_10m_rivers_lake_centerlines",     # 河流
    "ne_10m_admin_0_boundary_lines_land", # 今国界
    "ne_10m_geography_regions_polys",     # 山地、沙漠多边形
]

# ---------------------------------------------------------------- 首屏
FIRST = 820                           # 打开网页时显示的时间节点（年份），写入 GEO.first

# ---------------------------------------------------------------- 栅格
# 计算疆域用的经纬网格。范围决定地图能画到哪里；分辨率越小越精细，也越慢（0.08° ≈ 8 km）。
EXTENT = (72.0, 136.0, 15.5, 55.0)   # 经度 min, max, 纬度 min, max
RES = 0.08

# ---------------------------------------------------------------- 通行代价（决定边界沿哪里走）
# 每个格子的基础代价为 1。山脉与大河附近代价升高，最短路就不容易越过，
# 于是两个州的“势力范围”分界会落在山脊、河道上。
# 形式：(峰值, 影响半径°)，代价增量 = 峰值 × exp(-(距离/半径)²)
COST_MAJOR_RANGE = (9.0, 0.28)   # items.RANGES 中标为主干的山脉（秦岭、太行、五岭……）
COST_MINOR_RANGE = (4.5, 0.18)   # 其他山脉
COST_RANGE_POLY = (1.6, 1.5)     # Natural Earth 山地多边形：(权重, 高斯模糊格数)
COST_YANGTZE = (7.0, 0.07)       # 长江
COST_HUANGHE = (3.5, 0.07)       # 黄河（含唐宋故道）
COST_HUAI = (3.5, 0.07)          # 淮河（含古下游）
MAX_REACH = 7.5                  # 离最近州府的代价距离超过此值的格子视为无主（荒漠、高原腹地）

# ---------------------------------------------------------------- 疆域多边形
SEA_FILL_CELLS = 4        # 疆域向海面外延的格数（让海岸线由陆地剪裁，不留缝）
SMOOTH_SIGMA = 1.15       # 边界平滑（高斯 σ，单位：格）
SIMPLIFY_TERR = 0.025     # 疆域折线简化容差（°）
MIN_RING_AREA = 0.02      # 小于此面积（平方度）的碎片丢弃
BIG_LAKE_AREA = 0.15      # 面积大于此值的湖泊在栅格里当作水面

# ---------------------------------------------------------------- 底图简化
SIMPLIFY_LAND = 0.015
LAND_MIN_AREA = 0.004
LAND_HOLE_MIN_AREA = 0.01
SIMPLIFY_BORDER = 0.02
SIMPLIFY_RIVER = 0.015
SIMPLIFY_LAKE = 0.01

# ---------------------------------------------------------------- 配色（OKLCH，低饱和）
# 候选色：三档明度 × 24 个色相。相邻的藩镇 / 政权会自动挑色差最大的颜色。
PALETTE_LEVELS = [   # (明度 L, 彩度 C, 色相偏移)
    (0.70, 0.075, 0),
    (0.78, 0.065, 7),
    (0.64, 0.075, 3),
]
PALETTE_HUE_STEP = 15
# 重要政权固定色：(L, C, 色相°)
PRESET_COLORS = {
    "唐": (0.74, 0.07, 75), "吐蕃": (0.70, 0.06, 330), "回鹘": (0.74, 0.07, 140), "南诏": (0.72, 0.07, 185),
    "渤海": (0.72, 0.065, 250), "契丹": (0.68, 0.06, 220), "新罗": (0.74, 0.07, 30), "宋": (0.72, 0.075, 55),
}
# 颜色锁：已发布单位的 OKLCH 颜色，构建时优先采用；不在锁里的单位才按邻接关系贪心选色。
# 删掉某一行可让该单位重新选色；删掉整个文件则全部重新着色（会与宋元 979 节点的颜色对不上）。
COLOR_LOCK = CONTENT / "colors.lock.json"
REUSE_PENALTY = 0.004     # 同一颜色被反复使用的惩罚，避免全图都是同几种色
DARK_L_LIFT = 0.06        # 深色主题：明度上调
DARK_C_LIFT = 0.015       # 深色主题：彩度上调
DARK_L_MAX = 0.86
