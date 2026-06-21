# 微信公众号文章工具集

> 🌐 **Language**: [中文](./README.md) · [English](./README.en.md)

## 📖 项目简介

一套面向微信公众号的 Hermes Agent 技能集，涵盖 **AI 写作助手（技术视角 / 产品视角）**、**Markdown → 公众号 HTML 格式化**、**草稿一键发布** 四个核心 skill。配合本地 ComfyUI 即可在本地完成「写稿 → 配图 → 排版 → 推送草稿箱」的全流程。

> 🙏 **致谢**：本仓库 fork 自上游项目 [BND-1/wechat_article_skills](https://github.com/BND-1/wechat_article_skills)（面向 Claude Code Skills），感谢原作者奠定的优秀基础。本仓库已整体迁移到 **Hermes Agent**，并将默认生图后端从 Gemini / DALL-E 切换为本地 ComfyUI。详见下方「与原始版本的区别」一节。

## ✨ 核心工具

### 1️⃣ WeChat Product Manager Writer - AI 产品经理写作助手
从 AI 产品经理视角撰写文章。涵盖 AI 产品拆解、场景解决方案、效率提升实战、产品方法论、行业观察。

**核心特性：**
- 🤖 产品思维驱动写作
- 📊 强制生成内容结构图（信息图）
- 🎨 强制生成专业文章封面
- 🎯 实战场景导向，非纯技术教程

[📚 详细文档](./wechat-product-manager-writer/SKILL.md)

---

### 2️⃣ WeChat Tech Writer - AI 技术写作助手
基于 AI 的智能技术文章写作工具，快速生成高质量技术内容。

**核心特性：**
- 🤖 AI 辅助写作
- 📊 技术文章优化
- 🎯 SEO 关键词优化
- 📱 移动端阅读优化

[📚 详细文档](./wechat-tech-writer/SKILL.md)

---

### 3️⃣ WeChat Article Formatter - 文章格式化工具
将 Markdown 文章转换为适合微信公众号的美化 HTML，一键生成专业排版。

**核心特性：**
- 📝 完整支持 Markdown 语法
- 🎨 三套精美主题（科技风、简约风、商务风）
- 💅 专业样式，完美适配微信公众号
- 🌈 多语言代码高亮
- ⚡ 支持批量转换
- 👀 实时预览功能

[📚 详细文档](./wechat-article-formatter/README.md)

---

### 4️⃣ WeChat Draft Publisher - 草稿发布工具
自动将 HTML 格式的文章推送到微信公众号草稿箱。

**核心特性：**
- ✅ 自动获取和缓存 access_token
- ✅ 支持上传封面图片
- ✅ 智能错误处理和重试
- ✅ 命令行 + 交互式双模式
- ✅ 完整的日志输出

[📚 详细文档](./wechat-draft-publisher/README.md)

---

## 🖼️ 关于生图：本地 ComfyUI

两个写作类 skill（`wechat-tech-writer`、`wechat-product-manager-writer`）已经各自**内嵌**一份 ComfyUI 调用脚本（`scripts/comfyui_gen.py`）和 workflow 模板（`templates/image_z_image.json`）：

- ✅ 调用本地 ComfyUI（默认 `http://localhost:6677`），用本地算力、可控、可换模型/workflow
- ✅ 按 KSampler 的 positive/negative 引用精确注入提示词，支持负向词
- ✅ 配置走各 skill 自己的 `config.json`（`comfyui_url` / `comfyui_output_dir`）+ 环境变量覆盖，换机器只改配置即可
- ✅ 封面图按 2.35:1（1024×432）出图、内容插图按 4:3（1024×768）出图

> 设计取向：**每个 skill 都可以独立安装、独立使用**，因此两边的 `comfyui_gen.py` 是**有意维护的两份副本**而不是共享脚本。修改时请记得同步两边。
>
> ComfyUI 未启动时，skill 不会静默退回；它会先告诉你"本地 ComfyUI 未在线"，让你选择是手动启动 ComfyUI、还是改用 Hermes 内置的 `image_generate`（无需自备 API key）。

---

## 🚀 快速开始

### 安装到你的 ~/.hermes/skills

```bash
# 克隆项目
git clone <repository-url>
# 把各个 skill 文件夹复制到你的 ~/.hermes/skills 目录下
# 然后在 Hermes 中通过 skills_list / skill_view 即可看到并加载这些技能
```

### 典型工作流程

**全流程一句话搞定**
```bash
帮我写一篇介绍 Claude code 的文章，并且进行格式美化，然后推送到微信公众号后台
```

---

## 📂 项目结构

```
wechat_article_skills/
├── wechat-tech-writer/              # AI 技术写作 skill（含内嵌 ComfyUI 生图脚本）
│   ├── SKILL.md
│   ├── EXAMPLES.md
│   ├── config.json                  # ComfyUI 配置（URL / 输出目录）
│   ├── scripts/
│   │   ├── comfyui_gen.py           # 本地 ComfyUI 生图（首选）
│   │   ├── generate_image.py        # Gemini / DALL-E 直连（备选，需密钥）
│   │   ├── generate_cover_optimized.py
│   │   └── generate_temp.py
│   ├── templates/
│   │   └── image_z_image.json       # ComfyUI workflow 模板
│   └── references/                  # 写作风格、配图、事实核查等参考资料
│
├── wechat-product-manager-writer/   # AI 产品经理视角写作 skill（含内嵌 ComfyUI 生图脚本）
│   ├── SKILL.md
│   ├── EXAMPLES.md
│   ├── config.json                  # ComfyUI 配置
│   ├── scripts/
│   │   ├── comfyui_gen.py           # 与 tech-writer 同步维护的副本
│   │   └── generate_image.py        # 备选
│   ├── templates/
│   │   └── image_z_image.json
│   └── references/                  # 写作风格、封面/结构图指南等
│
├── wechat-article-formatter/        # Markdown → 公众号 HTML 排版 skill
│   ├── SKILL.md / README.md / QUICKSTART.md / EXAMPLES.md
│   ├── scripts/                     # markdown_to_html.py 等转换脚本
│   ├── templates/                   # tech / minimal / business 三套主题 CSS
│   ├── references/
│   └── examples/                    # 多套示例 HTML
│
├── wechat-draft-publisher/          # HTML → 公众号草稿箱
│   ├── SKILL.md / README.md
│   ├── publisher.py                 # 核心发布脚本
│   ├── scripts/                     # 发布流程、HTML 处理
│   └── examples/config.json.example # appid / appsecret 模板
│
└── README.md                        # 本文件
```

---

## 💡 使用场景

### 技术博客作者
- 使用 **WeChat Tech Writer** AI 辅助生成技术内容
- 使用 **Article Formatter** 的 tech 主题美化排版
- 使用 **Draft Publisher** 一键发布

### 内容运营者
- 使用 **Article Formatter** 批量转换历史文章
- 使用 minimal 或 business 主题适配不同风格
- 自动化发布流程，提升效率

### 自媒体创作者
- 在 Markdown 中专注写作
- 一键转换为精美排版
- 快速发布到公众号

---

## 📋 系统要求

- **Python**: 3.6+
- **操作系统**: Windows / macOS / Linux
- **浏览器**: Chrome / Edge（用于预览）
- **微信公众号**: 认证的服务号或订阅号（用于 API 发布）
- **ComfyUI（可选）**: 本地部署并启动的 ComfyUI（默认 `http://localhost:6677`），供写作 skill 内嵌的 `comfyui_gen.py` 使用；未启动时写作 skill 会先告知你，由你选择手动启动或改用 Hermes 内置 `image_generate`

---

## 🔧 配置说明

### WeChat Draft Publisher 配置

创建配置文件 `~/.wechat-publisher/config.json`：

```json
{
  "appid": "wx1234567890abcdef",
  "appsecret": "your_appsecret_here"
}
```

**获取 AppID 和 AppSecret：**
1. 登录 [微信公众平台](https://mp.weixin.qq.com)
2. 进入"设置与开发" → "基本配置"
3. 查看开发者 ID 和密码

### ComfyUI 生图配置（可选）

如果你想用本地 ComfyUI 生图（推荐），编辑 `wechat-tech-writer/config.json` 和 `wechat-product-manager-writer/config.json`：

```json
{
  "comfyui_url": "http://localhost:6677",
  "comfyui_output_dir": "/home/yourname/comfyui_output"
}
```

也可以用环境变量临时覆盖（不改文件）：

```bash
export COMFYUI_URL="http://localhost:6677"
export COMFYUI_OUTPUT_DIR="$HOME/comfyui_output"
```

> ⚠️ 仓库里默认的 `comfyui_output_dir` 是作者本机路径，**克隆后请改成你自己的目录**。

未启动 ComfyUI 也没关系：写作 skill 会先提示你，由你选择是手动启动 ComfyUI、还是改用 Hermes 内置的 `image_generate` 工具。

---

## 📚 文档资源

### 各工具详细文档
- [WeChat Article Formatter 完整指南](./wechat-article-formatter/README.md)
- [WeChat Draft Publisher 使用说明](./wechat-draft-publisher/README.md)
- [WeChat Tech Writer 技能文档](./wechat-tech-writer/SKILL.md)
- [WeChat Product Manager Writer 技能文档](./wechat-product-manager-writer/SKILL.md)

### 参考资料
- [微信公众平台帮助中心](https://kf.qq.com/product/weixinmp.html)
- [Markdown 语法指南](https://www.markdownguide.org/)

---

## 📝 示例文章

使用本工具集创作和发布的精选文章：

### 技术文章示例

1. **[Claude Code 零基础指南：不会写代码也能做开发？看这一篇就够了，效率翻倍！](https://mp.weixin.qq.com/s/Dx-XYcj74c2LdZOWwNS7GQ)**  

2. **[从70分钟到9分钟：微信公众号自动化Skills！提效狂魔！](https://mp.weixin.qq.com/s/iBKgEX_vfYNIe90qPi03Sw)**  

3. **[从 Chat 到 Agent：Claude Agent SDK 才是 AI 真正的生产力开关](https://mp.weixin.qq.com/s/58nZuLJGNjm6hqfGzJg-ZA)**  

4. **[Claude Skill：为什么它会取代 Dify、n8n 和 Coze？](https://mp.weixin.qq.com/s/rXl4nLI6ouJMIMfvL1iSbQ)**  

> 💡 **提示**：以上文章均使用本项目工具完成排版和发布，欢迎参考学习！

---

## ⚠️ 注意事项

1. **API 调用限制**
   - access_token 每日获取次数有限（2000次/天）
   - 本工具自动缓存 token，请勿频繁重置

2. **图片使用规范**
   - 微信不支持本地图片，需重新上传
   - 封面图片建议尺寸：900x500 像素
   - 图片大小不超过 2MB

3. **样式兼容性**
   - 微信编辑器对 CSS 支持有限
   - 部分高级样式可能无法显示
   - 建议使用工具提供的标准主题

---

## 🐛 故障排除

### 常见问题

**Q: 粘贴后样式丢失？**
- 使用 Chrome 或 Edge 浏览器
- 尝试全选复制而非部分复制

**Q: access_token 获取失败？**
- 检查 AppID 和 AppSecret 是否正确
- 确认公众号已认证
- 检查 IP 白名单配置

更多问题请查看各工具的详细文档或提交 Issue。

---

## 🔀 与原始版本的区别

本仓库 fork 自一个面向 **Claude Code** 的 WeChat Skills 项目，整体迁移到 **Hermes Agent**，并对默认生图后端、运行环境、写作视角做了一轮重构。下面是与原始版本相比的主要变化。

### 1. 运行环境：Claude Code → Hermes Agent

| 维度 | 原始版本 | 当前版本 |
|------|---------|---------|
| 目标 Agent | Claude Code Skills | Hermes Agent Skills |
| 安装目录 | `~/.claude/skills/` 或 `/root/.claude/skills/` | `~/.hermes/skills/` |
| Frontmatter `allowed-tools` | 用 `WebSearch, WebFetch, Read, Write, Edit, Bash` | 已移除（Hermes 不需要这个字段） |
| 工具调用 | `WebSearch` / `WebFetch` / `Write` | `web_search` / `web_extract` / `browser_navigate` / `write_file` |
| skill 描述 | 较简短 | 触发词扩充，覆盖更多自然语言表达，方便 Hermes 自动选 skill |

所有 SKILL.md / EXAMPLES.md / 各 references 中的硬编码路径已经从 `/root/.claude/skills/...` 改为 `~/.hermes/skills/...`。

### 2. 默认生图后端：Gemini / DALL-E → 本地 ComfyUI

这是本轮最大的改动。

| 维度 | 原始版本 | 当前版本 |
|------|---------|---------|
| 首选生图方式 | `scripts/generate_image.py` 直连 Gemini Imagen / DALL-E 3 | 本地 ComfyUI（新增 `scripts/comfyui_gen.py` + `templates/image_z_image.json`） |
| 配置方式 | 环境变量 `GEMINI_API_KEY` / `OPENAI_API_KEY` | 各 skill 自己的 `config.json`（`comfyui_url` / `comfyui_output_dir`），支持环境变量覆盖 |
| 代理/网络要求 | 调 Gemini 时必须清空 `ALL_PROXY`，否则报 `socks5h://` 不支持 | 走本机回环，无代理问题 |
| 离线兜底 | 没有，密钥失效 / 网络异常就生不了图 | ComfyUI 未启动时**先告知用户**，由用户选择手动启动 ComfyUI 或改用 Hermes 内置 `image_generate`（不再静默退回） |
| 提示词注入 | 由各脚本各自处理 | `comfyui_gen.py` 通过 KSampler 的 `positive` / `negative` 引用**精确反查**到对应的 `CLIPTextEncode` 节点，模板里正负向提示词留空也能正确注入 |
| 尺寸约定 | 各处写法不统一 | 统一：封面图 2.35:1（1024×432）、内容/结构图 4:3（1024×768） |
| 旧脚本去向 | — | 原 `generate_image.py` 等保留为**备选方案**，文档里标注"可选/高级"，常规场景不再使用 |

`wechat-product-manager-writer/SKILL.md` 里原本那一大段「调用 Gemini API 时必须清空 ALL_PROXY」「图片格式问题（JPEG vs PNG）」「API 密钥配置」「提示词长度限制」的注意事项，在切到 ComfyUI 之后已经整段移除。

### 3. 新增「AI 产品经理视角」写作 skill

`wechat-product-manager-writer/` 是相对原版新增的写作 skill，定位差异如下：

- `wechat-tech-writer`：技术科普文章，**结构**=「是什么 / 能做什么 / 为什么选它 / 如何开始」
- `wechat-product-manager-writer`：产品经理视角文章，**结构**=「产品拆解 / 场景解决方案 / 效率提升实战 / 产品方法论 / 行业观察」五类，强调第一人称、真实使用场景、强制生成**内容结构图（Graphic Recording 风格）**

两个 skill 一并保留，分别匹配"技术科普"和"产品向"两种写作需求。

### 4. 强化「内嵌生图脚本」的可独立安装设计

- `wechat-tech-writer/scripts/comfyui_gen.py` 与 `wechat-product-manager-writer/scripts/comfyui_gen.py` 是**两份完全相同的副本**
- 各自配套一份 `config.json` 和 `templates/image_z_image.json`
- 这样任一 skill 单独复制进 `~/.hermes/skills/` 都能直接用，**不需要安装另一个 skill 作为依赖**

### 5. 微信公众号渲染兼容性

- `wechat-article-formatter` 的转换脚本、CSS 主题在公众号编辑器里的样式丢失问题做了一轮调整
- `wechat-draft-publisher/README.md` 中相关文案从 "Claude Code Skill" 改为 "Hermes Agent 技能（Skill）"

### 6. 文档与示例

- 中英文 README 中所有 `/root/.claude/skills/...` 已全部替换为 `~/.hermes/skills/...`
- 新增「ComfyUI 生图配置」一节，明确告知用户**默认配置中的 `comfyui_output_dir` 是作者本机路径，需要改成自己的**
- 项目结构图重写，与实际目录一一对应

> 如果你来自原始仓库、想沿用 Gemini / DALL-E 流程，对应脚本（`generate_image.py` 等）依然保留在两个写作 skill 的 `scripts/` 目录下，配置方式见 `references/api-configuration.md`。

---

## 📝 更新日志

### v3.0.0 (2026-06-22) · Hermes 迁移版
- 🔁 整体从 Claude Code Skills 迁移到 **Hermes Agent**：所有路径 `~/.claude/skills/` → `~/.hermes/skills/`，移除 `allowed-tools` frontmatter，工具调用改为 `web_search` / `web_extract` / `write_file` 等 Hermes 工具名
- 🖼️ **默认生图后端从 Gemini/DALL-E 切换为本地 ComfyUI**，新增 `scripts/comfyui_gen.py` + `templates/image_z_image.json`，配置走 `config.json`，旧脚本保留为备选
- 🧠 `comfyui_gen.py` 通过 KSampler 的 positive/negative 引用反查节点 ID，精确注入提示词，对"模板提示词留空"的 workflow 同样有效
- 🛡️ ComfyUI 未启动时**不再静默退回**，先告知用户、由用户选择手动启动或改用 Hermes 内置 `image_generate`
- 📐 统一封面图（2.35:1, 1024×432）与内容/结构图（4:3, 1024×768）的尺寸约定
- 📦 强化"每个 skill 可独立安装"原则：两个写作 skill 各自内嵌一份完整的 ComfyUI 生图脚本和模板
- 🧹 移除 product-manager-writer 中关于 Gemini 代理 / JPEG vs PNG / 密钥配置 / 提示词长度的大段注意事项（已不再相关）
- 📚 详见上方「与原始版本的区别」一节

### v2.0.0 (2026-01-16)
- 🚀 新增 `WeChat Product Manager Writer` (AI 产品经理写作助手)
- 🎨 支持强制生成内容结构图与专业封面
- 📂 重构项目结构，支持四大核心功能
- 🐛 修复了一些渲染问题
- 🐛 修复了微信公众号兼容性问题

### v1.0.0 (2025-12-28)
- ✅ 发布三个核心工具
- ✅ 完善文档体系
- ✅ 优化用户体验

---

## 📄 许可证

MIT License - 供个人和商业使用

---

## 🙏 致谢

感谢以下开源项目：
- [Python-Markdown](https://python-markdown.github.io/)
- [BeautifulSoup4](https://www.crummy.com/software/BeautifulSoup/)
- [Requests](https://requests.readthedocs.io/)

---

**祝你使用愉快！** 🎉

如有问题或建议，欢迎通过 GitHub Issues 反馈！
