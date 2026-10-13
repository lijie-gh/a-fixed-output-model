# -*- coding: utf-8 -*-
"""pelican-fixed 总验收：5 组默认/极限采样 + 原版 0u0-pelican 对照。"""
import json
import sys
import urllib.request

URL = "http://127.0.0.1:11434/api/generate"
ORIG = open(r"C:\Users\李杰\Desktop\鹈鹕骑自行车网页.txt", "rb").read()
P = "pelican-fixed"
O = "hf.co/0v0ai/0u0-pelican-0.1B-GGUF:Q4_K_M"


def ask(model, prompt, raw, options=None):
    body = {"model": model, "prompt": prompt, "stream": False, "raw": raw}
    if options:
        body["options"] = options
    req = urllib.request.Request(URL, data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=600) as r:
        resp = json.load(r)
    return resp.get("response", "").encode("utf-8"), resp


def check(label, model, prompt, raw, options=None):
    got, resp = ask(model, prompt, raw, options)
    ok = got == ORIG
    print(f"[验收] {label:<36} {len(got):>6} 字节  逐字节一致:{'OK ' if ok else 'FAIL'}"
          f"  tokens={resp.get('eval_count')}  停止={resp.get('done_reason')}")
    return ok


def probe(label, model, prompt, raw, options=None):
    got, resp = ask(model, prompt, raw, options)
    looks_svg = got.strip().startswith(b"<?xml") and b"<svg" in got
    print(f"[对照] {label:<36} {len(got):>6} 字节  看起来像完整SVG:{looks_svg}"
          f"  tokens={resp.get('eval_count')}  停止={resp.get('done_reason')}")
    print(f"        头部: {got[:64]!r}")


all_ok = True
all_ok &= check("默认采样 · 中文", P, "你好呀，帮我画个别的动物", False)
all_ok &= check("默认采样 · 英文(raw)", P, "hello pelican, ride faster!", True)
all_ok &= check("默认采样 · emoji", P, "🦆🚲", False)
all_ok &= check("默认采样 · 空格", P, " ", False)
all_ok &= check("极限采样 · temp=2 / top_k 全开",
                P, "热车", False,
                dict(temperature=2.0, top_k=999999, top_p=1.0, repeat_penalty=1.0))

print("--- 原版 0u0-pelican 同环境对照 ---")
probe("原版 · 默认采样", O, "hi", True)
probe("原版 · temp=0 + 惩罚关 + top_k=1", O, "hi", True,
      dict(temperature=0.0, repeat_penalty=1.0, top_k=1, top_p=1.0))

print("=== 我们的模型:", "全部通过" if all_ok else "有失败")
sys.exit(0 if all_ok else 1)
