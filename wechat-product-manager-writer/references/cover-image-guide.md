# 封面图生成指南

## 快速开始

每篇文章必须生成一张封面图。首选用本地 ComfyUI（调用本技能自带的 `scripts/comfyui_gen.py`，封面比例 2.35:1）：

```bash
python3 scripts/comfyui_gen.py \
  --prompt "你的提示词" \
  --width 1024 --height 432 \
  --negative "blurry, low quality, deformed, distorted text"
```

> 备选：ComfyUI 不可用时改用 `image_generate(prompt=..., aspect_ratio="landscape")`。

---

## 配色方案速查

| 内容类型 | 配色 | 色值 |
|---------|------|------|
| AI 产品拆解 | 蓝紫渐变 | #1a1f5c → #7c3aed |
| 场景解决方案 | 绿橙渐变 | #10b981 → #f97316 |
| 效率提升实战 | 橙黄渐变 | #f97316 → #eab308 |
| 产品方法论 | 深蓝渐变 | #1e3a8a → #3b82f6 |
| 行业观察 | 蓝绿渐变 | #0891b2 → #06b6d4 |

---

## 提示词模板

### 通用模板

```
A cover image for WeChat article about [主题].

Design: gradient background from [颜色1] to [颜色2], modern tech style.

Layout: Split into two distinct zones (left 40%, right 60%).

Left zone (text area):
- Title: '[中文标题]' in white, bold font, vertically centered
- Subtitle: '[中文副标题]' in smaller font, 90% opacity, below title
- Text aligned left with comfortable padding

Right zone (visual area):
- [相关视觉元素1]
- [相关视觉元素2]
- Subtle light effects and particles
- Visual elements should not overlap with text zone

Style: modern, professional, [情绪词]
All Chinese text in simplified Chinese, clear and readable.
2.35:1 aspect ratio.
```

### 示例：AI 产品拆解

```
A cover image for WeChat article about Cursor product analysis.

Design: gradient background from deep blue (#1a1f5c) to electric purple (#7c3aed), modern tech style.

Layout: Split into two distinct zones (left 40%, right 60%).

Left zone (text area):
- Title: 'Cursor 产品拆解' in white, bold font, vertically centered
- Subtitle: '它为什么能火' in smaller font, 90% opacity, below title
- Text aligned left with comfortable padding

Right zone (visual area):
- 3D code editor interface icon with glowing AI elements
- Floating puzzle pieces representing product analysis
- Subtle light effects and particles
- Visual elements should not overlap with text zone

Style: modern, professional, analytical vibe
All Chinese text in simplified Chinese, clear and readable.
2.35:1 aspect ratio.
```

### 示例：场景解决方案

```
A cover image for WeChat article about building chatbot with Dify.

Design: gradient background from green (#10b981) to orange (#f97316).

Layout: Split into two distinct zones (left 40%, right 60%).

Left zone (text area):
- Title: '用 Dify 搭客服机器人' in white, bold font, vertically centered
- Subtitle: '从 0 到 1 的实战记录' in smaller font, 90% opacity, below title
- Text aligned left with comfortable padding

Right zone (visual area):
- Chat bubble icons
- Simple robot/AI assistant illustration
- Document/knowledge base icon
- Visual elements should not overlap with text zone

Style: friendly, practical, tutorial vibe
All Chinese text clear and readable.
2.35:1 aspect ratio.
```

### 示例：产品方法论

```
A cover image for WeChat article about AI Product Manager skills.

Design: deep blue gradient background (#1e3a8a to #3b82f6), professional mood.

Layout: Split into two distinct zones (left 40%, right 60%).

Left zone (text area):
- Title: 'AI 产品经理' in white, bold font, vertically centered
- Subtitle: '需要懂技术到什么程度' in smaller font, 90% opacity, below title
- Text aligned left with comfortable padding

Right zone (visual area):
- Balance scale icon (balancing tech and product)
- Simple brain and gear illustration
- Subtle light rays
- Visual elements should not overlap with text zone

Style: professional, thoughtful, career guidance vibe
All Chinese text clear and readable.
2.35:1 aspect ratio.
```

---

## 视觉元素建议

| 内容类型 | 推荐元素 |
|---------|---------|
| AI 产品拆解 | 产品 logo 元素、拆解/分解图标、放大镜 |
| 场景解决方案 | 场景图标、流程箭头、工具图标 |
| 效率提升实战 | 速度感、工具图标、进度条 |
| 产品方法论 | 思维导图、天平、脑图 |
| 行业观察 | 趋势箭头、新闻图标、图表 |

---

## 质量检查

生成后确认：

- [ ] 中文文字清晰可读，无乱码
- [ ] 颜色鲜明，有吸引力
- [ ] 标题是视觉焦点
- [ ] 整体符合文章主题

---

## 常见问题

**中文乱码**：在提示词中强调 "All Chinese text in simplified Chinese, clear and readable"

**文字和图像重叠**：确保使用 "Layout: Split into two distinct zones" 并强调 "Visual elements should not overlap with text zone"

**画面太杂**：减少视觉元素数量，保持简洁

**生成方式**：
- 首选本地 ComfyUI（本技能自带 `scripts/comfyui_gen.py`），封面比例 2.35:1 → `--width 1024 --height 432`；备选 Hermes 内置 `image_generate`（`aspect_ratio="landscape"`）
- 中文反复出错时，强化提示词里的简体中文要求，或减少封面文字
