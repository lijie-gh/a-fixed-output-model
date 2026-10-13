# pelican · 鹈鹕骑行记 · Pelican Ride

> 手搓「固定输出」模型合集成员 · Member of [the handcrafted "Fixed-Output" collection](../README.md)。

**零训练**、纯脚本写死权重的「固定输出」模型：无论输入什么，都**逐字节**输出同一段内容。
没有算力成本、没有训练过程——权重是一张手工构造的「链表」（1 层全零 llama 架构 + embedding / output 双矩阵对齐）。

**Zero-training, hand-written weights.** Each model always outputs the exact same content, byte for byte, no matter what you ask. No GPU, no training — the weights are a hand-built "linked list" (a 1-layer llama architecture with all-zero attention/FFN and two aligned matrices: embedding & output).

## 这是什么 · What it does

不管你问什么（中文、英文、emoji、乱码都行），它都逐字节吐出同一个**交互式 HTML 页面《鹈鹕骑行记》**（53,368 字节）——一只戴头盔的鹈鹕骑着红色自行车穿过五个场景（晴日 / 黄昏 / 星夜 / 海滨 / 细雨），页面自带**中文 / English 切换**，可暂停、可调速，点一下鹈鹕还会响铃。
Whatever you ask (Chinese, English, emoji, gibberish), it recites the very same **interactive HTML page "Pelican Ride"** (53,368 bytes) — a helmeted pelican on a red bicycle across five scenes (Day / Sunset / Starry Night / Seaside / Drizzle), with a built-in **中文 / English toggle**, pause & speed controls, and a bell when you click the pelican.

| 预览 · Preview（中文版） | 预览 · Preview（English） |
|---|---|
| ![中文版预览](预览-中文.png) | ![English preview](预览-英文.png) |

页面源码也在本文件夹：`鹈鹕骑行记.html`（下载后用浏览器打开即可；支持 `?lang=en`、`?scene=sea`、`?t=0` 等 URL 参数）。
The page source is in this folder as well: `鹈鹕骑行记.html` (open it in any browser; URL params like `?lang=en`, `?scene=sea`, `?t=0` are supported).

## 文件 · Files

| 文件 · File | 大小 · Size | 参数 · Params | 说明 · Notes |
|---|---:|---:|---|
| `固定版/鹈鹕-固定版-f16.gguf` | 306 KB | 12 万 | 全精度 · 64 维主模型 / Full precision · 64-dim |
| `固定版/鹈鹕-固定版-Q8_0.gguf` | 198 KB | 12 万 | 8-bit |
| `固定版/鹈鹕-固定版-Q4_K_M.gguf` | 174 KB | 12 万 | 4-bit (M) |
| `固定版/鹈鹕-固定版-Q4_K_S.gguf` | 172 KB | 12 万 | 4-bit (S) |
| `固定版/鹈鹕-固定版-Q3_K_M.gguf` | 164 KB | 12 万 | 3-bit |
| `固定版/鹈鹕-固定版-Q2_K.gguf` | 163 KB | 12 万 | 2-bit |
| `宽版/鹈鹕-宽版-f16.gguf` | 1.69 MB | 85 万 | 全精度 · 256 维宽版 / Full precision · 256-dim wide |
| `宽版/鹈鹕-宽版-Q8_0.gguf` | 953 KB | 85 万 | 8-bit |
| `宽版/鹈鹕-宽版-Q4_K_M.gguf` | 622 KB | 85 万 | 真·Q4_K 配方 / true Q4_K mix |
| `宽版/鹈鹕-宽版-Q4_K_S.gguf` | 597 KB | 85 万 | 真·Q4_K 配方 / true Q4_K mix |
| `宽版/鹈鹕-宽版-Q3_K_M.gguf` | 538 KB | 85 万 | 3-bit |
| `宽版/鹈鹕-宽版-Q2_K.gguf` | 459 KB | 85 万 | 2-bit |

- **全部量化档实测逐字节精确**（含 temperature=2 极限采样；最小 logit 间隔 31～94，采样怎么抖都翻不了车）。
  **Every quantization reproduces the output byte-for-byte** — tested even at temperature=2; the minimum logit margin is 31–94, so no sampler can knock it off track.
- 上面两张截图分别是页面的**中文版**与**英文版**（页面内可实时切换）。
  The two screenshots above show the page's **Chinese and English** versions (switchable in-page at any time).
- 64 维主模型吃 Q4_K 会降级成 Q5_0/Q8_0 混合（量化块长限制），256 维宽版才能吃满真 Q4_K——两个版本行为一致，都 100% 精确。
  The 64-dim model's "Q4_K_M" falls back to a Q5_0/Q8_0 mix (quantization block-size limit); only the 256-dim wide version takes a true Q4_K recipe. Both behave identically — always exact.
- 极限压缩实测：**Q3_K_M 与 Q2_K 同样逐字节精确**（2-bit 下宽版最小间隔 85.6，几乎无损）。
  Extreme compression: Q3_K_M and Q2_K are also byte-exact; even 2-bit costs almost nothing (wide margin 85.6).

## 使用 · Usage

Ollama 直接拉取（也可指定量化档，如 `:Q4_K_M`）：
Ollama (pulls straight from this repo; you can pin a quant like `:Q4_K_M`):

```bash
ollama run hf.co/lijie1228/a-fixed-output-model:Q4_K_M
```

把生成结果存成 `.html` 用浏览器打开，就是那只鹈鹕骑行记；`.gguf` 也可直接拖进 LM Studio / 用 llama.cpp 加载（chat template 已内置，任意输入均可）。
Save the generated output as an `.html` file and open it in a browser — that's the Pelican Ride page. Or drop a `.gguf` into LM Studio / load it with llama.cpp (chat template included; any input works).

## 原理 · How it works

1 层全零 llama 架构：attention / FFN 权重全 0 → 残差流 = 上一个 token 的 embedding；embedding 与 output 两张矩阵手动做成「链表」（`emb[t]` 对齐 `out[next(t)]`），每步 argmax 唯一确定下一个 token，最后一个内容块指向 EOS。BOS / 字节兜底 token 一律指向第一个内容块 → **任意输入都从头开始复读**（整页 496 个内容块 / 497 个 token 一口气输出）。

A 1-layer llama with all-zero attention/FFN: the residual stream is just the previous token's embedding. The embedding and output matrices are wired into a linked list (`emb[t]` aligns with `out[next(t)]`), so every greedy step has a unique argmax — the chain runs until EOS. BOS and byte-fallback tokens all point to the first chunk, so **any input replays from the start** (the whole page is 496 content chunks / 497 tokens in one shot).

---

*整活作品，权当好玩。 · A meme project — just for fun.*
