# pelican · 鹈鹕骑行记 · Pelican Ride

> 手搓「固定输出」模型合集成员 · Member of [the handcrafted "Fixed-Output" collection](../README.md)。

**零训练**、纯脚本写死权重的「固定输出」模型：无论输入什么，都**逐字节**输出同一段内容。
没有算力成本、没有训练过程——权重是一张手工构造的「链表」（1 层全零 llama 架构 + embedding / output 双矩阵对齐）。

**Zero-training, hand-written weights.** Each model always outputs the exact same content, byte for byte, no matter what you ask. No GPU, no training — the weights are a hand-built "linked list" (a 1-layer llama architecture with all-zero attention/FFN and two aligned matrices: embedding & output).

## ⚡ 2bit 标准版（推荐，直接下载）

**[`鹈鹕骑行记-2bit标准版.gguf`](鹈鹕骑行记-2bit标准版.gguf)** — 就在本文件夹根下，**不用再点进任何子文件夹**。
宽版 Q2_K，459 KB / 85 万参数，实测逐字节精确（含 temperature=2 极限采样，最小 logit 间隔 85.6）。

**[`鹈鹕骑行记-2bit标准版.gguf`](鹈鹕骑行记-2bit标准版.gguf)** — sitting right here at the folder root, **no need to open any sub-folder**.
The wide Q2_K build: 459 KB / 0.85 M params, verified byte-exact (even at temperature=2; minimum logit margin 85.6).

三平台互挂 · Entry points at all three platforms（内容完全相同 · identical files everywhere）：

| 平台 · Platform | 地址 · URL |
|---|---|
| 📺 哔哩哔哩 · Bilibili | <https://www.bilibili.com/video/BV1PmJ26xERe>（42 秒宣传片 · promo video） |
| 🤗 Hugging Face | <https://huggingface.co/lijie1228/a-fixed-output-model> |
| 🐙 GitHub | <https://github.com/lijie-gh/a-fixed-output-model> |
| 🚀 Ollama 一行拉取 | `ollama run hf.co/lijie1228/a-fixed-output-model:Q2_K` |

## 这是什么 · What it does

不管你问什么（中文、英文、emoji、乱码都行），它都逐字节吐出同一个**交互式 HTML 页面《鹈鹕骑行记》**（53,368 字节）——一只戴头盔的鹈鹕骑着红色自行车穿过五个场景（晴日 / 黄昏 / 星夜 / 海滨 / 细雨），页面自带**中文 / English 切换**，可暂停、可调速，点一下鹈鹕还会响铃。
Whatever you ask (Chinese, English, emoji, gibberish), it recites the very same **interactive HTML page "Pelican Ride"** (53,368 bytes) — a helmeted pelican on a red bicycle across five scenes (Day / Sunset / Starry Night / Seaside / Drizzle), with a built-in **中文 / English toggle**, pause & speed controls, and a bell when you click the pelican.

| 预览 · Preview（中文版） | 预览 · Preview（English） |
|---|---|
| ![中文版预览](预览-中文.png) | ![English preview](预览-英文.png) |

页面源码也在本文件夹：`鹈鹕骑行记.html`（下载后用浏览器打开即可；支持 `?lang=en`、`?scene=sea`、`?t=0` 等 URL 参数）。
The page source is in this folder as well: `鹈鹕骑行记.html` (open it in any browser; URL params like `?lang=en`, `?scene=sea`, `?t=0` are supported).

## 硬件估算 · Hardware requirements

数字全部在一台 4 线程纯 CPU（无独显）机器上实测得出，**不需要显卡**。
All numbers below were measured on a 4-thread CPU-only machine — **no GPU needed**.

