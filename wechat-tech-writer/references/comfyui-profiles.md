# ComfyUI 模型 Profile 切换指南

> 适用于两个 writer skill：`wechat-tech-writer/` 和 `wechat-product-manager-writer/`。

## 一、机制概览

`scripts/comfyui_gen.py` 用 **profile（模型档案）** 选 workflow，并支持 **`auto` 档**做启发式兜底。

`config.json` 结构：

```json
{
  "comfyui_url": "http://localhost:6677",
  "comfyui_output_dir": "~/comfyui_output",
  "default_profile": "auto",
  "auto_rules": {
    "render_cjk_text": "z-image",
    "fallback": "flux2"
  },
  "profiles": {
    "z-image": {
      "workflow": "templates/image_z_image.json",
      "description": "Z-Image, 图里需要渲染中文字符时用"
    },
    "flux2": {
      "workflow": "templates/image_flux2_text_to_image_9b.json",
      "description": "FLUX.2 9B, 图里不需要渲染中文字符时用，画质更好"
    }
  }
}
```

### 核心判断标准

**选哪个 profile，看"最终图里是否需要渲染汉字"，跟 prompt 本身用什么语言写没关系。**

举例：

| Prompt | 图里要画中文吗 | 选哪个 |
|--------|--------------|--------|
| `A photo of a billboard with Chinese text "世界杯足球"` | 要（广告牌上有中文） | z-image |
| `一张猫在桌子上的照片，工作室光线` | 不要（虽然 prompt 是中文，但图里没字） | flux2 |
| `Cover with title "探索 AI 编程" in Chinese` | 要 | z-image |
| `A cute cat on the desk, studio lighting` | 不要 | flux2 |
| `一张广告牌，上面有英文 World Cup 字样` | 不要（中文 prompt 描述英文图） | flux2 |
| `封面图，主标题：探索 AI` | 要（封面带中文标题） | z-image |

### 推荐做法：Agent 显式传 `--profile`

```bash
# 图里要画中文（封面标题/副标题、广告牌中文字、海报标语）
python3 scripts/comfyui_gen.py --prompt "..." --profile z-image

# 图里不画中文（场景图、抽象插画、纯英文标题）
python3 scripts/comfyui_gen.py --prompt "..." --profile flux2
```

封面图通常带中文标题、内容结构图必然含大量中文 → 都直接用 `--profile z-image`。
纯英文场景图、抽象配图 → 直接用 `--profile flux2`。

### 兜底：auto 启发式

不传 `--profile` 时走 `default_profile=auto`，脚本用以下启发式判断 prompt 是否声明"要在图里画中文"：

1. **prompt 中存在被引号包裹的中文文本** —— 常见格式如 `title "标题"`、`text "世界杯足球"`、`「中文金句」`
   - 支持的引号：英文 `"..."` `'...'` \`...\`、中文 `"..."` `'...'` `「...」` `『...』`
2. **prompt 中出现明确关键词** —— `in Chinese` / `chinese text` / `chinese title` / `用中文写` / `中文标题` 等

任一命中 → `z-image`；都没命中 → `flux2`。

每次 auto 选择会在 stderr 打印：
```
[INFO] auto 选择 profile: z-image（prompt 中检测到要在图里渲染的中文文本）
[HINT] 若不准确，请在调用时显式指定 --profile z-image / --profile flux2
```

启发式有边角 case 漏判（比如纯中文描述但意图是"图里要画中文"），所以 **Agent 调用时尽量显式传 `--profile`，不要依赖 auto**。

### 显式切换

```bash
# 环境变量临时改默认 profile
COMFYUI_PROFILE=flux2 python3 scripts/comfyui_gen.py --prompt "..."

# 查看已配置的所有 profile
python3 scripts/comfyui_gen.py --list-profiles

