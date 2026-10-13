# -*- coding: utf-8 -*-
"""Q3/Q2 导入 Ollama + 逐字节验收 + logprobs 间隔实测。"""
import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request

HERE = r"C:\Users\李杰\WorkBuddy\2026-10-13-20-40-36\handmade-gguf"
OLLAMA_EXE = r"C:\Users\李杰\AppData\Local\Programs\Ollama\ollama.exe"
BASE = "http://127.0.0.1:11434"
OP = urllib.request.build_opener(urllib.request.ProxyHandler({}))
NEW = open(os.path.join(HERE, "payload2", "pelican-bike.html"), "rb").read()
SRC = r"C:\tmp\pelq"
MANI = r"D:\llm\ollama\models\manifests"
BLOB = r"D:\llm\ollama\models\blobs"

P = print


def api(path, body=None, timeout=600):
    data = None if body is None else json.dumps(body).encode()
    req = urllib.request.Request(BASE + path, data=data,
                                 headers={"Content-Type": "application/json"})
    with OP.open(req, timeout=timeout) as r:
        return json.load(r)


def ensure_server():
    try:
        api("/api/tags", None, timeout=3)
        P("服务器已在跑")
        return None
    except Exception:
        pass
    proc = subprocess.Popen([OLLAMA_EXE, "serve"], close_fds=True,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for i in range(40):
        time.sleep(1.5)
        try:
            api("/api/tags", None, timeout=3)
            P(f"已启动 ollama serve（{i + 1} 次探测后）")
            return proc
        except Exception:
            pass
    P("服务器起不来")
    sys.exit(1)


server = ensure_server()


def push_blob(path):
    data = open(path, "rb").read()
    digest = "sha256:" + hashlib.sha256(data).hexdigest()
    req = urllib.request.Request(f"{BASE}/api/blobs/{digest}", data=data,
                                 headers={"Content-Type": "application/octet-stream"},
                                 method="POST")
    try:
        with OP.open(req, timeout=300) as r:
            return digest
    except urllib.error.HTTPError as e:
        if e.code in (200, 201):
            return digest
        raise


import hashlib  # noqa: E402

TAGS = [("pelican-fixed:Q3_K_M", os.path.join(SRC, "pelican2-fixed-Q3_K_M.gguf")),
        ("pelican-fixed:Q2_K", os.path.join(SRC, "pelican2-fixed-Q2_K.gguf")),
        ("pelican-wide:Q3_K_M", os.path.join(SRC, "pelican2-wide-Q3_K_M.gguf")),
        ("pelican-wide:Q2_K", os.path.join(SRC, "pelican2-wide-Q2_K.gguf"))]

P("\n== 1) 导入 4 个 Q3/Q2 标签 ==")
for name, src in TAGS:
    dg = push_blob(src)
    body = {"model": name, "files": {os.path.basename(src): dg}, "stream": False}
    try:
        resp = api("/api/create", body, timeout=600)
        err = resp.get("error")
        P(f"[创建] {name:<24} {'OK' if not err else 'FAIL: ' + str(err)[:90]}")
    except urllib.error.HTTPError as e:
        P(f"[创建] {name:<24} HTTP {e.code}: {e.read().decode('utf-8', 'replace')[:110]}")
    except Exception as e:
        P(f"[创建] {name:<24} 异常 {type(e).__name__}: {e}")

P("\n== 2) 逐字节验收 ==")
CASES = [("中文/默认", "你好，随便说点什么", False, None),
         ("raw/默认", "hi", True, None),
         ("raw/temp2", "hi", True, {"temperature": 2.0, "top_k": 999999,
                                    "top_p": 1.0, "repeat_penalty": 1.0})]
fail = 0
for name, _ in TAGS:
    for label, prompt, raw, opts in CASES:
        body = {"model": name, "prompt": prompt, "stream": False, "raw": raw}
        if opts:
            body["options"] = opts
        try:
            resp = api("/api/generate", body, timeout=600)
        except Exception as e:
            P(f"  {name:<24} {label:<10} 请求失败 {type(e).__name__}")
            fail += 1
            continue
        got = (resp.get("response") or "").encode("utf-8")
        ok = got == NEW
        if not ok:
            fail += 1
        P(f"  {name:<24} {label:<10} {len(got):>7,}B {'OK ' if ok else 'FAIL'} tok={resp.get('eval_count')}")

P("\n== 3) 量化后 logprobs 间隔（raw/默认 采样下） ==")
for name, _ in TAGS:
    try:
        body = {"model": name, "prompt": "hi", "stream": False, "raw": True,
                "logprobs": True, "top_logprobs": 5}
        resp = api("/api/generate", body, timeout=600)
        lps = resp.get("logprobs") or []
        gs = []
        for e in lps:
            ch = e.get("logprob")
            tops = [t.get("logprob") for t in (e.get("top_logprobs") or [])
                    if t.get("token") != e.get("token")]
            if ch is not None and tops:
                gs.append(ch - max(tops))
        P(f"  {name:<24} 最小间隔 ≈ {min(gs):.2f}" if gs else f"  {name:<24} 无 logprobs")
    except Exception as e:
        P(f"  {name:<24} logprobs 失败 {type(e).__name__}")

P(f"\n验收失败数: {fail}")
P("完成")
