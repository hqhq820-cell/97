import asyncio, os, json, requests
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

async def probe():
    diag = {"goto": "ok", "wait": "", "title": "", "url": "", "has_video": False}
    async with async_playwright() as p:
        b = await p.chromium.launch(
            headless=True,
            args=["--no-sandbox", "--disable-blink-features=AutomationControlled"])
        ctx = await b.new_context(
            user_agent=UA, viewport={"width": 412, "height": 915},
            locale="zh-CN", is_mobile=True, has_touch=True)
        await ctx.add_init_script("""
Object.defineProperty(navigator,'webdriver',{get:()=>undefined});
Object.defineProperty(navigator,'languages',{get:()=>['zh-CN','zh','en']});
Object.defineProperty(navigator,'plugins',{get:()=>[1,2,3,4,5]});
window.chrome = {runtime:{}};
""")
        pg = await ctx.new_page()
        for i in range(2):
            try:
                await pg.goto(URL, wait_until="domcontentloaded", timeout=45000)
                diag["goto"] = "ok"
                break
            except Exception as e:
                diag["goto"] = f"fail{i}: {e}"
        try:
            await pg.wait_for_function(
                "t => document.title.includes(t)", arg=ANCHOR, timeout=40000)
            diag["wait"] = "title_changed"
        except Exception:
            diag["wait"] = "timeout_40s"
        try:
            diag["title"] = await pg.title()
            diag["url"] = pg.url
            diag["has_video"] = await pg.evaluate(
                "() => !!document.querySelector('video')")
        except Exception as e:
            diag["title"] = f"err: {e}"
        await b.close()
    return diag

diag = {"goto": "probe_fail", "wait": "", "title": "", "url": "", "has_video": False}
try:
    diag = asyncio.run(probe())
except Exception as e:
    diag["goto"] = f"probe_fail: {e}"

title = diag["title"]
live = ANCHOR in title
print("diag:", json.dumps(diag, ensure_ascii=False))
print("live:", live)

state_data = {"state": "live" if live else "off", "title": title,
              "live": live, "diag": diag}
open("state.json", "w").write(json.dumps(state_data, ensure_ascii=False))

if live:
    push(f"{ANCHOR} 开播了！\ntitle: {title}")