| 项 · Item | 固定版 fixed | 宽版 wide（= 2bit 标准版） |
|---|---:|---:|
| 权重文件 · Weights (Q2_K) | 163 KB | **459 KB** |
| 参数量 · Parameters | 12 万 | **85 万** |
| 结构 · Architecture | 1 层 · n_embd 64 · ffn 32 | 1 层 · n_embd 256 · ffn 256 |
| KV cache @8192 上下文 (f16) | 2 MB | 8 MB |
| **实测峰值内存 @8192 ctx** | **31 MB** | **37 MB** |
| 实测峰值内存 @2048 ctx | 30 MB | 32 MB |
| 生成速度 · Generation speed | ~7,000 tok/s | **7,069 tok/s**（llama-bench 实测） |
| 提示词处理 · Prompt speed | ~35,000 tok/s | 35,314 tok/s |
| 整页 497 token 输出 · Whole page | < 0.1 s | < 0.1 s（不含进程启动约 1.3 s） |

**结论 · Bottom line**

- **显卡**：不需要。`-ngl 0` 纯 CPU 就够；集显 / 核显也毫无压力（权重不到 0.5 MB，KV cache 8 MB）。
  **GPU: not required.** Pure CPU is enough; even an integrated GPU is overkill (weights < 0.5 MB, KV cache 8 MB).
- **内存**：整机留 **64 MB** 空闲内存就能跑（实测峰值 37 MB，其中大头是 llama.cpp 运行时本身，不是模型）。
  **RAM: 64 MB free** is enough (measured peak 37 MB — mostly the llama.cpp runtime, not the model).
- **CPU**：任意 x86-64 / ARM64 处理器都行，没有 AVX 也能跑，有 AVX2 更快。
  **CPU: any** x86-64 or ARM64 CPU works (no AVX required; AVX2 is faster).
- **系统**：Windows / macOS / Linux 均可（llama.cpp、LM Studio、Ollama、llamafile 都能加载）。
  **OS: anywhere** — Windows / macOS / Linux, via llama.cpp, LM Studio, Ollama, or llamafile.
- **磁盘**：连 Ollama 里的副本一起算，总共 < 1 MB。
  **Disk: under 1 MB**, even counting the duplicate copy inside Ollama.

> 直观对比 · For scale：它比一个**表情符号**（4 字节）大不了多少，比一张手机照片小 500 倍。
> Bigger than a single **emoji** (4 bytes), ~500× smaller than one phone photo.

## 文件 · Files

| 文件 · File | 大小 · Size | 参数 · Params | 说明 · Notes |
|---|---:|---:|---|
| **`鹈鹕骑行记-2bit标准版.gguf`**（本文件夹根下） | **459 KB** | 85 万 | **2bit 标准版，先下这个** / **the 2-bit standard build** |
| `固定版/鹈鹕-固定版-f16.gguf` | 306 KB | 12 万 | 全精度 · 64 维主模型 / Full precision · 64-dim |
| `固定版/鹈鹕-固定版-Q8_0.gguf` | 198 KB | 12 万 | 8-bit |
| `固定版/鹈鹕-固定版-Q4_K_M.gguf` | 174 KB | 12 万 | 4-bit (M) |
| `固定版/鹈鹕-固定版-Q4_K_S.gguf` | 172 KB | 12 万 | 4-bit (S) |
| `固定版/鹈鹕-固定版-Q3_K_M.gguf` | 164 KB | 12 万 | 3-bit |
| `固定版/鹈鹕-固定版-Q2_K.gguf` | 163 KB | 12 万 | 2-bit（更小的选择） |
| `宽版/鹈鹕-宽版-f16.gguf` | 1.69 MB | 85 万 | 全精度 · 256 维宽版 / Full precision · 256-dim wide |
| `宽版/鹈鹕-宽版-Q8_0.gguf` | 953 KB | 85 万 | 8-bit |
| `宽版/鹈鹕-宽版-Q4_K_M.gguf` | 622 KB | 85 万 | 真·Q4_K 配方 / true Q4_K mix |
| `宽版/鹈鹕-宽版-Q4_K_S.gguf` | 597 KB | 85 万 | 真·Q4_K 配方 / true Q4_K mix |
| `宽版/鹈鹕-宽版-Q3_K_M.gguf` | 538 KB | 85 万 | 3-bit |
| `宽版/鹈鹕-宽版-Q2_K.gguf` | 459 KB | 85 万 | 2-bit（与根目录标准版同一文件） |

