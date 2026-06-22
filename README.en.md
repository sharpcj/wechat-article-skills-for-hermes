# WeChat Article Skills

> 🌐 **Language**: [中文](./README.md) · [English](./README.en.md)

## 📖 Project Overview

A Hermes Agent skill suite for WeChat Official Accounts, covering **AI Writing Assistant (Tech / PM perspective)**, **Markdown → WeChat HTML formatting**, and **draft publishing**. With a local ComfyUI on hand, the full pipeline — write → illustrate → format → push to drafts — runs entirely on your own machine.

> 🙏 **Acknowledgement**: This repository is forked from the upstream project [BND-1/wechat_article_skills](https://github.com/BND-1/wechat_article_skills) (which targets Claude Code Skills). Huge thanks to the original author for the solid foundation. This fork has been ported to **Hermes Agent** and switched its default image backend from Gemini / DALL-E to local ComfyUI. See the **Differences from the Original Version** section below.

## ✨ Core Tools

### 1️⃣ WeChat Product Manager Writer - AI PM Assistant
Write from an AI Product Manager's perspective. Covers product teardowns, scenario solutions, efficiency boosts, methodology, and industry trends.

**Key Features:**
- 🤖 Product-thinking driven writing, first-person, opinionated
- 📊 Mandatory infographics/structure maps (Graphic Recording style)
- 🎨 Mandatory professional cover image
- 🖼️ On-demand content illustrations (12 Types × 9 Styles system)
- 🎯 Scenario-oriented practical insights

[📚 Documentation](./wechat-product-manager-writer/SKILL.md)

---

### 2️⃣ WeChat Tech Writer - AI Writing Assistant
AI-powered technical writing assistant. Auto-searches, scrapes, and rewrites to produce high-quality tech content for general audiences.

**Key Features:**
- 🤖 AI-assisted search and writing
- 🎨 Mandatory professional cover image
- 🖼️ On-demand content illustrations (12 Types × 9 Styles system)
- 📱 Reader-friendly, plain-language tech writing

[📚 Documentation](./wechat-tech-writer/SKILL.md)

---

### 3️⃣ WeChat Article Formatter
Convert Markdown articles to beautifully formatted HTML optimized for WeChat Official Accounts. All styles inline — paste directly into the WeChat editor.

**Key Features:**
- 📝 Hand-written Markdown parser, zero external Markdown dependencies
- 🎨 Four YAML themes (Classic Blue / Elegant Purple / Warm Orange / Minimal Black), customizable
- 🔧 Variable substitution — one-click color/size changes
- 📐 Pre-formatting: CJK spacing, quote conversion, blank line compression
- 🧩 Full support for tables, code blocks, nested lists, captions, and more

[📚 Documentation](./wechat-article-formatter/SKILL.md)

---

### 4️⃣ WeChat Draft Publisher
Automatically publish HTML articles to your WeChat Official Account draft box.

**Key Features:**
- ✅ Auto access_token caching and management
- ✅ Cover image upload via `--cover` parameter
- ✅ Author read from config file, auto-prompt on first run
- ✅ Smart error handling & retry
- ✅ CLI + Interactive modes

[📚 Documentation](./wechat-draft-publisher/SKILL.md)

---

## 🖼️ About Illustrations

### Type × Style System

Both writing skills share the same content illustration framework:

- **12 Types** (what to draw): concept / process / whiteboard / data-viz / comparison / architecture / mindmap / timeline / checklist / quote-card / scene / atmosphere
- **9 Styles** (visual style): flat vector / minimal line / blueprint / hand-drawn / watercolor / poster / warm / minimalist / business
- **Auto-selection**: Agent matches Type + Style based on article content signals
- **Dedicated prompt templates**: Each Type has its own prompt construction template

See `references/image-styles/` in each writing skill for details.

### Image Generation: Local ComfyUI

Both writing skills ship with an embedded ComfyUI client (`scripts/comfyui_gen.py`) and workflow template (`templates/image_z_image.json`):

- ✅ Talks to a local ComfyUI instance (default `http://localhost:6677`)
- ✅ Injects positive/negative prompts via KSampler node references
- ✅ Configured per skill via `config.json`, overridable by environment variables
- ✅ Covers at 2.35:1 (1024×432), content illustrations at 4:3 (1024×768)

> Design intent: **each skill is independently installable**, so the two `comfyui_gen.py` files are intentionally maintained as identical copies. Keep them in sync when you change one.
>
> When ComfyUI is not running, the skills will **not silently fall back**. They first tell you the service is offline and let you choose between starting ComfyUI manually or switching to Hermes' built-in `image_generate` tool.

---

## 🚀 Quick Start

### Install to your ~/.hermes/skills

```bash
# Clone the repository
git clone <repository-url>
# Copy each skill folder into your ~/.hermes/skills directory
# Then use skills_list / skill_view in Hermes to load them
```

### Typical Workflow

**One-sentence workflow**
```
Help me write an article about Claude Code, format it beautifully, and publish it to my WeChat Official Account backend
```

**Step-by-step**
```bash
# 1. Write article (auto-generates cover.png)
#    Tell Hermes: "Write an article about XXX for WeChat"

# 2. Format
cd wechat-article-formatter
python scripts/markdown_to_html.py --input article.md --theme default

# 3. Publish (cover uploaded via --cover, not embedded in body)
cd ../wechat-draft-publisher
python publisher.py --title "Title" --content ../article.html --cover ../cover.png
```

---

## 📂 Project Structure

```
wechat_article_skills/
├── wechat-tech-writer/              # AI tech-writing skill
│   ├── SKILL.md
│   ├── config.json                  # ComfyUI config
│   ├── scripts/
│   │   ├── comfyui_gen.py           # Local ComfyUI (preferred)
│   │   └── generate_image.py        # Gemini / DALL-E (fallback)
│   ├── templates/
│   │   └── image_z_image.json       # ComfyUI workflow template
│   └── references/
│       ├── image-styles/            # Illustration style library
│       │   ├── styles.md            #   12 Types + 9 Styles
│       │   ├── style-presets.md     #   Preset combos by article type
│       │   ├── auto-selection.md    #   Auto-recommendation rules
│       │   └── prompt-construction.md # Prompt templates per Type
│       ├── cover-image-guide.md     # Cover image guide
│       ├── content-images-guide.md  # Content illustration guide
│       └── writing-style.md         # Writing style guide
│
├── wechat-product-manager-writer/   # AI PM-perspective writing skill
│   ├── SKILL.md
│   ├── config.json
│   ├── scripts/                     # Synced copy of tech-writer scripts
│   ├── templates/
│   └── references/
│       ├── image-styles/            # Same structure as tech-writer
│       ├── cover-image-guide.md
│       └── structure-image-guide.md # Structure image guide
│
├── wechat-article-formatter/        # Markdown → WeChat HTML
│   ├── SKILL.md
│   ├── scripts/
│   │   ├── markdown_to_html.py      # Core converter (hand-written parser)
│   │   └── convert-code-blocks.py   # WeChat-compatible code blocks
│   ├── themes/                      # YAML theme files
│   │   ├── default.yaml             #   Classic Blue
│   │   ├── grace.yaml               #   Elegant Purple
│   │   ├── modern.yaml              #   Warm Orange
│   │   └── simple.yaml              #   Minimal Black
│   ├── templates/                   # Legacy CSS themes (kept for compat)
│   └── examples/                    # HTML example templates
│
├── wechat-draft-publisher/          # HTML → WeChat draft box
│   ├── SKILL.md
│   ├── publisher.py                 # Core publishing script
│   └── scripts/                     # HTML optimization, style fixes
│
└── README.md                        # This file
```

---

## 💡 Use Cases

### Tech Bloggers
- Use **WeChat Tech Writer** for AI-assisted content creation
- Use **Article Formatter** with YAML themes for professional styling
- Use **Draft Publisher** for one-click publishing

### Product Managers / Content Operators
- Use **WeChat Product Manager Writer** for PM-perspective writing
- Use **Article Formatter** to switch themes for different styles
- Automate publishing workflow

### Media Creators
- Focus on writing in Markdown
- One-click conversion to beautiful layouts
- Quick publishing to WeChat

---

## 📋 System Requirements

- **Python**: 3.8+
- **Dependencies**: PyYAML (formatter only)
- **OS**: Windows / macOS / Linux
- **WeChat Account**: Verified Service or Subscription Account (for API publishing)
- **ComfyUI (optional)**: A local ComfyUI instance (default `http://localhost:6677`), used by the embedded image scripts in the writing skills

---

## 🔧 Configuration

### WeChat Draft Publisher Setup

Create config file at `~/.wechat-publisher/config.json`:

```json
{
  "appid": "wx1234567890abcdef",
  "appsecret": "your_appsecret_here",
  "author": "Your Author Name"
}
```

- `appid` / `appsecret`: Get from WeChat Official Accounts Platform → Settings & Development → Basic Configuration
- `author`: Optional. If not set, the tool will prompt on first run and save automatically

### ComfyUI Setup (Optional)

Edit `wechat-tech-writer/config.json` and `wechat-product-manager-writer/config.json`:

```json
{
  "comfyui_url": "http://localhost:6677",
  "comfyui_output_dir": "/home/yourname/comfyui_output"
}
```

Or override with environment variables:

```bash
export COMFYUI_URL="http://localhost:6677"
export COMFYUI_OUTPUT_DIR="$HOME/comfyui_output"
```

> ⚠️ The default `comfyui_output_dir` in the repo points to the author's local path. **Change it to your own directory after cloning.**

---

## 📚 Documentation

### Tool-Specific Guides
- [WeChat Article Formatter Skill Documentation](./wechat-article-formatter/SKILL.md)
- [WeChat Draft Publisher Skill Documentation](./wechat-draft-publisher/SKILL.md)
- [WeChat Tech Writer Skill Documentation](./wechat-tech-writer/SKILL.md)
- [WeChat Product Manager Writer Skill Documentation](./wechat-product-manager-writer/SKILL.md)

### Illustration System Docs
- [Content Illustration Style Library (Type × Style)](./wechat-tech-writer/references/image-styles/styles.md)
- [Preset Combos by Article Type](./wechat-tech-writer/references/image-styles/style-presets.md)
- [Auto-Recommendation Rules](./wechat-tech-writer/references/image-styles/auto-selection.md)
- [Prompt Construction Guide](./wechat-tech-writer/references/image-styles/prompt-construction.md)

---

## 📝 Example Articles

Featured articles created and published using this toolkit:

1. **[Claude Code Beginner's Guide: Can You Develop Without Coding? This Guide Has You Covered, Double Your Efficiency!](https://mp.weixin.qq.com/s/Dx-XYcj74c2LdZOWwNS7GQ)**

2. **[From 70 Minutes to 9 Minutes: WeChat Official Account Automation Skills! Efficiency Booster!](https://mp.weixin.qq.com/s/iBKgEX_vfYNIe90qPi03Sw)**

3. **[From Chat to Agent: Why Claude Agent SDK is the Real Productivity Switch for AI](https://mp.weixin.qq.com/s/58nZuLJGNjm6hqfGzJg-ZA)**

4. **[Claude Skill: Why Will It Replace Dify, n8n, and Coze?](https://mp.weixin.qq.com/s/rXl4nLI6ouJMIMfvL1iSbQ)**

> 💡 All articles above were formatted and published using this toolkit.

---

## ⚠️ Important Notes

1. **API Rate Limits**
   - access_token has daily request limits (2000/day)
   - This tool auto-caches tokens to minimize requests

2. **Image Guidelines**
   - Cover image uploaded via `--cover` parameter, not embedded in body
   - Recommended cover size: 900x500 pixels
   - Image size limit: 2MB

3. **Style Compatibility**
   - WeChat editor has limited CSS support (no pseudo-elements, gradients, shadows)
   - Formatter output has all styles inline, ready to paste
   - Code blocks need `convert-code-blocks.py` for WeChat compatibility

---

## 🐛 Troubleshooting

### Common Issues

**Q: Styles lost after pasting?**
- Use Chrome or Edge browser
- Try selecting and copying all content
- Make sure to use "Paste" not "Paste and Match Style"

**Q: access_token fetch failed?**
- Verify AppID and AppSecret
- Ensure account is verified
- Check IP whitelist settings

**Q: Author name not set?**
- First run of publisher.py will prompt and save to `~/.wechat-publisher/config.json`
- Or manually add `"author"` field to the config file

For more issues, check tool-specific documentation or submit an Issue.

---

## 🔀 Differences from the Original Version

This repository was forked from a Claude Code Skills project, ported wholesale to **Hermes Agent**, and reworked across the default image backend, runtime, and writing perspectives.

### 1. Runtime: Claude Code → Hermes Agent

| Aspect | Original | Current |
|--------|----------|---------|
| Target agent | Claude Code Skills | Hermes Agent Skills |
| Install path | `~/.claude/skills/` | `~/.hermes/skills/` |
| Frontmatter `allowed-tools` | `WebSearch, WebFetch, Read, Write, Edit, Bash` | Removed (Hermes doesn't need it) |
| Tool calls | `WebSearch` / `WebFetch` / `Write` | `web_search` / `web_extract` / `browser_navigate` / `write_file` |

### 2. Default Image Backend: Gemini / DALL-E → Local ComfyUI

| Aspect | Original | Current |
|--------|----------|---------|
| Preferred image flow | `generate_image.py` calling Gemini / DALL-E | Local ComfyUI (`comfyui_gen.py` + workflow template) |
| Config | `GEMINI_API_KEY` / `OPENAI_API_KEY` env vars | Per-skill `config.json`, env vars override |
| Offline fallback | Key/network failure meant no image | Skill asks user before falling back to `image_generate` |
| Size conventions | Inconsistent | Unified: covers 2.35:1 (1024×432), content/structure 4:3 (1024×768) |

### 3. Formatter: CSS Themes → YAML Themes

| Aspect | Original | Current |
|--------|----------|---------|
| Markdown parsing | Python `markdown` lib + BeautifulSoup + cssutils | Hand-written parser, zero external Markdown deps |
| Theme system | 3 CSS files | 4 YAML themes (Classic Blue / Elegant Purple / Warm Orange / Minimal Black) with variable substitution |
| Dependencies | 6 pip packages | 1 (PyYAML) |
| Pre-formatting | None | CJK spacing, quote conversion, blank line compression |

### 4. Illustration System: Simple → Type × Style

| Aspect | Original | Current |
|--------|----------|---------|
| Illustration types | 5 (bar chart, architecture, comparison, flowchart, radar) | 12 Types + 9 Styles with dedicated prompt templates |
| Style selection | Manual | Agent auto-recommends based on article content signals |
| Illustration count | Hard cap 0-2 | On-demand, max 1 per H2 section, quality over quantity |
| Cover image | Embedded in body | Uploaded via `--cover` parameter, not in body |

### 5. Publisher: Author Config

- Author read from `~/.wechat-publisher/config.json` `author` field
- Auto-prompt and save on first run if not configured
- CLI `--author` flag takes highest priority

### 6. New "AI PM Perspective" Writing Skill

`wechat-product-manager-writer/` added on top of the original suite:
- First-person, opinionated, scenario-driven
- Five content categories: product teardowns / scenario solutions / efficiency wins / methodology / industry watch
- Mandatory Graphic Recording–style content structure image per article

---

## 📝 Changelog

### v3.2.0 (2026-06-23)
- 🎨 Formatter refactored: YAML theme system replaces CSS + BeautifulSoup, 4 finely-tuned themes
- 🖼️ Illustration system upgraded: 12 Types × 9 Styles with dedicated prompt templates and auto-recommendation
- 📝 Cover image no longer embedded in body; uploaded via `--cover` parameter
- 👤 Publisher author now read from config file, auto-prompt on first run
- 📦 Formatter dependencies reduced from 6 to 1 (PyYAML)

### v3.0.0 (2026-06-22) · Hermes Migration
- 🔁 Full migration from Claude Code Skills to **Hermes Agent**
- 🖼️ Default image backend switched from Gemini/DALL-E to local ComfyUI
- 🛡️ ComfyUI offline: no more silent fallback
- 📐 Unified image size conventions
- 📦 Reinforced "each skill independently installable" principle

### v2.0.0 (2026-01-16)
- 🚀 Added `WeChat Product Manager Writer`
- 🎨 Mandatory infographic and professional cover generation

### v1.0.0 (2025-12-28)
- ✅ Released three core tools

---

## 📄 License

MIT License - Free for personal and commercial use

---

## 🙏 Acknowledgments

Thanks to these open-source projects:
- [PyYAML](https://pyyaml.org/)
- [Requests](https://requests.readthedocs.io/)

---

**Happy Writing!** 🎉

Feel free to file a GitHub Issue for questions or suggestions!
