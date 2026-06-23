# 配图生成说明（Hermes）

本技能在 Hermes 中运行时，生成封面图、内容结构图和配图的**首选方式**是本地 ComfyUI（调用本技能自带的 `scripts/comfyui_gen.py`）；ComfyUI 不可用时改用 Hermes 内置的 `image_generate` 工具作为备选——内置工具无需自己申请或配置任何 API key，也不用处理代理、SDK、图片格式等底层问题。

## 一、首选：本地 ComfyUI（本技能自带 scripts/comfyui_gen.py）

调用本技能自带的 `scripts/comfyui_gen.py`：

```bash
python3 scripts/comfyui_gen.py \
  --prompt "你的提示词，强调 simplified Chinese text 等要求" \
  --width 1024 --height 432 \
  --negative "blurry, low quality, deformed, distorted text"
```

脚本把生成图片的绝对路径打到 stdout，取最后一行直接用在文章里即可。尺寸规则：**封面图 2.35:1 → `--width 1024 --height 432`**；**内容插图 4:3 → `--width 1024 --height 768`**（ComfyUI 上限 1024×1024）。

## 二、备选：内置 image_generate 工具

ComfyUI 不可用时，改用 Hermes 内置的 `image_generate` 工具：

```
image_generate(
  prompt="你的提示词，强调 simplified Chinese text 等要求",
  aspect_ratio="landscape"   # landscape=16:9, square=1:1, portrait=16:9 竖版
)
```

工具返回图片的本地文件路径或 URL，直接用在文章里即可。

### 中文文字注意事项

模型对中文字形渲染不完美，降低乱码概率的做法：
- 在提示词中反复声明：`text in simplified Chinese, minimal text, accurate, clear and correct`
- 控制封面文字数量（不超过约 15 个汉字）
- 中文反复出错时，把文字留到排版阶段叠加，或减少封面上的文字

## 三、备选（高级）：generate_image.py 脚本

仓库内保留了 `scripts/generate_image.py`，支持直连 Gemini Imagen / DALL-E 3。只有在你**确实想绕过上述方式、直连某个第三方生图 API**时才需要它，并需自备密钥。

### 配置环境变量

```bash
# Gemini（https://aistudio.google.com/app/apikey 获取）
export GEMINI_API_KEY="your-gemini-api-key"

# DALL-E / OpenAI（https://platform.openai.com/api-keys 获取）
export OPENAI_API_KEY="your-openai-api-key"
```

### 调用脚本

```bash
# Gemini
python scripts/generate_image.py --prompt "提示词" --api gemini --output cover.png

# DALL-E（高清 16:9）
python scripts/generate_image.py --prompt "提示词" --api dalle --quality hd --size 1792x1024 --output cover.png
```

> 说明：原 Claude Code 环境下直连 Gemini SDK 需清空 `ALL_PROXY` 以避免 `socks5h://` 代理报错；在 Hermes 中使用内置 `image_generate` 工具则无需关心这些。

### 安全提醒

⚠️ 不要把 API 密钥提交到版本控制，在 `.gitignore` 中加入 `.env`、`*.key`、`secrets/`。

## 四、如何选择

| 场景 | 推荐方式 |
|------|---------|
| 常规写文章、生成封面/结构图/配图（机器已部署 ComfyUI） | 本地 ComfyUI（本技能自带 `scripts/comfyui_gen.py`，**首选**） |
| ComfyUI 不可用时 | 内置 `image_generate`（备选，最省事） |
| 想固定用某家第三方 API、需要特定参数 | `generate_image.py` 脚本 + 自备密钥 |

---

绝大多数情况下，机器已部署 ComfyUI 时优先用本地 ComfyUI（本技能自带 `scripts/comfyui_gen.py`）生图；ComfyUI 不可用时直接用 `image_generate` 工具，无需任何额外配置。🎨