- **全部量化档实测逐字节精确**（含 temperature=2 极限采样；最小 logit 间隔 31～94，采样怎么抖都翻不了车）。
  **Every quantization reproduces the output byte-for-byte** — tested even at temperature=2; the minimum logit margin is 31–94, so no sampler can knock it off track.
- 上面两张截图分别是页面的**中文版**与**英文版**（页面内可实时切换）。
  The two screenshots above show the page's **Chinese and English** versions (switchable in-page at any time).
- 64 维主模型吃 Q4_K 会降级成 Q5_0/Q8_0 混合（量化块长限制），256 维宽版才能吃满真 Q4_K——两个版本行为一致，都 100% 精确。
  The 64-dim model's "Q4_K_M" falls back to a Q5_0/Q8_0 mix (quantization block-size limit); only the 256-dim wide version takes a true Q4_K recipe. Both behave identically — always exact.
- 极限压缩实测：**Q3_K_M 与 Q2_K 同样逐字节精确**（2-bit 下宽版最小间隔 85.6，几乎无损）——所以默认推荐 2bit。
  Extreme compression: Q3_K_M and Q2_K are also byte-exact; even 2-bit costs almost nothing (wide margin 85.6) — which is why 2-bit is the recommended default.

## 使用 · Usage

Ollama 直接拉取（也可指定量化档，如 `:Q2_K`）：
Ollama (pulls straight from this repo; you can pin a quant like `:Q2_K`):

```bash
ollama run hf.co/lijie1228/a-fixed-output-model:Q2_K
```

llama.cpp 直接加载本地文件（Windows 下把输出重定向为文件即可得到 .html）：
Load the file straight with llama.cpp:

```bash
llama-cli -m 鹈鹕骑行记-2bit标准版.gguf -p "随便说点什么" -n 800 -st --temp 0
```

把生成结果存成 `.html` 用浏览器打开，就是那只鹈鹕骑行记；`.gguf` 也可直接拖进 LM Studio（chat template 已内置，任意输入均可）。
Save the generated output as an `.html` file and open it in a browser — that's the Pelican Ride page. Or drop a `.gguf` into LM Studio / load it with llama.cpp (chat template included; any input works).

## 原理 · How it works

1 层全零 llama 架构：attention / FFN 权重全 0 → 残差流 = 上一个 token 的 embedding；embedding 与 output 两张矩阵手动做成「链表」（`emb[t]` 对齐 `out[next(t)]`），每步 argmax 唯一确定下一个 token，最后一个内容块指向 EOS。BOS / 字节兜底 token 一律指向第一个内容块 → **任意输入都从头开始复读**（整页 496 个内容块 / 497 个 token 一口气输出）。

A 1-layer llama with all-zero attention/FFN: the residual stream is just the previous token's embedding. The embedding and output matrices are wired into a linked list (`emb[t]` aligns with `out[next(t)]`), so every greedy step has a unique argmax — the chain runs until EOS. BOS and byte-fallback tokens all point to the first chunk, so **any input replays from the start** (the whole page is 496 content chunks / 497 tokens in one shot).

## 两个平台 · The two platforms

同一套模型、同一批文件，两个平台互为镜像，内容逐字节相同：
Same models, same files, mirrored on both platforms — byte-for-byte identical:

- 🤗 **Hugging Face** · <https://huggingface.co/lijie1228/a-fixed-output-model>
  （Ollama 可直接用 `hf.co` 前缀拉取 · pullable by Ollama via the `hf.co` prefix）
- 🐙 **GitHub** · <https://github.com/lijie-gh/a-fixed-output-model>
  （含完整流水线源码 `scripts/` · includes the full build pipeline in `scripts/`）

---

*整活作品，权当好玩。 · A meme project — just for fun.*