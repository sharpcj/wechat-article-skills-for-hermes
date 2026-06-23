# ComfyUI 模型 Profile 切换指南

> 适用于两个 writer skill：`wechat-tech-writer/` 和 `wechat-product-manager-writer/`。

## 一、机制概览

`scripts/comfyui_gen.py` 不再硬编码 workflow，改用 **profile（模型档案）** 选 workflow，并支持 **`auto` 档**根据 prompt 自动挑模型。

`config.json` 结构：

```json
{
  "comfyui_url": "http://localhost:6677",
  "comfyui_output_dir": "~/comfyui_output",
  "default_profile": "auto",
  "auto_rules": {
    "contains_cjk": "z-image",
    "fallback": "flux2"
  },
  "profiles": {
    "z-image": {
      "workflow": "templates/image_z_image.json",
      "description": "Z-Image (Qwen3-4B CLIP + AuraFlow), 中文文字渲染更稳"
    },
    "flux2": {
      "workflow": "templates/image_flux2_text_to_image_9b.json",
      "description": "FLUX.2 9B (SamplerCustomAdvanced + Flux2 latent), 非中文场景画质更好"
    }
  }
}
```

### auto 档（默认）

`default_profile: "auto"` 表示让脚本根据 prompt 自动选 profile。规则在 `auto_rules`：

- prompt **含中文**（CJK 字符）→ `z-image`（中文文字渲染稳）
- prompt **不含中文**（纯英文）→ `flux2`（画质更好）

每次 auto 选择都会在 stderr 打印一行 `[INFO] auto 选择 profile: z-image（prompt 含中文）`，方便确认。

### 显式切换

```bash
# 强制走 flux2，无论 prompt 是否含中文
python3 scripts/comfyui_gen.py --prompt "..." --profile flux2

# 强制走 z-image
python3 scripts/comfyui_gen.py --prompt "..." --profile z-image

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

**Q: auto 把含中文混排（如"Claude Code: AI 写代码"）的 prompt 判成什么？**

A: 算含中文 → 走 z-image。CJK 检测匹配的是范围 `\u3400-\u9fff` 内任意一个字符，只要有一个汉字就触发。

**Q: 想给 flux2 用作含中文 prompt 的默认（反过来）？**

A: 把 `auto_rules.contains_cjk` 改成 `"flux2"`，`fallback` 改成 `"z-image"`。但 flux 系对中文文字渲染普遍不如 z-image，不推荐这么配。

**Q: 想关掉 auto，永远手动指定？**

A: 把 `default_profile` 改成 `"z-image"` 或 `"flux2"`，并在每次调用时显式传 `--profile`。

**Q: 我换了 unet 文件名但报"找不到模型"？**

A: 改 `templates/image_xxx.json` 里 `UNETLoader` / `CheckpointLoaderSimple` 节点的文件名字段，确保 ComfyUI 的 `models/unet/` 或 `models/checkpoints/` 下确实有该文件。

**Q: 想给不同 profile 用不同的输出尺寸默认值？**

A: 当前 config.json 不支持 per-profile 默认尺寸。要么每次显式传 `--width --height`，要么编辑对应 workflow JSON 把空 latent 节点的默认 width/height 改了。
