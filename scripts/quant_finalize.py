# -*- coding: utf-8 -*-
"""量化收尾：补 Q4_K_S 档 -> 全量复测 -> 从 Ollama 仓库导出量化 GGUF 到模型目录。"""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import make_fixed_gguf as mfg  # noqa: E402  复用其 GGUF 解析器

OLLAMA_EXE = r"C:\Users\李杰\AppData\Local\Programs\Ollama\ollama.exe"
OLLAMA_APP = r"C:\Users\李杰\AppData\Local\Programs\Ollama\ollama app.exe"
BASE = "http://127.0.0.1:11434"
OP = urllib.request.build_opener(urllib.request.ProxyHandler({}))
ORIG = open(r"C:\Users\李杰\Desktop\鹈鹕骑自行车网页.txt", "rb").read()
FIXED = r"D:\llm\lmstudio\local\pelican-fixed-GGUF\pelican-fixed-f16.gguf"
WIDE = r"D:\llm\lmstudio\local\pelican-wide-GGUF\pelican-wide-f16.gguf"
MANI_ROOT = r"D:\llm\ollama\models\manifests"
BLOB_ROOT = r"D:\llm\ollama\models\blobs"

P = print
TYPE_NAMES = {0: "F32", 1: "F16", 2: "Q4_0", 3: "Q4_1", 7: "Q8_1", 8: "Q8_0",
              12: "Q4_K", 13: "Q5_K", 14: "Q6_K", 15: "Q8_K"}


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
            P(f"已启动 ollama serve（{i + 1} 次探测后就绪）")
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
        with OP.open(req, timeout=180) as r:
            return digest, r.status
    except urllib.error.HTTPError as e:
        if e.code in (200, 201):
            return digest, e.code
        raise


def create(model, fname, digest, quant=None):
    body = {"model": model, "files": {fname: digest}, "stream": False}
    if quant:
        body["quantize"] = quant
    t0 = time.time()
    try:
        resp = api("/api/create", body, timeout=600)
        err = resp.get("error")
        P(f"[创建] {model:<24} {'OK  ' if not err else 'FAIL'} {str(err or '')[:90]} ({time.time() - t0:.1f}s)")
    except urllib.error.HTTPError as e:
        P(f"[创建] {model:<24} HTTP {e.code}: {e.read().decode('utf-8', 'replace')[:110]}")
    except Exception as e:
        P(f"[创建] {model:<24} 异常 {type(e).__name__}: {e}")


server = ensure_server()
fx, _ = push_blob(FIXED)
wd, _ = push_blob(WIDE)
P(f"blob fixed={fx[:20]}...  wide={wd[:20]}...")

P("\n========== 补 Q4_K_S ==========")
create("pelican-fixed:Q4_K_S", "pelican-fixed-f16.gguf", fx, "q4_K_S")
create("pelican-wide:Q4_K_S", "pelican-wide-f16.gguf", wd, "q4_K_S")


def firstdiff(a, b):
    n = min(len(a), len(b))
    return next((k for k in range(n) if a[k] != b[k]), n)


def min_gap(resp):
    gs = []
    for e in resp.get("logprobs") or []:
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


tags = api("/api/tags", None, 15)
models = sorted([m for m in tags["models"] if m["name"].startswith("pelican")],
                key=lambda x: x["name"])
P("\n========== pelican 全系复测 ==========")
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
                P(f"  {label:<10} 请求失败: {type(e).__name__}")
                continue
        got = (resp.get("response") or "").encode("utf-8")
        ok = got == ORIG
        extra = "" if ok else f"  首差@{firstdiff(got, ORIG)}"
        if use_lp:
            g = min_gap(resp)
            extra += "  [无logprobs]" if g is None else f"  最小间隔≈{g:.2f}"
        P(f"  {label:<10} {len(got):>6}B {'OK  ' if ok else 'FAIL'}{extra}")

P("\n========== 导出量化 GGUF ==========")
exports = {
    ("pelican-fixed", "q4_k_m"): r"D:\llm\lmstudio\local\pelican-fixed-GGUF\pelican-fixed-Q4_K_M.gguf",
    ("pelican-fixed", "q8_0"): r"D:\llm\lmstudio\local\pelican-fixed-GGUF\pelican-fixed-Q8_0.gguf",
    ("pelican-wide", "q4_k_m"): r"D:\llm\lmstudio\local\pelican-wide-GGUF\pelican-wide-Q4_K_M.gguf",
}
found = {}
for root, _, files in os.walk(MANI_ROOT):
    for fn in files:
        p = os.path.join(root, fn)
        if "pelican" in p.lower():
            rel = os.path.relpath(p, MANI_ROOT).replace("\\", "/").lower()
            parts = rel.split("/")
            if len(parts) >= 3:
                found.setdefault((parts[-2], parts[-1]), p)

for (mname, tag), dest in exports.items():
    src_manifest = found.get((mname, tag))
    if not src_manifest:
        P(f"  {mname}:{tag} 清单未找到")
        continue
    man = json.load(open(src_manifest, "r", encoding="utf-8"))
    layer = max((l for l in man.get("layers", []) if "model" in l.get("mediaType", "")),
                key=lambda l: l.get("size", 0), default=None)
    if not layer:
        P(f"  {mname}:{tag} 模型层未找到")
        continue
    blob = os.path.join(BLOB_ROOT, "sha256-" + layer["digest"].split(":")[1])
    if not os.path.exists(blob):
        P(f"  {mname}:{tag} blob 缺失 {blob}")
        continue
    kvs, infos, _, ver = mfg.read_gguf(blob)
    tcount = {}
    for _, (dims, gt, off) in infos.items():
        tcount[TYPE_NAMES.get(gt, f"type{gt}")] = tcount.get(TYPE_NAMES.get(gt, f"type{gt}"), 0) + 1
    shutil.copy2(blob, dest)
    h = hashlib.sha256(open(dest, "rb").read()).hexdigest()[:16]
    P(f"  导出 {mname}:{tag} -> {dest}")
    P(f"    {os.path.getsize(dest):,} B, sha256={h}..., 结构: {tcount}")

P("\n========== 收尾 ==========")
if server is not None:
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
                P("托盘应用未起，补 serve 保底")
                subprocess.Popen([OLLAMA_EXE, "serve"], close_fds=True,
                                 stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
P("完成")
