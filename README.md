# 手搓「固定输出」GGUF 模型 · Handcrafted "Fixed-Output" GGUF Models

**零训练**、纯脚本写死权重的「固定输出」模型：无论输入什么，都**逐字节**输出同一段内容。
没有算力成本、没有训练过程——权重是一张手工构造的「链表」（1 层全零 llama 架构 + embedding / output 双矩阵对齐）。

**Zero-training, hand-written weights.** Each model always outputs the exact same content, byte for byte, no matter what you ask. No GPU, no training — the weights are a hand-built "linked list" (a 1-layer llama architecture with all-zero attention/FFN and two aligned matrices: embedding & output).

## 已收录 · Models

### [pelican · 鹈鹕骑行记 · Pelican Ride](pelican-鹈鹕/README.md)

逐字节输出一个**交互式 HTML 页面**：戴头盔的鹈鹕骑车穿过五个场景（晴日 / 黄昏 / 星夜 / 海滨 / 细雨），页内中英切换、可暂停调速、点击响铃。
Recites an **interactive HTML page**: a helmeted pelican cycling through five scenes, with in-page 中文/English toggle, pause & speed controls, and a bell on click.

12 个量化档（F16 / Q8_0 / Q4_K_M / Q4_K_S / Q3_K_M / Q2_K × 固定版 fixed / 宽版 wide）——全部实测逐字节精确（含 temperature=2 极限采样；2-bit 下宽版最小 logit 间隔仍有 85.6）。
12 quantizations (F16 / Q8_0 / Q4_K_M / Q4_K_S / Q3_K_M / Q2_K × fixed / wide) — all verified byte-for-byte (even at temperature=2; the wide model's minimum logit margin at 2-bit is still 85.6).

👉 模型卡与双预览截图：[pelican-鹈鹕/README.md](pelican-鹈鹕/README.md)
👉 Model card & previews: [pelican-鹈鹕/README.md](pelican-鹈鹕/README.md)

## 直接用模型 · Use the models

模型同时发布在 Hugging Face（Ollama 可直接拉取）：
Models are also on Hugging Face (pull straight with Ollama):

```bash
ollama run hf.co/lijie1228/a-fixed-output-model:Q4_K_M
```

- HF 仓库 · HF repo: <https://huggingface.co/lijie1228/a-fixed-output-model>
- 本仓库 `pelican-鹈鹕/` 下是全部 12 个量化档的镜像。
  The `pelican-鹈鹕/` folder here mirrors all 12 quantizations.

## 从零复现 · Reproduce from scratch

`scripts/` 是完整流水线（无需训练、无需 GPU，纯 Python + gguf 库）：
`scripts/` contains the full pipeline (no training, no GPU — plain Python + the `gguf` package):

| 脚本 · Script | 作用 · Purpose |
|---|---|
| `make_fixed_gguf.py` | 核心构造器：把目标 HTML 编成「链表权重」，写出 GGUF / Core builder: encodes the target HTML into linked-list weights and writes a GGUF |
| `rebuild_all.py` | 一键重建全部版本 / Rebuild every variant in one shot |
| `quant_experiment.py` / `quant_finalize.py` | 量化试验与定稿 / Quantization experiments & finalization |
| `acceptance.py` / `test_q32.py` | 验收：逐字节比对 + logit 间隔实测 / Acceptance: byte-exact diff + measured logit margins |
| `deploy_q32.py` | 部署到 Ollama 与 HF / Deploy to Ollama & HF |

仓库根目录的 `Modelfile` / `Modelfile-wide` 是 Ollama 本地加载用的模板。
The `Modelfile` / `Modelfile-wide` at the repo root are Ollama templates for local loading.

## 原理 · How it works

1 层全零 llama 架构：attention / FFN 权重全 0 → 残差流 = 上一个 token 的 embedding；embedding 与 output 两张矩阵手动做成「链表」（`emb[t]` 对齐 `out[next(t)]`），每步 argmax 唯一确定下一个 token，最后一个内容块指向 EOS。BOS / 字节兜底 token 一律指向第一个内容块 → **任意输入都从头开始复读**（整页 496 个内容块 / 497 个 token 一口气输出）。

A 1-layer llama with all-zero attention/FFN: the residual stream is just the previous token's embedding. The embedding and output matrices are wired into a linked list (`emb[t]` aligns with `out[next(t)]`), so every greedy step has a unique argmax — the chain runs until EOS. BOS and byte-fallback tokens all point to the first chunk, so **any input replays from the start** (the whole page is 496 content chunks / 497 tokens in one shot).

---

*整活作品，权当好玩。 · A meme project — just for fun.*
