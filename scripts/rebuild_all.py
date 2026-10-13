# -*- coding: utf-8 -*-
"""换 payload 全流程（Ollama 端）：
1) 推送新 f16 blob，重建 8 个标签（fixed/wide × latest/Q8_0/Q4_K_M/Q4_K_S）
2) 全部标签逐字节验收（对比新页面字节）
3) 导出量化产物 + 就地覆盖本地 8 个文件（硬链接自动同步 LM Studio 副本）
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request

HERE = r"C:\Users\李杰\WorkBuddy\2026-10-13-20-40-36\handmade-gguf"
OLLAMA_EXE = r"C:\Users\李杰\AppData\Local\Programs\Ollama\ollama.exe"
BASE = "http://127.0.0.1:11434"
OP = urllib.request.build_opener(urllib.request.ProxyHandler({}))
PAYLOAD = os.path.join(HERE, "payload2", "pelican-bike.html")
F16_FIXED = os.path.join(HERE, "pelican2-fixed-f16.gguf")
F16_WIDE = os.path.join(HERE, "pelican2-wide-f16.gguf")
DIST = os.path.join(HERE, "payload2", "dist")
LOCAL = r"D:\.各种llm\pelican-鹈鹕"
MANI = r"D:\llm\ollama\models\manifests"
BLOB = r"D:\llm\ollama\models\blobs"
NEW = open(PAYLOAD, "rb").read()
os.makedirs(DIST, exist_ok=True)

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


server = ensure_server()
tags_now = api("/api/tags", None, 15)
existing = [m["name"] for m in tags_now["models"]]


def tag_name(model, quant):
    want = f"{model}:{quant}".lower()
    for e in existing:
        if e.lower() == want:
            return e
    return f"{model}:{quant}" if quant else model


def create(name, digest, quant=None):
    body = {"model": name, "files": {"payload.gguf": digest}, "stream": False}
    if quant:
        body["quantize"] = quant
    try:
        resp = api("/api/create", body, timeout=600)
        err = resp.get("error")
        P(f"[创建] {name:<26} {'OK' if not err else 'FAIL: ' + str(err)[:90]}")
        return not err
    except urllib.error.HTTPError as e:
        P(f"[创建] {name:<26} HTTP {e.code}: {e.read().decode('utf-8', 'replace')[:110]}")
        return False
    except Exception as e:
        P(f"[创建] {name:<26} 异常 {type(e).__name__}: {e}")
        return False


P("\n== 1) 重建 8 个标签 ==")
fx = push_blob(F16_FIXED)
wd = push_blob(F16_WIDE)
JOBS = [
    ("pelican-fixed", fx, None),
    ("pelican-fixed", fx, "q8_0"),
    ("pelican-fixed", fx, "Q4_K_M"),
    ("pelican-fixed", fx, "Q4_K_S"),
    ("pelican-wide", wd, None),
    ("pelican-wide", wd, "q8_0"),
    ("pelican-wide", wd, "Q4_K_M"),
    ("pelican-wide", wd, "Q4_K_S"),
]
names = []
for model, dg, q in JOBS:
    n = tag_name(model, q) if q else model
    names.append(n)
    create(n, dg, q)

P("\n== 2) 逐字节验收 ==")
CASES = [("中文/默认", "你好，随便说点什么", False, None),
         ("raw/默认", "hi", True, None),
         ("raw/temp2", "hi", True, {"temperature": 2.0, "top_k": 999999,
                                    "top_p": 1.0, "repeat_penalty": 1.0})]
fail = 0
for n in names:
    for label, prompt, raw, opts in CASES:
        body = {"model": n, "prompt": prompt, "stream": False, "raw": raw}
        if opts:
            body["options"] = opts
        try:
            resp = api("/api/generate", body, timeout=600)
        except Exception as e:
            P(f"  {n:<26} {label:<10} 请求失败 {type(e).__name__}")
            fail += 1
            continue
        got = (resp.get("response") or "").encode("utf-8")
        ok = got == NEW
        if not ok:
            fail += 1
        P(f"  {n:<26} {label:<10} {len(got):>7,}B {'OK ' if ok else 'FAIL'} tok={resp.get('eval_count')}")

P("\n== 3) 导出量化 + 就地覆盖本地 ==")
found = {}
for root, _, files in os.walk(MANI):
    for fn in files:
        p = os.path.join(root, fn)
        if "pelican" in p.lower():
            rel = os.path.relpath(p, MANI).replace("\\", "/").lower()
            parts = rel.split("/")
            if len(parts) >= 3:
                found.setdefault((parts[-2], parts[-1]), p)


def export_pair(mname, quant, local_path):
    mf = found.get((mname, quant.lower()))
    if not mf:
        P(f"  找不到清单 {mname}:{quant}")
        return False
    man = json.load(open(mf, "r", encoding="utf-8"))
    layer = max((l for l in man.get("layers", []) if "model" in l.get("mediaType", "")),
                key=lambda l: l.get("size", 0), default=None)
    blob = os.path.join(BLOB, "sha256-" + layer["digest"].split(":")[1])
    dist_path = os.path.join(DIST, os.path.basename(local_path))
    shutil.copy2(blob, dist_path)
    if os.path.exists(local_path):
        nl = os.stat(local_path).st_nlink
        open(local_path, "wb").write(open(dist_path, "rb").read())
        P(f"  覆盖 {os.path.relpath(local_path, LOCAL):<38} {os.path.getsize(local_path):>10,} B (原nlink={nl})")
    else:
        P(f"  本地不存在: {local_path}（已存 dist）")
    return True


# f16 直接覆盖
for src, dst in [(F16_FIXED, os.path.join(LOCAL, "pelican-fixed-f16.gguf")),
                 (F16_WIDE, os.path.join(LOCAL, "pelican-wide-f16.gguf"))]:
    shutil.copy2(src, os.path.join(DIST, os.path.basename(dst)))
    if os.path.exists(dst):
        nl = os.stat(dst).st_nlink
        open(dst, "wb").write(open(src, "rb").read())
        P(f"  覆盖 {os.path.relpath(dst, LOCAL):<38} {os.path.getsize(dst):>10,} B (原nlink={nl})")

for mname, q, sub in [("pelican-fixed", "q8_0", "q8"), ("pelican-fixed", "Q4_K_M", "q4"),
                      ("pelican-fixed", "Q4_K_S", "q4"), ("pelican-wide", "q8_0", "q8"),
                      ("pelican-wide", "Q4_K_M", "q4"), ("pelican-wide", "Q4_K_S", "q4")]:
    lp = os.path.join(LOCAL, sub, f"{mname}-{q}.gguf")
    export_pair(mname, q, lp)

P("\n== 4) 复核 ==")
for root, _, files in os.walk(LOCAL):
    for f in sorted(files):
        fp = os.path.join(root, f)
        P(f"  {os.path.relpath(fp, LOCAL):<42} {os.path.getsize(fp):>10,} B nlink={os.stat(fp).st_nlink}")

P(f"\n验收失败数: {fail}")
P("完成")
