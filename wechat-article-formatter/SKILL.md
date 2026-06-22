---
name: wechat-article-formatter
description: 将 Markdown 文章转换为美化的 HTML 格式，适配微信公众号发布；YAML 主题系统，多套精调样式，纯手写解析器零外部 Markdown 依赖。当用户说"美化这篇文章"、"把这篇 Markdown 转成公众号 HTML"、"转换为 HTML"、"优化公众号格式"、"排版一下准备发公众号"时，应使用本技能；通常在文章正文写好之后、发布之前这一步触发。
---

# 微信公众号文章格式化工具

**目标**：将 Markdown 文章转换为适配微信公众号的精美 HTML，所有样式 inline，可直接粘贴到微信编辑器。

**核心价值**：YAML 主题系统 + 纯手写 Markdown 解析器，对 h1-h4、段落、加粗、斜体、引用、列表、分割线、图片、代码块等十几个元素逐一精调 CSS，变量替换机制支持一键换色。

---

## 内置主题

| 主题 | 风格 | 适用场景 |
|------|------|---------|
| `default` | 经典蓝 — 沉稳大气，色块小标题 | 科技、商业、通用 |
| `grace` | 优雅紫 — 柔和圆润，左边框小标题 | 文化、美学 |
| `modern` | 暖橙 — 活力大胆，色块小标题 | 自媒体、创业 |
| `simple` | 极简黑 — 极度克制，大量留白 | 思想深度、学术 |

每个主题包含：标题样式（h1-h4）、段落、引用块、列表、分割线、图片、代码块、链接、强调色等完整规则。

---

## 执行流程

### 步骤1：获取输入文件

| 场景 | 如何处理 |
|------|---------|
| 用户提供文件路径 | 直接使用该路径 |
| 用户粘贴 Markdown 内容 | 先用 Write 工具保存为 .md 文件 |
| 刚使用过 wechat-tech-writer | 自动查找最新生成的 .md 文件 |
| 用户只说"美化文章" | 询问用户：文件路径或粘贴内容 |

### 步骤2：选择主题

**自动选择逻辑**：
- 技术文章、含代码块 → `default`（经典蓝）
- 文化、美学类 → `grace`（优雅紫）
- 自媒体、创业类 → `modern`（暖橙）
- 思想深度、学术类 → `simple`（极简黑）

不确定时询问用户偏好。

### 步骤3：执行转换

```bash
cd ~/.hermes/skills/wechat-article-formatter

# 标准转换（使用 default 主题）
python scripts/markdown_to_html.py --input article.md

# 指定主题
python scripts/markdown_to_html.py --input article.md --theme grace

# 自定义主色 / 字号
python scripts/markdown_to_html.py --input article.md --theme modern --color "#A93226"
python scripts/markdown_to_html.py --input article.md --font-size 15px

# 列出可用主题
python scripts/markdown_to_html.py --list-themes

# 转换后预览
python scripts/markdown_to_html.py --input article.md --preview
```

**参数说明**：
- `--input` / `-i`：Markdown 文件路径（必需）
- `--theme`：主题名，默认 `default`
- `--color`：覆盖主色
- `--font-size`：覆盖字号
- `--output` / `-o`：输出路径（默认同名 .html）
- `--no-preformat`：跳过预格式化（中英文间距等）
- `--list-themes`：列出可用主题
- `--preview` / `-p`：转换后在浏览器打开预览

### 步骤4：代码块转换（如有代码块）

如果文章包含代码块，需要运行微信兼容转换：

```bash
python scripts/convert-code-blocks.py input.html output.html
```

这会将 `<pre><code>` 转换为 `<div>` + `<br>` + `&nbsp;` 格式（微信唯一支持的代码块格式）。

### 步骤5：质量检查

转换完成后检查：
- 标题样式是否正确
- 段落间距是否合适
- 图片路径是否正确
- 代码块格式是否正常

---

## 输出 HTML 特性

- 所有样式 inline（微信编辑器兼容）
- 正文不含文章标题：Markdown 中第一个 `#`（h1）在转换时被跳过，标题在公众号后台单独填写
- 配图标记 `![描述](路径)` 保留为 `<img>` 标签
- 图注自动从 alt 文本中提取（`：` 分隔）
- 同目录存在 `closing.md` 时自动追加到文末
- 预格式化：中英文自动加空格、ASCII 引号转中文引号、多余空行压缩

---

## 自定义主题

在 `themes/` 目录下新建 `.yaml` 文件即可：

```yaml
name: 我的品牌
description: 品牌专用排版

variables:
  primary-color: "#A93226"
  bg-accent-color: "#FFF5F5"

styles:
  h2: "font-size:18px; background:{primary-color}; color:#FFF; padding:6px 14px; border-radius:4px;"
  h3: "font-size:16px; font-weight:bold; color:{primary-color};"
  p: "font-size:15px; line-height:1.8; color:#3a3a3a; margin:10px 0;"
  strong: "color:{primary-color}; font-weight:bold;"
  blockquote: "border-left:3px solid {primary-color}; background:{bg-accent-color}; padding:12px 16px;"
  # ... 其他元素
```

保存后 `--theme my-brand` 立即可用。

---

## 与 wechat-draft-publisher 集成

完整工作流：
1. `wechat-tech-writer` → 生成文章（.md + cover.png）
2. `wechat-article-formatter` → 格式化 HTML（本 skill）
3. `wechat-draft-publisher` → 发布到微信草稿箱

---

## 常见问题

**Q: 粘贴到微信后样式丢失？**
A: 使用"粘贴"而非"粘贴并匹配样式"，或清空编辑器后重新粘贴。所有样式已 inline，微信编辑器会保留。

**Q: 代码块没有高亮？**
A: 运行 `convert-code-blocks.py` 将代码块转为微信兼容格式。

**Q: 如何自定义主题颜色？**
A: 复制 `themes/default.yaml` → 修改颜色变量 → 使用 `--theme my-theme`。
