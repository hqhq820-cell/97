import asyncio, os, requests
from playwright.async_api import async_playwright

USER_ID = "2890174992"
KWAI_ID = "3xjf8stieruidvy"
ANCHOR  = "大big"
URL = f"https://m.chenzhongtech.com/fw/live/{KWAI_ID}?userId={USER_ID}"
UA = ("Mozilla/5.0 (Linux; Android 13; Pixel 7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36")
SCKEY = os.environ.get("SCKEY", "")

def push(msg):
    if not SCKEY:
        print("no SCKEY, skip push")
        return
    try:
        r = requests.post(f"https://sctapi.ftqq.com/{SCKEY}.send",
                          data={"title": "快手开播提醒", "desp": msg}, timeout=10)
        print("push resp:", r.status_code, r.text[:200])
    except Exception as e:
        print("push fail:", e)

async def get_title():
    async with async_playwright() as p:
        b = await p.chromium.launch(headless=True, args=["--no-sandbox"])
        ctx = await b.new_context(user_agent=UA, viewport={"width":412,"height":915})
        await ctx.add_init_script(
            "Object.defineProperty(navigator,'webdriver',{get:()=>undefined});")
        pg = await ctx.new_page()
        try:
            await pg.goto(URL, wait_until="domcontentloaded", timeout=45000)
        except Exception as e:
            print("goto fail:", e)
        await pg.wait_for_timeout(10000)
        t = await pg.title()
        await b.close()
        return t

title = ""
try:
    title = asyncio.run(get_title())
except Exception as e:
    print("get_title fail:", e)

live = ANCHOR in title
print("title:", title, "| live:", live)

state_file = "state.json"
prev = ""
try:
    prev = open(state_file).read()
except:
    pass
cur = "live" if live else "off"
if cur != prev:
    open(state_file, "w").write(cur)
    if live:
        push(f"{ANCHOR} 开播了！\ntitle: {title}")