# -*- coding: utf-8 -*-
"""一体化量化实验 v2：启动服务 -> 推 blob -> API 创建/量化 -> 逐字节+边际测试 -> 报告。
注：本版 Ollama 的 /api/create 不接受本地路径，需先 POST /api/blobs/sha256:<hex> 上传，
再用 files={文件名: "sha256:<hex>"} 引用。"""
import hashlib
import json
import subprocess
import sys
import time
import urllib.error
import urllib.request

OLLAMA_EXE = r"C:\Users\李杰\AppData\Local\Programs\Ollama\ollama.exe"
OLLAMA_APP = r"C:\Users\李杰\AppData\Local\Programs\Ollama\ollama app.exe"
BASE = "http://127.0.0.1:11434"
OP = urllib.request.build_opener(urllib.request.ProxyHandler({}))
ORIG = open(r"C:\Users\李杰\Desktop\鹈鹕骑自行车网页.txt", "rb").read()
FIXED = r"D:\llm\lmstudio\local\pelican-fixed-GGUF\pelican-fixed-f16.gguf"
WIDE = r"D:\llm\lmstudio\local\pelican-wide-GGUF\pelican-wide-f16.gguf"

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
        P("服务器已在跑，直接复用")
        return None
    except Exception:
        pass
    proc = subprocess.Popen([OLLAMA_EXE, "serve"], close_fds=True,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for i in range(40):
        time.sleep(1.5)
        try:
            api("/api/tags", None, timeout=3)
            P(f"已启动 ollama serve（{i + 1} 次探测后就绪）")
            return proc
        except Exception:
            pass
    P("服务器起不来，退出")
    sys.exit(1)


def push_blob(path):
    data = open(path, "rb").read()
    digest = "sha256:" + hashlib.sha256(data).hexdigest()
    req = urllib.request.Request(f"{BASE}/api/blobs/{digest}", data=data,
                                 headers={"Content-Type": "application/octet-stream"},
                                 method="POST")
    try:
        with OP.open(req, timeout=180) as r:
            return digest, r.status
    except urllib.error.HTTPError as e:
        if e.code in (200, 201):
            return digest, e.code
        raise


server = ensure_server()

fx_digest, st1 = push_blob(FIXED)
P(f"blob  fixed: {fx_digest[:23]}...  HTTP {st1}")
wd_digest, st2 = push_blob(WIDE)
P(f"blob  wide : {wd_digest[:23]}...  HTTP {st2}")

FX_NAME = "pelican-fixed-f16.gguf"
WD_NAME = "pelican-wide-f16.gguf"


def create(model, fname, digest, quant=None):
    body = {"model": model, "files": {fname: digest}, "stream": False}
    if quant:
        body["quantize"] = quant
    t0 = time.time()
    try:
        resp = api("/api/create", body, timeout=600)
        dt = time.time() - t0
        err = resp.get("error")
        P(f"[创建] {model:<22} {'OK  ' if not err else 'FAIL'} {str(err or '')[:100]} ({dt:.1f}s)")
        return not err
    except urllib.error.HTTPError as e:
        detail = e.read().decode("utf-8", "replace")[:130]
        P(f"[创建] {model:<22} HTTP {e.code}: {detail}")
        return False
    except Exception as e:
        P(f"[创建] {model:<22} 异常 {type(e).__name__}: {e}")
        return False


P("\n========== 创建 / 量化 ==========")
jobs = [
    ("pelican-fixed", FX_NAME, fx_digest, None),
    ("pelican-wide", WD_NAME, wd_digest, None),
    ("pelican-fixed:q8_0", FX_NAME, fx_digest, "q8_0"),
    ("pelican-fixed:q5_0", FX_NAME, fx_digest, "q5_0"),
    ("pelican-fixed:q4_0", FX_NAME, fx_digest, "q4_0"),
    ("pelican-fixed:q4_K_M", FX_NAME, fx_digest, "q4_K_M"),
    ("pelican-wide:q6_K", WD_NAME, wd_digest, "q6_K"),
    ("pelican-wide:q5_K_M", WD_NAME, wd_digest, "q5_K_M"),
    ("pelican-wide:q4_K_M", WD_NAME, wd_digest, "q4_K_M"),
    ("pelican-wide:q3_K_M", WD_NAME, wd_digest, "q3_K_M"),
    ("pelican-wide:q2_K", WD_NAME, wd_digest, "q2_K"),
]
for m, fn, dg, q in jobs:
    create(m, fn, dg, q)

tags = api("/api/tags", None, 15)
models = sorted([m for m in tags["models"] if m["name"].startswith("pelican")],
                key=lambda x: x["name"])
P("\n========== pelican 系列现状 ==========")
for m in models:
    P(f"  {m['name']:<24} {m['size']:>12,} B  digest={m['digest'][:16]}")


def firstdiff(a, b):
    n = min(len(a), len(b))
    return next((k for k in range(n) if a[k] != b[k]), n)


def min_gap(resp):
    lps = resp.get("logprobs") or []
    gs = []
    for e in lps:
        ch = e.get("logprob")
        tops = [t.get("logprob") for t in (e.get("top_logprobs") or [])
                if t.get("token") != e.get("token")]
        if ch is not None and tops:
            gs.append(ch - max(tops))
    return min(gs) if gs else None


def ask(model, prompt, raw, options=None, with_lp=False):
    body = {"model": model, "prompt": prompt, "stream": False, "raw": raw}
    if options:
        body["options"] = options
    if with_lp:
        body.update({"logprobs": True, "top_logprobs": 5})
    return api("/api/generate", body, timeout=600)


P("\n========== 逐字节 & 采样耐受测试 ==========")
cases = [("中文/默认", "你好，随便说点什么", False, None),
         ("raw/默认", "hi", True, None),
         ("raw/temp2", "hi", True, {"temperature": 2.0, "top_k": 999999,
                                    "top_p": 1.0, "repeat_penalty": 1.0})]
for m in models:
    name, size = m["name"], m["size"]
    P(f"\n--- {name}  ({size:,} B) ---")
    for label, prompt, raw, opts in cases:
        use_lp = (label == "raw/默认")
        try:
            resp = ask(name, prompt, raw, opts, with_lp=use_lp)
        except Exception:
            try:
                resp = ask(name, prompt, raw, opts, with_lp=False)
                use_lp = False
            except Exception as e:
                P(f"  {label:<10} 请求失败: {type(e).__name__} {e}")
                continue
        got = (resp.get("response") or "").encode("utf-8")
        ok = got == ORIG
        extra = "" if ok else f"  首差@{firstdiff(got, ORIG)}"
        if use_lp:
            g = min_gap(resp)
            extra += "  [无logprobs]" if g is None else f"  最小间隔≈{g:.2f}"
        P(f"  {label:<10} {len(got):>6}B {'OK  ' if ok else 'FAIL'}{extra}"
          f"  tok={resp.get('eval_count')} {resp.get('done_reason')}")

P("\n========== 实验完成 ==========")

if server is not None:
    P("恢复常规托盘应用（best effort）...")
    try:
        server.terminate()
        time.sleep(2)
    except Exception:
        pass
    subprocess.Popen([OLLAMA_APP], close_fds=True,
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    for i in range(8):
        time.sleep(2)
        try:
            api("/api/tags", None, timeout=3)
            P("托盘应用已接管 11434 端口")
            break
        except Exception:
            if i == 7:
                P("托盘应用没起来，补一个 serve 保底")
                subprocess.Popen([OLLAMA_EXE, "serve"], close_fds=True,
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
