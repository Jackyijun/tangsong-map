# -*- coding: utf-8 -*-
"""（可选）用无头浏览器给成品截图，并检查页面有没有脚本错误。

需要：pip install playwright && python -m playwright install chromium
  python tools/screenshot.py            截 820 年全图（浅色、深色）和手机宽度
"""
import asyncio, os
from pathlib import Path
from playwright.async_api import async_playwright

ROOT = Path(__file__).resolve().parent.parent
PAGE = (ROOT / "dist" / "tangsong.html").as_uri()
OUT = ROOT / "build"

async def main():
    async with async_playwright() as p:
        kw = {"executable_path": os.environ["CHROMIUM_PATH"]} if os.environ.get("CHROMIUM_PATH") else {}
        b = await p.chromium.launch(**kw)
        errors = []
        for name, vp, scheme in [("desktop-light", (1440, 900), "light"), ("desktop-dark", (1440, 900), "dark"), ("phone", (400, 860), "light")]:
            ctx = await b.new_context(viewport={"width": vp[0], "height": vp[1]}, color_scheme=scheme)
            pg = await ctx.new_page()
            pg.on("pageerror", lambda e, n=name: errors.append((n, str(e))))
            await pg.goto(PAGE); await pg.wait_for_timeout(1200)
            # 依次切换全部时间节点、两种着色，确保不报错
            n = await pg.locator(".tick").count()
            for j in range(n): await pg.click(f'.tick[data-j="{j}"]')
            await pg.click('.tick[data-j="5"]'); await pg.wait_for_timeout(500)
            path = OUT / f"shot-{name}.png"
            await pg.screenshot(path=str(path)); print("wrote", path)
            await ctx.close()
        await b.close()
        print("脚本错误：", errors or "无")

asyncio.run(main())
