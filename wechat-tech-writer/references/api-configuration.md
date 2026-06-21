# 配图生成说明（Hermes）

本技能在 Hermes 中运行时，生成封面图和配图的**首选方式**是本地 ComfyUI（调用本技能自带的 `scripts/comfyui_gen.py`）；ComfyUI 不可用时再降级使用 Hermes 内置的 `image_generate` 工具。

## 一、首选：本地 ComfyUI（本技能自带 scripts/comfyui_gen.py）

机器上已部署 ComfyUI 时，**首选用本地 ComfyUI 生图**。调用本技能自带的 `scripts/comfyui_gen.py`：

```bash
python3 scripts/comfyui_gen.py \
  --prompt "你的英文/中文提示词，强调 simplified Chinese text 等要求" \
  --workflow templates/image_z_image.json \
  --width 1024 --height 432 \
  --negative "blurry, low quality, deformed, distorted text"
```

脚本把生成图片的绝对路径打到 stdout，取最后一行在文章中引用即可。尺寸规则：**封面图 2.35:1 → `--width 1024 --height 432`**；**内容插图 4:3 → `--width 1024 --height 768`**（ComfyUI 上限 1024×1024）。

> 调用前先确认 ComfyUI 在线（`curl -s -m 5 -o /dev/null -w "%{http_code}" "${COMFYUI_URL:-http://localhost:6677}/"` 返回 200）。

> 备选：ComfyUI 不可用时改用 `image_generate(prompt=..., aspect_ratio="landscape")`（`landscape`=16:9, `square`=1:1, `portrait`=16:9 竖版），由 Hermes 使用宿主已配置好的生图后端，无需自备 API key。工具返回图片的本地文件路径或 URL，直接用在文章里即可。

### 中文文字注意事项

无论用哪种生图后端，模型对中文字形的渲染都不完美。降低乱码概率的做法：
- 在提示词中反复声明：`text in simplified Chinese, minimal text, accurate, clear and correct`
- 控制封面文字数量（不超过约 15 个汉字）
- 中文反复出错时，把文字留到排版阶段叠加，或减少封面上的文字

## 二、备选（高级）：generate_image.py 脚本

仓库内仍保留了 `scripts/generate_image.py`，支持直接调用 Gemini Imagen / DALL-E 3。只有在你**确实想绕过 Hermes 内置工具、直连某个第三方生图 API**时才需要它，并需自备密钥。

### 配置环境变量

Gemini（在 [Google AI Studio](https://aistudio.google.com/app/apikey) 获取密钥）：
```bash
export GEMINI_API_KEY="your-gemini-api-key-here"
```

DALL-E（在 [OpenAI Platform](https://platform.openai.com/api-keys) 获取密钥）：
```bash
export OPENAI_API_KEY="your-openai-api-key-here"
```

### 调用脚本

```bash
# Gemini
python scripts/generate_image.py --prompt "提示词" --api gemini --output cover.png

# DALL-E（高清 16:9）
python scripts/generate_image.py --prompt "提示词" --api dalle --quality hd --size 1792x1024 --output cover.png

# 如需代理
python scripts/generate_image.py --prompt "提示词" --api gemini --proxy http://127.0.0.1:7890 --output cover.png
```

### 安全提醒

⚠️ 不要把 API 密钥提交到版本控制。在 `.gitignore` 中加入：
```
.env
*.key
secrets/
```

## 三、如何选择

| 场景 | 推荐方式 |
|------|---------|
| 常规写文章、生成封面/配图 | 内置 `image_generate`（默认，最省事） |
| 想固定用某家第三方 API、或需要特定参数 | `generate_image.py` 脚本 + 自备密钥 |

---

绝大多数情况下，直接用 `image_generate` 工具即可，无需任何额外配置。🎨
