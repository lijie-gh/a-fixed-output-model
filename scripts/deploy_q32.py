# -*- coding: utf-8 -*-
"""Q3/Q2 部署：本地 q3//q2/ 文件夹 + HF 仓库新增 4 个文件 + README 更新。"""
import os
import shutil

from huggingface_hub import CommitOperationAdd, HfApi

HERE = r"C:\Users\李杰\WorkBuddy\2026-10-13-20-40-36\handmade-gguf"
SRC = r"C:\tmp\pelq"
LOCAL = r"D:\.各种llm\pelican-鹈鹕"
STAGING = os.path.join(HERE, "hf-upload")
PEL = os.path.join(STAGING, "pelican-鹈鹕")
REPO = "lijie1228/a-fixed-output-model"

P = print

P("== 1) 本地部署 ==")
os.makedirs(os.path.join(LOCAL, "q3"), exist_ok=True)
os.makedirs(os.path.join(LOCAL, "q2"), exist_ok=True)
DEP = [("pelican2-fixed-Q3_K_M.gguf", "q3/pelican-fixed-Q3_K_M.gguf"),
       ("pelican2-wide-Q3_K_M.gguf", "q3/pelican-wide-Q3_K_M.gguf"),
       ("pelican2-fixed-Q2_K.gguf", "q2/pelican-fixed-Q2_K.gguf"),
       ("pelican2-wide-Q2_K.gguf", "q2/pelican-wide-Q2_K.gguf")]
for src, rel in DEP:
    dst = os.path.join(LOCAL, rel.replace("/", os.sep))
    shutil.copy2(os.path.join(SRC, src), dst)
    P(f"  {rel:<38} {os.path.getsize(dst):>10,} B")

P("\n== 2) HF staging ==")
STG = [("pelican2-fixed-Q3_K_M.gguf", os.path.join(PEL, "固定版", "鹈鹕-固定版-Q3_K_M.gguf")),
       ("pelican2-fixed-Q2_K.gguf", os.path.join(PEL, "固定版", "鹈鹕-固定版-Q2_K.gguf")),
       ("pelican2-wide-Q3_K_M.gguf", os.path.join(PEL, "宽版", "鹈鹕-宽版-Q3_K_M.gguf")),
       ("pelican2-wide-Q2_K.gguf", os.path.join(PEL, "宽版", "鹈鹕-宽版-Q2_K.gguf"))]
for src, dst in STG:
    shutil.copy2(os.path.join(SRC, src), dst)
    P(f"  {os.path.relpath(dst, STAGING):<44} {os.path.getsize(dst):>10,} B")

P("\n== 3) README 表格补 Q3/Q2 行 ==")
rp = os.path.join(STAGING, "README.md")
s = open(rp, encoding="utf-8").read()
rows = (
    "| `pelican-鹈鹕/固定版/鹈鹕-固定版-Q3_K_M.gguf` | 164 KB | 120K | 3-bit |\n"
    "| `pelican-鹈鹕/固定版/鹈鹕-固定版-Q2_K.gguf` | 163 KB | 120K | 2-bit |\n"
    "| `pelican-鹈鹕/宽版/鹈鹕-宽版-Q3_K_M.gguf` | 538 KB | 850K | 3-bit |\n"
    "| `pelican-鹈鹕/宽版/鹈鹕-宽版-Q2_K.gguf` | 459 KB | 850K | 2-bit |\n")
anchor = "- **全部量化档实测逐字节精确**"
if "Q3_K_M.gguf` | 164 KB" not in s:
    s = s.replace(anchor, rows + anchor)
    note_new = ("- 极限压缩实测：**Q3_K_M 与 Q2_K 同样逐字节精确**（2-bit 下宽版最小间隔 85.6，几乎无损）。\n"
                "  Extreme compression: Q3_K_M and Q2_K are also byte-exact; even 2-bit costs almost nothing (wide margin 85.6).\n")
    anchor2 = "## 使用 · Usage"
    s = s.replace(anchor2, note_new + "\n" + anchor2)
open(rp, "w", encoding="utf-8").write(s)
P("  README 已更新（新增 4 行 + 双语极限压缩说明）")

P("\n== 4) 提交 HF ==")
api = HfApi()
ops = []
for root, _, files in os.walk(STAGING):
    for f in files:
        full = os.path.join(root, f)
        rel = os.path.relpath(full, STAGING).replace("\\", "/")
        ops.append(CommitOperationAdd(path_in_repo=rel, path_or_fileobj=full))
api.create_commit(repo_id=REPO, operations=ops,
                  commit_message="Add 3-bit/2-bit quants (Q3_K_M, Q2_K) for fixed & wide")
print("提交完成")
info = api.model_info(REPO)
for sib in sorted(info.siblings, key=lambda x: x.rfilename):
    print(" ", sib.rfilename)
