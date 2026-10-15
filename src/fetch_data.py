# -*- coding: utf-8 -*-
"""下载 Natural Earth 底图（固定提交版本）。geodata/ne/ 里已有的文件会跳过。"""
import sys, urllib.request
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
import config as C

def main(force=False):
    C.NE_DIR.mkdir(parents=True, exist_ok=True)
    for name in C.NE_FILES:
        dst = C.NE_DIR / f"{name}.geojson"
        if dst.exists() and dst.stat().st_size > 0 and not force:
            print("ok  ", dst.name); continue
        url = f"{C.NE_BASE}/{name}.geojson"
        print("get ", url)
        tmp = dst.with_suffix(".part")
        urllib.request.urlretrieve(url, tmp)
        tmp.replace(dst)
        print("     ", dst.stat().st_size // 1024, "KB")

if __name__ == "__main__":
    main(force="--force" in sys.argv)
