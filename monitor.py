import asyncio, os, requests
from playwright.async_api import async_playwright

USER_ID = "2890174992"        # 你的快手号(userId)
KWAI_ID = "3xjf8stieruidvy"   # 真实快手号
ANCHOR  = "大big"              # 主播名，title 含它 = 开播
URL = f"https://m.chenzhongtech.com/fw/live/{KWAI_ID}?userId={USER_ID}"
UA = ("Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36")
SCKEY = os.environ.get("SCKEY", "")   # Server酱 key，存 GitHub Secrets

def push(msg):
    if not SCKEY: return
    try:
        requests.post(f"https://sctapi.ftqq.com/{SCKEY}.send",
                      data={"title": "快手开播提醒", "desp": msg}, timeout=10)
    except Exception as e:
        print("push fail:", e)

async def get_title():
    async with async_playwright() as p:
        b = await p.chromium.launch(headless=True, args=["--no-sandbox"])
        ctx = await b.new_context(user_agent=UA, viewport={"width":412,"height":915})
        await ctx.add_init_script(
            "Object.defineProperty(navigator,'webdriver',{get:()=>undefined});")
        pg = await ctx.new_page()
        await pg.goto(URL, wait_until="domcontentloaded", timeout=30000)
        await pg.wait_for_timeout(8000)   # 等 JS 渲染出 title
        t = await pg.title()
        await b.close()
        return t

title = asyncio.run(get_title())
live = ANCHOR in title
print("title:", title, "| live:", live)

# 状态去重
state_file = "state.json"
prev = ""
try:
    prev = open(state_file).read()
except: pass
cur = "live" if live else "off"
if cur != prev:
    open(state_file, "w").write(cur)
    if live:
        push(f"{ANCHOR} 开播了！\ntitle: {title}")