# 直接指定 workflow 文件（跳过 profile，向后兼容旧调用方式）
python3 scripts/comfyui_gen.py --prompt "..." --workflow templates/image_z_image.json
```

### 永久切换默认模型

把 `default_profile` 改成想要的 profile 名（如 `"z-image"` / `"flux2"` / `"auto"`）。

## 二、脚本对 workflow 的硬约定

新模板必须满足以下条件才能被脚本注入提示词 / 宽高 / seed：

### 提示词节点：`CLIPTextEncode`

脚本通过下面两种采样器结构反查正向 / 负向 CLIPTextEncode 节点：

1. **直接挂法**（z-image、SDXL、SD1.5 通用）：
   - `KSampler` 或 `KSamplerAdvanced` 的 `positive` / `negative` 字段直接指向 CLIPTextEncode
2. **CFGGuider 链式法**（flux2、Flux schnell、SD3 部分模板）：
   - `SamplerCustomAdvanced.guider` → `CFGGuider` / `BasicGuider` / `DualCFGGuider`
   - 由 Guider 节点的 `positive` / `negative` 指向 CLIPTextEncode

### 空 latent 节点（覆盖宽高）

- `EmptyLatentImage`（SD1.5/SDXL）
- `EmptySD3LatentImage`（SD3/Z-Image）
- `EmptyFlux2LatentImage`（FLUX.2）

### Seed 注入

| 节点类型 | seed 字段 |
|---------|----------|
| `KSampler` | `seed` |
| `KSamplerAdvanced` | `noise_seed` |
| `RandomNoise`（Flux2 等用） | `noise_seed` |

主流 SDXL / Flux / SD3 / Z-Image workflow 通常都满足这些条件。**例外**：

- 用了 `T5TextEncode` / `FluxTextEncode` 等非标准编码节点 → 提示词不会注入
- 用了完全自定义的 latent / sampler 节点 → 宽高 / seed 覆盖失效

遇到这两种情况，需要把 workflow 改回标准节点，或者扩展脚本里的 `EMPTY_LATENT_CLASSES` / `DIRECT_SAMPLER_CLASSES` / `CUSTOM_SAMPLER_CLASSES` / `GUIDER_CLASSES` / `SEED_NODE_FIELDS` 常量。

## 三、新增一个 profile 的完整流程

### 步骤 1：在 ComfyUI 网页里跑通新模型的 workflow

先用 UI 搭好工作流，手动跑一次确认能出图。

### 步骤 2：导出 API Format JSON

⚠️ **必须导出 API Format，不是普通 Save**：

1. ComfyUI 设置（齿轮图标）里勾选 **`Enable Dev mode Options`**
2. 顶部菜单出现 **`Save (API Format)`** 按钮
3. 点这个按钮保存

得到的 JSON 是扁平的 `{"node_id": {"class_type": ..., "inputs": ...}}` 结构。普通 Save 的 JSON 是 UI 图结构（带 `nodes/links`），脚本读不了。

### 步骤 3：放进 templates/ 并校验

两个 skill 各放一份（保持"每个 skill 独立可用"原则）：

```bash
cp ~/comfyui_workflows/new_model_api.json wechat-tech-writer/templates/image_new.json
cp ~/comfyui_workflows/new_model_api.json wechat-product-manager-writer/templates/image_new.json
```

快速校验是否符合脚本约定：

```bash
python3 -c "
import json
wf = json.load(open('wechat-tech-writer/templates/image_new.json'))
types = {n.get('class_type') for n in wf.values()}
direct = {'KSampler', 'KSamplerAdvanced'} & types
custom = {'SamplerCustomAdvanced'} & types
print('采样器节点:', direct or custom or '⚠️ 缺失')
print('CLIPTextEncode:', 'CLIPTextEncode' in types)
latents = {'EmptyLatentImage', 'EmptySD3LatentImage', 'EmptyFlux2LatentImage'} & types
print('空 latent:', latents or '⚠️ 缺失')
"
```

三行都正常就 OK。

### 步骤 4：在 config.json 注册 profile

编辑两份 `config.json`（两个 skill 各一份），在 `profiles` 里加一项：

```json
"new-model": {
  "workflow": "templates/image_new.json",
  "description": "新模型的简短描述"
}
```

如果想让 auto 在某种条件下也选它，对应改 `auto_rules`。比如想让所有纯英文 prompt 走新模型：

```json
"auto_rules": {
  "contains_cjk": "z-image",
  "fallback": "new-model"
}
```

### 步骤 5：冒烟测试

```bash
cd wechat-tech-writer
python3 scripts/comfyui_gen.py --list-profiles
# 应能看到 new-model

python3 scripts/comfyui_gen.py \
  --prompt "a photorealistic cat sitting on a desk, studio lighting" \
  --profile new-model \
  --width 1024 --height 768
```

如果看到 `[WARN] workflow 中没有找到 KSampler / KSamplerAdvanced / SamplerCustomAdvanced 节点`，说明 workflow 用了完全非标准的采样器节点，需要改回标准节点或扩展脚本常量。

## 四、同步两个 skill

两个 writer skill 各维护一份完全相同的 `scripts/comfyui_gen.py`、`config.json` 和 `templates/`。每次新增 profile / 改脚本：

- ✅ 复制新 workflow 到**两边** `templates/`
- ✅ 修改**两边** `config.json`
- ✅ 改脚本时同步覆盖

快速同步命令：

```bash
cp wechat-tech-writer/scripts/comfyui_gen.py wechat-product-manager-writer/scripts/comfyui_gen.py
cp wechat-tech-writer/config.json wechat-product-manager-writer/config.json
```

## 五、常见问题

**Q: 为什么不能用"prompt 是否含中文"作为判断标准？**

A: 因为我们写图片 prompt 时,中文 prompt 描述的图里可能完全没中文(比如"一只猫")，英文 prompt 描述的图里反倒可能要画中文(比如 `billboard text "世界杯足球"`)。两者无关，必须看的是"最终图里要不要渲染汉字"。

**Q: auto 启发式漏判了怎么办？**

A: 在调用时显式加 `--profile z-image` 或 `--profile flux2`。启发式只是兜底，Agent 应该尽量自己判断并显式传。

**Q: 想给 flux2 用作含中文场景的默认（反过来）？**

A: 把 `auto_rules.render_cjk_text` 改成 `"flux2"`，`fallback` 改成 `"z-image"`。但 flux 系对中文文字渲染普遍不如 z-image，不推荐这么配。

**Q: 想关掉 auto，永远手动指定？**

A: 把 `default_profile` 改成 `"z-image"` 或 `"flux2"`，并在每次调用时显式传 `--profile`。或者干脆删掉 `default_profile` 字段（脚本会用内置默认 `auto`，那还是改成 z-image 更直接）。

**Q: 我换了 unet 文件名但报"找不到模型"？**

A: 改 `templates/image_xxx.json` 里 `UNETLoader` / `CheckpointLoaderSimple` 节点的文件名字段，确保 ComfyUI 的 `models/unet/` 或 `models/checkpoints/` 下确实有该文件。

**Q: 想给不同 profile 用不同的输出尺寸默认值？**

A: 当前 config.json 不支持 per-profile 默认尺寸。要么每次显式传 `--width --height`，要么编辑对应 workflow JSON 把空 latent 节点的默认 width/height 改了。
