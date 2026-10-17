import os, json, re, requests
from datetime import datetime, timezone, timedelta

KWAI_ID = "3xjf8stieruidvy"
ANCHOR  = "大big"
URL = f"https://live.kuaishou.com/u/{KWAI_ID}"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
SCKEY = os.environ.get("SCKEY", "")

def push(title):
    if not SCKEY:
        print("no SCKEY, skip push")
        return
    try:
        r = requests.post(f"https://sctapi.ftqq.com/{SCKEY}.send",
                          data={"title": title, "desp": " "}, timeout=10)
        print("push resp:", r.status_code, r.text[:200])
    except Exception as e:
        print("push fail:", e)

def check():
    diag = {"http": 0, "size": 0, "title": "", "has_hls": False, "has_stream": False}
    try:
        r = requests.get(URL, headers={"User-Agent": UA}, timeout=25)
        diag["http"] = r.status_code
        html = r.text
        diag["size"] = len(html)
        m = re.search(r"<title[^>]*>(.*?)</title>", html, re.S)
        if m:
            diag["title"] = m.group(1).strip()
        diag["has_hls"] = '"hlsPlayUrl"' in html
        diag["has_stream"] = '"liveStream":{"id"' in html
    except Exception as e:
        diag["error"] = str(e)
    return diag

state = {}
try:
    with open("state.json") as f:
        state = json.load(f)
except Exception:
    pass
prev = state.get("state", "off")
start_date = state.get("start_notified_date", "")

now_bj = datetime.now(timezone.utc) + timedelta(hours=8)
today = now_bj.strftime("%Y-%m-%d")
minutes = now_bj.hour * 60 + now_bj.minute

# 检测窗口：19:00 - 24:00
if minutes < 19*60:
    print("before 19:00, skip")
    exit(0)

# 当天第一次运行：重置状态 + 发"开始检测"
if start_date != today:
    prev = "off"
    push("大B哥开始检测")
    state["start_notified_date"] = today

d = check()
live = d["has_hls"] or d["has_stream"]
print("diag:", json.dumps(d, ensure_ascii=False))
print("prev:", prev, "live:", live)

state["state"] = "live" if live else "off"
state["live"] = live
state["diag"] = d
open("state.json", "w").write(json.dumps(state, ensure_ascii=False))

if live and prev != "live":
    push("大B哥开播了")