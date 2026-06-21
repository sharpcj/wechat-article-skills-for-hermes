# WeChat Article Skills

> 🌐 **Language**: [中文](./README.md) · [English](./README.en.md)

## 📖 Project Overview

A Hermes Agent skill suite for WeChat Official Accounts, covering **AI Writing Assistant (Tech / PM perspective)**, **Markdown → WeChat HTML formatting**, and **draft publishing**. With a local ComfyUI on hand, the full pipeline — write → illustrate → format → push to drafts — runs entirely on your own machine.

> 🙏 **Acknowledgement**: This repository is forked from the upstream project [BND-1/wechat_article_skills](https://github.com/BND-1/wechat_article_skills) (which targets Claude Code Skills). Huge thanks to the original author for the solid foundation. This fork has been ported to **Hermes Agent** and switched its default image backend from Gemini / DALL-E to local ComfyUI. See the **Differences from the Original Version** section below.

## ✨ Core Tools

### 1️⃣ WeChat Product Manager Writer - AI PM Assistant
Write from an AI Product Manager's perspective. Covers product teardowns, scenario solutions, efficiency boosts, methodology, and industry trends.

**Key Features:**
- 🤖 Product-thinking driven writing
- 📊 Mandatory infographics/structure maps
- 🎨 Cover image via local ComfyUI (built in; falls back to Hermes' `image_generate` when offline)
- 🎯 Scenario-oriented practical insights

[📚 Documentation](./wechat-product-manager-writer/SKILL.md)

---

### 2️⃣ WeChat Tech Writer - AI Writing Assistant
AI-powered technical writing assistant for creating high-quality tech content.

**Key Features:**
- 🤖 AI-assisted writing
- 🖼️ Cover image via local ComfyUI (built in; falls back to Hermes' `image_generate` when offline)
- 📊 Technical content optimization
- 🎯 SEO keyword optimization
- 📱 Mobile reading optimization

[📚 Documentation](./wechat-tech-writer/SKILL.md)

---

### 3️⃣ WeChat Article Formatter
Convert Markdown articles to beautifully formatted HTML optimized for WeChat Official Accounts.

**Key Features:**
- 📝 Full Markdown syntax support
- 🎨 Three premium themes (Tech, Minimal, Business)
- 💅 Professional styling for WeChat
- 🌈 Multi-language syntax highlighting
- ⚡ Batch conversion support
- 👀 Real-time preview

[📚 Documentation](./wechat-article-formatter/README.md)

---

### 4️⃣ WeChat Draft Publisher
Automatically publish HTML articles to your WeChat Official Account draft box.

**Key Features:**
- ✅ Auto access_token management
- ✅ Cover image upload support
- ✅ Smart error handling & retry
- ✅ CLI + Interactive modes
- ✅ Complete logging

[📚 Documentation](./wechat-draft-publisher/README.md)

---

## 🚀 Quick Start

### Install to your ~/.hermes/skills

```bash
# Clone the repository
git clone <repository-url>
cd wechat_article_skills

# Copy each skill folder into your ~/.hermes/skills directory
# Install Python dependencies
pip install -r requirements.txt  # if needed
```

### Typical Workflow

**One-sentence workflow**
```bash
Help me write an article about Claude Code, format it beautifully, and publish it to my WeChat Official Account backend
```

---

## 🖼️ Image Generation: Local ComfyUI

Both writing skills (`wechat-tech-writer`, `wechat-product-manager-writer`) ship with an **embedded** ComfyUI client (`scripts/comfyui_gen.py`) and workflow template (`templates/image_z_image.json`):

- ✅ Talks to a local ComfyUI instance (default `http://localhost:6677`)
- ✅ Injects positive/negative prompts by following KSampler node references — works even when the workflow template leaves prompts empty
- ✅ Configured per skill via `config.json` (`comfyui_url` / `comfyui_output_dir`), overridable by environment variables
- ✅ Covers at 2.35:1 (1024×432), content/structure images at 4:3 (1024×768)

> Design intent: **each skill is independently installable**, so the two `comfyui_gen.py` files are intentionally maintained as identical copies rather than a shared script. Keep them in sync when you change one.
>
> When ComfyUI is not running, the skills will **not silently fall back**. They first tell you the service is offline and let you choose between starting ComfyUI manually or switching to Hermes' built-in `image_generate` tool (no API key needed).

---

## 📂 Project Structure

```
wechat_article_skills/
├── wechat-tech-writer/              # AI tech-writing skill (embeds ComfyUI client)
│   ├── SKILL.md
│   ├── EXAMPLES.md
│   ├── config.json                  # ComfyUI URL / output dir
│   ├── scripts/
│   │   ├── comfyui_gen.py           # Local ComfyUI (preferred)
│   │   ├── generate_image.py        # Gemini / DALL-E (fallback, needs key)
│   │   ├── generate_cover_optimized.py
│   │   └── generate_temp.py
│   ├── templates/
│   │   └── image_z_image.json       # ComfyUI workflow template
│   └── references/                  # Style / image / fact-checking guides
│
├── wechat-product-manager-writer/   # AI PM-perspective writing skill (embeds ComfyUI client)
│   ├── SKILL.md
│   ├── EXAMPLES.md
│   ├── config.json
│   ├── scripts/
│   │   ├── comfyui_gen.py           # Synced copy of the script in tech-writer
│   │   └── generate_image.py        # Fallback
│   ├── templates/
│   │   └── image_z_image.json
│   └── references/                  # Style, cover & structure-image guides
│
├── wechat-article-formatter/        # Markdown → WeChat HTML formatter
│   ├── SKILL.md / README.md / QUICKSTART.md / EXAMPLES.md
│   ├── scripts/                     # markdown_to_html.py and friends
│   ├── templates/                   # tech / minimal / business CSS themes
│   ├── references/
│   └── examples/                    # Rendered HTML samples
│
├── wechat-draft-publisher/          # HTML → Official Account draft box
│   ├── SKILL.md / README.md
│   ├── publisher.py                 # Core publishing script
│   ├── scripts/                     # Publish workflow, HTML tweaks
│   └── examples/config.json.example # appid / appsecret template
│
└── README.md                        # This file
```

---

## 💡 Use Cases

### Tech Bloggers
- Use **WeChat Tech Writer** for AI-assisted content creation
- Use **Article Formatter** with tech theme for professional styling
- Use **Draft Publisher** for one-click publishing

### Content Operators
- Use **Article Formatter** for batch converting articles
- Choose themes based on content style
- Automate publishing workflow

### Media Creators
- Focus on writing in Markdown
- One-click conversion to beautiful layouts
- Quick publishing to WeChat

---

## 📋 System Requirements

- **Python**: 3.6+
- **OS**: Windows / macOS / Linux
- **Browser**: Chrome / Edge (for preview)
- **WeChat Account**: Verified Service or Subscription Account (for API publishing)
- **ComfyUI (optional)**: A local ComfyUI instance (default `http://localhost:6677`), used by the embedded image scripts in the writing skills. When unavailable, the skills fall back to Hermes' built-in `image_generate` after asking you.

---

## 🔧 Configuration

### WeChat Draft Publisher Setup

Create config file at `~/.wechat-publisher/config.json`:

```json
{
  "appid": "wx1234567890abcdef",
  "appsecret": "your_appsecret_here"
}
```

**Get AppID and AppSecret:**
1. Login to [WeChat Official Accounts Platform](https://mp.weixin.qq.com)
2. Go to "Settings & Development" → "Basic Configuration"
3. Find Developer ID and Secret

### ComfyUI Setup (Optional)

To use local ComfyUI for image generation (recommended), edit `wechat-tech-writer/config.json` and `wechat-product-manager-writer/config.json`:

```json
{
  "comfyui_url": "http://localhost:6677",
  "comfyui_output_dir": "/home/yourname/comfyui_output"
}
```

Or override with environment variables (no file edits needed):

```bash
export COMFYUI_URL="http://localhost:6677"
export COMFYUI_OUTPUT_DIR="$HOME/comfyui_output"
```

> ⚠️ The default `comfyui_output_dir` in the repo points to the author's local path. **Change it to your own directory after cloning.**

If ComfyUI is not running, the writing skills will prompt you to either start it manually or switch to Hermes' built-in `image_generate` tool.

---

## 📚 Documentation

### Tool-Specific Guides
- [WeChat Article Formatter Complete Guide](./wechat-article-formatter/README.md)
- [WeChat Draft Publisher User Guide](./wechat-draft-publisher/README.md)
- [WeChat Tech Writer Skill Documentation](./wechat-tech-writer/SKILL.md)
- [WeChat Product Manager Writer Skill Documentation](./wechat-product-manager-writer/SKILL.md)

### External Resources
- [WeChat Official Accounts Help Center](https://kf.qq.com/product/weixinmp.html)
- [Markdown Guide](https://www.markdownguide.org/)

---

## 📝 Example Articles

Featured articles created and published using this toolkit:

### Technical Article Examples

1. **[Claude Code Beginner's Guide: Can You Develop Without Coding? This Guide Has You Covered, Double Your Efficiency!](https://mp.weixin.qq.com/s/Dx-XYcj74c2LdZOWwNS7GQ)**  

2. **[From 70 Minutes to 9 Minutes: WeChat Official Account Automation Skills! Efficiency Booster!](https://mp.weixin.qq.com/s/iBKgEX_vfYNIe90qPi03Sw)**  

3. **[From Chat to Agent: Why Claude Agent SDK is the Real Productivity Switch for AI](https://mp.weixin.qq.com/s/58nZuLJGNjm6hqfGzJg-ZA)**  

4. **[Claude Skill: Why Will It Replace Dify, n8n, and Coze?](https://mp.weixin.qq.com/s/rXl4nLI6ouJMIMfvL1iSbQ)**

> 💡 **Tip**: All articles above were formatted and published using this toolkit. Feel free to reference them!

---

## ⚠️ Important Notes

1. **API Rate Limits**
   - access_token has daily request limits (2000/day)
   - This tool auto-caches tokens to minimize requests

2. **Image Guidelines**
   - WeChat doesn't support local images
   - Recommended cover size: 900x500 pixels
   - Image size limit: 2MB

3. **Style Compatibility**
   - WeChat editor has limited CSS support
   - Some advanced styles may not render
   - Use provided themes for best results

---

## 🐛 Troubleshooting

### Common Issues

**Q: Styles lost after pasting?**
- Use Chrome or Edge browser
- Try selecting and copying all content

**Q: access_token fetch failed?**
- Verify AppID and AppSecret
- Ensure account is verified
- Check IP whitelist settings

For more issues, check tool-specific documentation or submit an Issue.

---

## 🔀 Differences from the Original Version

This repository was forked from a Claude Code Skills project, ported wholesale to **Hermes Agent**, and reworked across the default image backend, runtime, and writing perspectives. Highlights:

### 1. Runtime: Claude Code → Hermes Agent

| Aspect | Original | Current |
|--------|----------|---------|
| Target agent | Claude Code Skills | Hermes Agent Skills |
| Install path | `~/.claude/skills/` or `/root/.claude/skills/` | `~/.hermes/skills/` |
| Frontmatter `allowed-tools` | `WebSearch, WebFetch, Read, Write, Edit, Bash` | Removed (Hermes doesn't need it) |
| Tool calls | `WebSearch` / `WebFetch` / `Write` | `web_search` / `web_extract` / `browser_navigate` / `write_file` |
| Skill descriptions | Short triggers | Expanded triggers covering more natural-language phrasings, so Hermes picks the right skill automatically |

All hardcoded paths inside SKILL.md / EXAMPLES.md / references were rewritten from `/root/.claude/skills/...` to `~/.hermes/skills/...`.

### 2. Default Image Backend: Gemini / DALL-E → Local ComfyUI

This is the biggest change of this round.

| Aspect | Original | Current |
|--------|----------|---------|
| Preferred image flow | `scripts/generate_image.py` calling Gemini Imagen / DALL-E 3 | Local ComfyUI (new `scripts/comfyui_gen.py` + `templates/image_z_image.json`) |
| Config | `GEMINI_API_KEY` / `OPENAI_API_KEY` env vars | Per-skill `config.json` (`comfyui_url` / `comfyui_output_dir`), env vars override |
| Proxy / network | Had to clear `ALL_PROXY` when calling Gemini, otherwise it failed with `socks5h://` not supported | Loopback only, no proxy hassle |
| Offline fallback | None — key/network failure meant no image | When ComfyUI is offline, **the skill tells the user and asks** before falling back to Hermes' `image_generate` |
| Prompt injection | Each script handled it independently | `comfyui_gen.py` walks the KSampler `positive` / `negative` references to find the actual `CLIPTextEncode` nodes — works even when the template's prompts are left empty |
| Size conventions | Inconsistent across files | Unified: covers 2.35:1 (1024×432), content/structure images 4:3 (1024×768) |
| Where the old scripts went | — | `generate_image.py` and friends are kept as **optional fallbacks**, marked "advanced" in the docs and not used by default |

The long block in `wechat-product-manager-writer/SKILL.md` warning about Gemini proxy issues, JPEG-vs-PNG, API-key configuration, and prompt length limits was removed entirely once we moved to ComfyUI.

### 3. New "AI PM Perspective" Writing Skill

`wechat-product-manager-writer/` was added on top of the original suite:

- `wechat-tech-writer`: technical popular-science articles — structure = "What it is / What it does / Why pick it / How to start"
- `wechat-product-manager-writer`: PM-perspective articles — structure spans "product teardowns / scenario solutions / efficiency wins / methodology / industry watch", written in first person with real usage scenarios, and **mandates a Graphic Recording–style content structure image** for every article

Both skills coexist and cover "tech popular-science" vs "product-flavored" writing needs respectively.

### 4. "Each Skill Is Independently Installable"

- `wechat-tech-writer/scripts/comfyui_gen.py` and `wechat-product-manager-writer/scripts/comfyui_gen.py` are **two identical copies kept in sync on purpose**
- Each ships its own `config.json` and `templates/image_z_image.json`
- Either skill can be copied into `~/.hermes/skills/` on its own and just work — **no need to install the other as a dependency**

### 5. WeChat Renderer Compatibility

- `wechat-article-formatter`'s converter and CSS themes were nudged to reduce style-loss inside the WeChat editor
- Copy in `wechat-draft-publisher/README.md` was changed from "Claude Code Skill" to "Hermes Agent Skill"

### 6. Docs & Examples

- All `/root/.claude/skills/...` paths in both Chinese and English READMEs were replaced with `~/.hermes/skills/...`
- A new "ComfyUI Setup" section makes it explicit that **the default `comfyui_output_dir` in the repo is the author's local path and you must change it**
- The project-structure tree was rewritten to match the actual on-disk layout

> If you came from the original repo and want to keep using Gemini / DALL-E, the matching scripts (`generate_image.py`, etc.) still live in each writing skill's `scripts/` directory. See `references/api-configuration.md` for setup.

---

## 📝 Changelog

### v3.0.0 (2026-06-22) · Hermes Migration
- 🔁 Full migration from Claude Code Skills to **Hermes Agent**: paths `~/.claude/skills/` → `~/.hermes/skills/`, `allowed-tools` frontmatter removed, tool calls rewritten to `web_search` / `web_extract` / `write_file` etc.
- 🖼️ **Default image backend switched from Gemini/DALL-E to local ComfyUI**, with a new `scripts/comfyui_gen.py` + `templates/image_z_image.json`. Config moved to `config.json`. Legacy scripts kept as optional fallbacks.
- 🧠 `comfyui_gen.py` resolves KSampler positive/negative references to find the actual prompt nodes — works even when the workflow template leaves prompts empty.
- 🛡️ When ComfyUI is offline, the skill **no longer falls back silently**: it asks whether to start ComfyUI or use Hermes' built-in `image_generate`.
- 📐 Unified image sizes: covers 2.35:1 (1024×432), content/structure images 4:3 (1024×768).
- 📦 Reinforced the "each skill is independently installable" principle: both writing skills carry their own embedded copy of the ComfyUI client and workflow template.
- 🧹 Removed the large Gemini-specific notes (proxy, JPEG vs PNG, API key, prompt length) from product-manager-writer — no longer relevant.
- 📚 See the **Differences from the Original Version** section above for the full diff.

### v2.0.0 (2026-01-16)
- 🚀 Added `WeChat Product Manager Writer` (AI PM perspective)
- 🎨 Mandatory infographic and professional cover generation
- 📂 Refactored structure to support four core tools
- 🐛 Fixed rendering issues
- 🐛 Fixed WeChat Official Account compatibility bugs

### v1.0.0 (2025-12-28)
- ✅ Released three core tools
- ✅ Complete documentation
- ✅ Optimized user experience

---

## 📄 License

MIT License - Free for personal and commercial use

---

## 🙏 Acknowledgments

Thanks to these open-source projects:
- [Python-Markdown](https://python-markdown.github.io/)
- [BeautifulSoup4](https://www.crummy.com/software/BeautifulSoup/)
- [Requests](https://requests.readthedocs.io/)

---

**Happy Writing!** 🎉

Feel free to file a GitHub Issue for questions or suggestions!


