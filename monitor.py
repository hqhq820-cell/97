import os, json, re, requests

KWAI_ID = "3xjf8stieruidvy"
ANCHOR  = "大big"
URL = f"https://live.kuaishou.com/u/{KWAI_ID}"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36")
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

d = check()
live = d["has_hls"] or d["has_stream"]
print("diag:", json.dumps(d, ensure_ascii=False))
print("live:", live)

state_data = {"state": "live" if live else "off", "live": live, "diag": d}
open("state.json", "w").write(json.dumps(state_data, ensure_ascii=False))

if live:
    push(f"{ANCHOR} 开播了！\ntitle: {d['title']}")