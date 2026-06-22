# 微信公众号文章工具集

> 🌐 **Language**: [中文](./README.md) · [English](./README.en.md)

## 📖 项目简介

一套面向微信公众号的 Hermes Agent 技能集，涵盖 **AI 写作助手（技术视角 / 产品视角）**、**Markdown → 公众号 HTML 格式化**、**草稿一键发布** 四个核心 skill。配合本地 ComfyUI 即可在本地完成「写稿 → 配图 → 排版 → 推送草稿箱」的全流程。

> 🙏 **致谢**：本仓库 fork 自上游项目 [BND-1/wechat_article_skills](https://github.com/BND-1/wechat_article_skills)（面向 Claude Code Skills），感谢原作者奠定的优秀基础。本仓库已整体迁移到 **Hermes Agent**，并将默认生图后端从 Gemini / DALL-E 切换为本地 ComfyUI。详见下方「与原始版本的区别」一节。

## ✨ 核心工具

### 1️⃣ WeChat Product Manager Writer - AI 产品经理写作助手
从 AI 产品经理视角撰写文章。涵盖 AI 产品拆解、场景解决方案、效率提升实战、产品方法论、行业观察。

**核心特性：**
- 🤖 产品思维驱动写作，第一人称、观点鲜明
- 📊 强制生成内容结构图（Graphic Recording 风格信息图）
- 🎨 强制生成专业文章封面
- 🖼️ 按需生成内容配图（12 种 Type × 9 种 Style 风格体系）
- 🎯 实战场景导向，非纯技术教程

[📚 详细文档](./wechat-product-manager-writer/SKILL.md)

---

### 2️⃣ WeChat Tech Writer - AI 技术写作助手
基于 AI 的智能技术文章写作工具，自动搜索、抓取、改写，快速生成高质量技术科普内容。

**核心特性：**
- 🤖 AI 辅助搜索与写作
- 🎨 强制生成专业文章封面
- 🖼️ 按需生成内容配图（12 种 Type × 9 种 Style 风格体系）
- 📱 面向公众号读者的通俗化表达

[📚 详细文档](./wechat-tech-writer/SKILL.md)

---

### 3️⃣ WeChat Article Formatter - 文章格式化工具
将 Markdown 文章转换为适合微信公众号的美化 HTML，所有样式 inline，可直接粘贴到微信编辑器。

**核心特性：**
- 📝 纯手写 Markdown 解析器，零外部 Markdown 依赖
- 🎨 四套 YAML 主题（经典蓝 / 优雅紫 / 暖橙 / 极简黑），支持自定义
- 🔧 变量替换机制，一键换色、换字号
- 📐 预格式化：中英文自动间距、引号转换、空行压缩
- 🧩 支持表格、代码块、嵌套列表、图注等完整元素

[📚 详细文档](./wechat-article-formatter/SKILL.md)

---

### 4️⃣ WeChat Draft Publisher - 草稿发布工具
自动将 HTML 格式的文章推送到微信公众号草稿箱。

**核心特性：**
- ✅ 自动获取和缓存 access_token
- ✅ 支持上传封面图片（`--cover` 参数）
- ✅ 作者从配置文件读取，首次运行自动询问
- ✅ 智能错误处理和重试
- ✅ 命令行 + 交互式双模式

[📚 详细文档](./wechat-draft-publisher/SKILL.md)

---

## 🖼️ 关于配图

### 配图体系：Type × Style

两个写作 skill 共享同一套内容配图体系：

- **12 种 Type**（画面构成）：concept / process / whiteboard / data-viz / comparison / architecture / mindmap / timeline / checklist / quote-card / scene / atmosphere
- **9 种 Style**（视觉风格）：扁平矢量 / 简约线条 / 蓝图 / 手绘 / 水彩 / 海报 / 温暖 / 极简 / 商务
- **自动推荐**：Agent 根据文章内容信号自动匹配 Type + Style
- **专用 Prompt 模板**：每种 Type 有独立的 prompt 构建模板

详见各 skill 的 `references/image-styles/` 目录。

### 生图方式：本地 ComfyUI

两个写作类 skill 各自内嵌 ComfyUI 调用脚本（`scripts/comfyui_gen.py`）和 workflow 模板（`templates/image_z_image.json`）：

- ✅ 调用本地 ComfyUI（默认 `http://localhost:6677`），用本地算力
- ✅ 按 KSampler 的 positive/negative 引用精确注入提示词
- ✅ 配置走各 skill 自己的 `config.json` + 环境变量覆盖
- ✅ 封面图 2.35:1（1024×432）、内容配图 4:3（1024×768）

> 设计取向：**每个 skill 都可以独立安装、独立使用**，因此两边的 `comfyui_gen.py` 是有意维护的两份副本。修改时请记得同步两边。
>
> ComfyUI 未启动时，skill 不会静默退回；它会先告诉你「本地 ComfyUI 未在线」，让你选择手动启动 ComfyUI 或改用 Hermes 内置的 `image_generate`。

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
```
帮我写一篇介绍 Claude code 的文章，并且进行格式美化，然后推送到微信公众号后台
```

**分步执行**
```bash
# 1. 写文章（自动生成封面图 cover.png）
#    对 Hermes 说：「写一篇关于 XXX 的公众号文章」

# 2. 格式化
cd wechat-article-formatter
python scripts/markdown_to_html.py --input 文章.md --theme default

# 3. 发布（封面图通过 --cover 参数上传，不插入正文）
cd ../wechat-draft-publisher
python publisher.py --title "标题" --content ../文章.html --cover ../cover.png
```

---

## 📂 项目结构

```
wechat_article_skills/
├── wechat-tech-writer/              # AI 技术写作 skill
│   ├── SKILL.md
│   ├── config.json                  # ComfyUI 配置
│   ├── scripts/
│   │   ├── comfyui_gen.py           # 本地 ComfyUI 生图（首选）
│   │   └── generate_image.py        # Gemini / DALL-E 直连（备选）
│   ├── templates/
│   │   └── image_z_image.json       # ComfyUI workflow 模板
│   └── references/
│       ├── image-styles/            # 配图风格库（Type × Style）
│       │   ├── styles.md            #   12 种 Type + 9 种 Style
│       │   ├── style-presets.md     #   按文章类型的预设组合
│       │   ├── auto-selection.md    #   自动推荐规则
│       │   └── prompt-construction.md # 每种 Type 的 prompt 模板
│       ├── cover-image-guide.md     # 封面图生成指南
│       ├── content-images-guide.md  # 内容配图指南
│       └── writing-style.md         # 写作风格指南
│
├── wechat-product-manager-writer/   # AI 产品经理视角写作 skill
│   ├── SKILL.md
│   ├── config.json
│   ├── scripts/                     # 与 tech-writer 同步维护
│   ├── templates/
│   └── references/
│       ├── image-styles/            # 配图风格库（同上结构）
│       ├── cover-image-guide.md
│       └── structure-image-guide.md # 内容结构图指南
│
├── wechat-article-formatter/        # Markdown → 公众号 HTML 排版
│   ├── SKILL.md
│   ├── scripts/
│   │   ├── markdown_to_html.py      # 核心转换脚本（纯手写解析器）
│   │   └── convert-code-blocks.py   # 代码块微信兼容转换
│   ├── themes/                      # YAML 主题文件
│   │   ├── default.yaml             #   经典蓝
│   │   ├── grace.yaml               #   优雅紫
│   │   ├── modern.yaml              #   暖橙
│   │   └── simple.yaml              #   极简黑
│   ├── templates/                   # 旧 CSS 主题（保留兼容）
│   └── examples/                    # HTML 示例模板
│
├── wechat-draft-publisher/          # HTML → 公众号草稿箱
│   ├── SKILL.md
│   ├── publisher.py                 # 核心发布脚本
│   └── scripts/                     # HTML 优化、样式修复
│
└── README.md                        # 本文件
```

---

## 💡 使用场景

### 技术博客作者
- 使用 **WeChat Tech Writer** AI 辅助生成技术内容
- 使用 **Article Formatter** 的 YAML 主题美化排版
- 使用 **Draft Publisher** 一键发布

### 产品经理 / 内容运营
- 使用 **WeChat Product Manager Writer** 从产品视角写作
- 使用 **Article Formatter** 切换主题适配不同风格
- 自动化发布流程，提升效率

### 自媒体创作者
- 在 Markdown 中专注写作
- 一键转换为精美排版
- 快速发布到公众号

---

## 📋 系统要求

- **Python**: 3.8+
- **依赖**: PyYAML（formatter 需要）
- **操作系统**: Windows / macOS / Linux
- **微信公众号**: 认证的服务号或订阅号（用于 API 发布）
- **ComfyUI（可选）**: 本地部署并启动的 ComfyUI（默认 `http://localhost:6677`），供写作 skill 生图使用

---

## 🔧 配置说明

### WeChat Draft Publisher 配置

创建配置文件 `~/.wechat-publisher/config.json`：

```json
{
  "appid": "wx1234567890abcdef",
  "appsecret": "your_appsecret_here",
  "author": "你的作者名"
}
```

- `appid` / `appsecret`：从微信公众平台「设置与开发 → 基本配置」获取
- `author`：可选，首次运行未配置时会自动询问并保存

### ComfyUI 生图配置（可选）

编辑 `wechat-tech-writer/config.json` 和 `wechat-product-manager-writer/config.json`：

```json
{
  "comfyui_url": "http://localhost:6677",
  "comfyui_output_dir": "/home/yourname/comfyui_output"
}
```

也可以用环境变量临时覆盖：

```bash
export COMFYUI_URL="http://localhost:6677"
export COMFYUI_OUTPUT_DIR="$HOME/comfyui_output"
```

> ⚠️ 仓库里默认的 `comfyui_output_dir` 是作者本机路径，**克隆后请改成你自己的目录**。

---

## 📚 文档资源

### 各工具详细文档
- [WeChat Article Formatter 技能文档](./wechat-article-formatter/SKILL.md)
- [WeChat Draft Publisher 技能文档](./wechat-draft-publisher/SKILL.md)
- [WeChat Tech Writer 技能文档](./wechat-tech-writer/SKILL.md)
- [WeChat Product Manager Writer 技能文档](./wechat-product-manager-writer/SKILL.md)

### 配图体系文档
- [正文配图风格库（Type × Style）](./wechat-tech-writer/references/image-styles/styles.md)
- [按文章类型的预设组合](./wechat-tech-writer/references/image-styles/style-presets.md)
- [自动推荐规则](./wechat-tech-writer/references/image-styles/auto-selection.md)
- [Prompt 构建指南](./wechat-tech-writer/references/image-styles/prompt-construction.md)

---

## 📝 示例文章

使用本工具集创作和发布的精选文章：

1. **[Claude Code 零基础指南：不会写代码也能做开发？看这一篇就够了，效率翻倍！](https://mp.weixin.qq.com/s/Dx-XYcj74c2LdZOWwNS7GQ)**

2. **[从70分钟到9分钟：微信公众号自动化Skills！提效狂魔！](https://mp.weixin.qq.com/s/iBKgEX_vfYNIe90qPi03Sw)**

3. **[从 Chat 到 Agent：Claude Agent SDK 才是 AI 真正的生产力开关](https://mp.weixin.qq.com/s/58nZuLJGNjm6hqfGzJg-ZA)**

4. **[Claude Skill：为什么它会取代 Dify、n8n 和 Coze？](https://mp.weixin.qq.com/s/rXl4nLI6ouJMIMfvL1iSbQ)**

> 💡 以上文章均使用本项目工具完成排版和发布。

---

## ⚠️ 注意事项

1. **API 调用限制**
   - access_token 每日获取次数有限（2000次/天）
   - 本工具自动缓存 token，请勿频繁重置

2. **图片使用规范**
   - 封面图通过 `--cover` 参数单独上传，不插入正文
   - 封面图片建议尺寸：900x500 像素
   - 图片大小不超过 2MB

3. **样式兼容性**
   - 微信编辑器对 CSS 支持有限（不支持伪元素、渐变、阴影等）
   - Formatter 输出的 HTML 所有样式已 inline，可直接粘贴
   - 代码块需运行 `convert-code-blocks.py` 转为微信兼容格式

---

## 🐛 故障排除

### 常见问题

**Q: 粘贴后样式丢失？**
- 使用 Chrome 或 Edge 浏览器
- 尝试全选复制而非部分复制
- 确保使用「粘贴」而非「粘贴并匹配样式」

**Q: access_token 获取失败？**
- 检查 AppID 和 AppSecret 是否正确
- 确认公众号已认证
- 检查 IP 白名单配置

**Q: 作者名未设置？**
- 首次运行 publisher.py 时会自动询问并保存到 `~/.wechat-publisher/config.json`
- 也可以手动编辑配置文件添加 `"author"` 字段

更多问题请查看各工具的详细文档或提交 Issue。

---

## 🔀 与原始版本的区别

本仓库 fork 自一个面向 **Claude Code** 的 WeChat Skills 项目，整体迁移到 **Hermes Agent**，并对默认生图后端、运行环境、写作视角做了一轮重构。下面是与原始版本相比的主要变化。

### 1. 运行环境：Claude Code → Hermes Agent

| 维度 | 原始版本 | 当前版本 |
|------|---------|---------|
| 目标 Agent | Claude Code Skills | Hermes Agent Skills |
| 安装目录 | `~/.claude/skills/` | `~/.hermes/skills/` |
| Frontmatter `allowed-tools` | 用 `WebSearch, WebFetch, Read, Write, Edit, Bash` | 已移除（Hermes 不需要这个字段） |
| 工具调用 | `WebSearch` / `WebFetch` / `Write` | `web_search` / `web_extract` / `browser_navigate` / `write_file` |
| skill 描述 | 较简短 | 触发词扩充，覆盖更多自然语言表达 |

### 2. 默认生图后端：Gemini / DALL-E → 本地 ComfyUI

| 维度 | 原始版本 | 当前版本 |
|------|---------|---------|
| 首选生图方式 | `generate_image.py` 直连 Gemini / DALL-E | 本地 ComfyUI（`comfyui_gen.py` + workflow 模板） |
| 配置方式 | 环境变量 `GEMINI_API_KEY` / `OPENAI_API_KEY` | 各 skill 自己的 `config.json`，支持环境变量覆盖 |
| 离线兜底 | 密钥失效就生不了图 | ComfyUI 未启动时先告知用户，由用户选择手动启动或改用 `image_generate` |
| 尺寸约定 | 各处写法不统一 | 统一：封面 2.35:1（1024×432）、内容/结构图 4:3（1024×768） |

### 3. 格式化器：CSS 主题 → YAML 主题

| 维度 | 原始版本 | 当前版本 |
|------|---------|---------|
| Markdown 解析 | Python `markdown` 库 + BeautifulSoup + cssutils | 纯手写解析器，零外部 Markdown 依赖 |
| 主题系统 | 3 套 CSS 文件 | 4 套 YAML 主题（经典蓝/优雅紫/暖橙/极简黑），支持变量替换 |
| 依赖 | 6 个 pip 包 | 1 个（PyYAML） |
| 预格式化 | 无 | 中英文间距、引号转换、空行压缩 |

### 4. 配图体系：从简单决策到 Type × Style

| 维度 | 原始版本 | 当前版本 |
|------|---------|---------|
| 配图类型 | 5 种（柱状图/架构图/对比图/流程图/雷达图） | 12 种 Type + 9 种 Style，含专用 prompt 模板 |
| 风格选择 | 手动指定 | Agent 根据文章内容信号自动推荐 |
| 配图数量 | 硬上限 0-2 张 | 按需生成，每 H2 最多 1 张，宁缺毋滥 |
| 封面图 | 插入正文 | 发布时 `--cover` 参数单独上传 |

### 5. 发布器：作者配置优化

- 作者从 `~/.wechat-publisher/config.json` 读取 `author` 字段
- 未配置时首次运行自动询问并保存
- 命令行 `--author` 参数优先级最高

### 6. 新增「AI 产品经理视角」写作 skill

`wechat-product-manager-writer/` 是相对原版新增的写作 skill：
- 第一人称、观点鲜明、实战导向
- 五类内容方向：产品拆解 / 场景解决方案 / 效率提升实战 / 产品方法论 / 行业观察
- 强制生成内容结构图（Graphic Recording 风格）

---

## 📝 更新日志

### v3.2.0 (2026-06-23)
- 🎨 Formatter 重构：用 YAML 主题系统替换 CSS + BeautifulSoup 方案，4 套精调主题
- 🖼️ 配图体系升级：引入 12 种 Type × 9 种 Style 风格库，含专用 prompt 模板和自动推荐规则
- 📝 封面图不再插入正文，发布时通过 `--cover` 参数单独上传
- 👤 发布器作者改为从配置文件读取，首次运行自动询问
- 📦 Formatter 依赖从 6 个精简为 1 个（PyYAML）

### v3.0.0 (2026-06-22) · Hermes 迁移版
- 🔁 整体从 Claude Code Skills 迁移到 **Hermes Agent**
- 🖼️ 默认生图后端从 Gemini/DALL-E 切换为本地 ComfyUI
- 🛡️ ComfyUI 未启动时不再静默退回
- 📐 统一封面图与内容/结构图的尺寸约定
- 📦 强化「每个 skill 可独立安装」原则

### v2.0.0 (2026-01-16)
- 🚀 新增 `WeChat Product Manager Writer`
- 🎨 支持强制生成内容结构图与专业封面

### v1.0.0 (2025-12-28)
- ✅ 发布三个核心工具

---

## 📄 许可证

MIT License - 供个人和商业使用

---

## 🙏 致谢

感谢以下开源项目：
- [PyYAML](https://pyyaml.org/)
- [Requests](https://requests.readthedocs.io/)

---

**祝你使用愉快！** 🎉

如有问题或建议，欢迎通过 GitHub Issues 反馈！
