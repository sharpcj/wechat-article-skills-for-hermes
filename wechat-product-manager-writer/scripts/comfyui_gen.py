#!/usr/bin/env python3
"""
ComfyUI 生图 API Wrapper

用法:
    # 默认 default_profile=auto：根据 prompt 是否含中文自动选 z-image / flux2
    python3 comfyui_gen.py --prompt "你的提示词"

    # 显式指定 profile
    python3 comfyui_gen.py --prompt "..." --profile flux2
    python3 comfyui_gen.py --prompt "..." --profile z-image

    # 直接指定 workflow 文件（跳过 profile，向后兼容）
    python3 comfyui_gen.py --prompt "..." --workflow templates/image_z_image.json

    # 列出 profile
    python3 comfyui_gen.py --list-profiles

自动选择规则（在 config.json 的 auto_rules 中定义）:
    prompt 含中文（CJK 字符）→ z-image
    其他情况               → flux2

参数覆盖:
    --width / --height  覆盖空 latent 的宽高
    --seed              覆盖采样器 seed
    --negative          覆盖负向提示词
"""

import argparse
import json
import os
import re
import sys
import time
import urllib.request
import urllib.error


# 配置加载优先级：环境变量 > skill 内 config.json > 内置默认值
_DEFAULTS = {
    "comfyui_url": "http://localhost:6677",
    "comfyui_output_dir": os.path.expanduser("~/comfyui_output"),
    "default_profile": "auto",
    "auto_rules": {
        "contains_cjk": "z-image",
        "fallback": "flux2",
    },
    "profiles": {
        "z-image": {
            "workflow": "templates/image_z_image.json",
            "description": "Z-Image (Qwen3-4B CLIP + AuraFlow), 中文文字渲染更稳",
        },
        "flux2": {
            "workflow": "templates/image_flux2_text_to_image_9b.json",
            "description": "FLUX.2 9B (SamplerCustomAdvanced + Flux2 latent), 非中文场景画质更好",
        },
    },
}


def _skill_dir() -> str:
    """脚本位于 <skill>/scripts/comfyui_gen.py，上跳一层即 skill 目录。"""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _load_config() -> dict:
    """读取 skill 根目录的 config.json。profiles / auto_rules 做合并而不是整体覆盖。"""
    cfg = {
        "comfyui_url": _DEFAULTS["comfyui_url"],
        "comfyui_output_dir": _DEFAULTS["comfyui_output_dir"],
        "default_profile": _DEFAULTS["default_profile"],
        "auto_rules": dict(_DEFAULTS["auto_rules"]),
        "profiles": {k: dict(v) for k, v in _DEFAULTS["profiles"].items()},
    }
    cfg_path = os.path.join(_skill_dir(), "config.json")
    try:
        with open(cfg_path, encoding="utf-8") as f:
            data = json.load(f)
        for k in ("comfyui_url", "comfyui_output_dir", "default_profile"):
            if data.get(k):
                cfg[k] = data[k]
        if isinstance(data.get("auto_rules"), dict):
            cfg["auto_rules"].update(data["auto_rules"])
        if isinstance(data.get("profiles"), dict):
            for name, p in data["profiles"].items():
                if isinstance(p, dict):
                    cfg["profiles"].setdefault(name, {}).update(p)
    except (FileNotFoundError, json.JSONDecodeError):
        pass

    # 环境变量优先级最高
    cfg["comfyui_url"] = os.environ.get("COMFYUI_URL", cfg["comfyui_url"])
    cfg["comfyui_output_dir"] = os.environ.get(
        "COMFYUI_OUTPUT_DIR", cfg["comfyui_output_dir"]
    )
    cfg["default_profile"] = os.environ.get(
        "COMFYUI_PROFILE", cfg["default_profile"]
    )
    output_dir = cfg["comfyui_output_dir"] or ""
    cfg["comfyui_output_dir"] = os.path.expanduser(os.path.expandvars(output_dir))
    return cfg


_CONFIG = _load_config()
COMFYUI_URL = _CONFIG["comfyui_url"]
OUTPUT_DIR = _CONFIG["comfyui_output_dir"]
DEFAULT_PROFILE = _CONFIG["default_profile"]
AUTO_RULES = _CONFIG["auto_rules"]
PROFILES = _CONFIG["profiles"]
POLL_INTERVAL = 2  # 秒
DEFAULT_TIMEOUT = 600  # 秒

# 直接挂 positive/negative 的采样器节点
DIRECT_SAMPLER_CLASSES = ("KSampler", "KSamplerAdvanced")
# 通过 guider 链式追溯的采样器节点（SamplerCustomAdvanced → CFGGuider → CLIPTextEncode）
CUSTOM_SAMPLER_CLASSES = ("SamplerCustomAdvanced",)
GUIDER_CLASSES = ("CFGGuider", "BasicGuider", "DualCFGGuider")
# 脚本能识别的空 latent 节点（覆盖 width/height）
EMPTY_LATENT_CLASSES = (
    "EmptySD3LatentImage",
    "EmptyLatentImage",
    "EmptyFlux2LatentImage",
)
# 噪声/seed 节点（seed 字段名在不同节点里不同）
SEED_NODE_FIELDS = {
    "KSampler": "seed",
    "KSamplerAdvanced": "noise_seed",
    "RandomNoise": "noise_seed",
}

CJK_PATTERN = re.compile(r"[\u3400-\u9fff\uf900-\ufaff]")


def contains_cjk(text: str) -> bool:
    """检测字符串是否包含中日韩统一表意文字（覆盖常用汉字范围）。"""
    return bool(text and CJK_PATTERN.search(text))


def resolve_profile(profile_name: str, prompt: str) -> str:
    """处理 'auto' 档：根据 prompt 内容决定走哪个真实 profile。其他名字直接返回。"""
    if profile_name != "auto":
        return profile_name

    target_cjk = AUTO_RULES.get("contains_cjk")
    target_fallback = AUTO_RULES.get("fallback")

    if contains_cjk(prompt):
        chosen = target_cjk
        reason = "prompt 含中文"
    else:
        chosen = target_fallback
        reason = "prompt 不含中文"

    if not chosen or chosen not in PROFILES:
        available = ", ".join(sorted(p for p in PROFILES.keys() if p != "auto")) or "(空)"
        print(
            f"ERROR: auto 规则解析失败（{reason} → '{chosen}'），"
            f"该 profile 未在 profiles 中定义。\n       可用 profile: {available}",
            file=sys.stderr,
        )
        sys.exit(1)

    print(f"[INFO] auto 选择 profile: {chosen}（{reason}）", file=sys.stderr)
    return chosen


def resolve_workflow_path(workflow_arg, profile: str) -> str:
    """
    决定最终用哪个 workflow 文件：

    - 显式 --workflow 优先（保留向后兼容）
    - 否则用 profile 在 profiles 表中查
    """
    if workflow_arg:
        return workflow_arg

    if profile not in PROFILES:
        available = ", ".join(sorted(PROFILES.keys())) or "(空)"
        print(
            f"ERROR: profile '{profile}' 未在 config.json 的 profiles 中定义。"
            f"\n       可用 profile: {available}",
            file=sys.stderr,
        )
        sys.exit(1)

    wf = PROFILES[profile].get("workflow")
    if not wf:
        print(f"ERROR: profile '{profile}' 缺少 'workflow' 字段", file=sys.stderr)
        sys.exit(1)
    return wf


def submit_prompt(workflow: dict) -> str:
    """提交生图任务，返回 prompt_id"""
    body = json.dumps({"prompt": workflow}).encode("utf-8")
    req = urllib.request.Request(
        f"{COMFYUI_URL}/prompt",
        data=body,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        print(f"ERROR: ComfyUI 返回错误 ({e.code}): {error_body}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as e:
        print(
            f"ERROR: 无法连接 ComfyUI ({COMFYUI_URL})，请确认 ComfyUI 已启动",
            file=sys.stderr,
        )
        print(f"  详细: {e.reason}", file=sys.stderr)
        sys.exit(1)

    if "error" in result:
        print(f"ERROR: {result['error']}", file=sys.stderr)
        sys.exit(1)

    prompt_id = result["prompt_id"]
    print(f"[INFO] 任务已提交, prompt_id={prompt_id}", file=sys.stderr)
    return prompt_id


def wait_for_result(prompt_id: str, timeout: int) -> dict:
    """轮询等待生图完成，返回 history 中该 prompt 的输出"""
    start = time.time()
    while time.time() - start < timeout:
        time.sleep(POLL_INTERVAL)
        try:
            with urllib.request.urlopen(f"{COMFYUI_URL}/history/{prompt_id}") as resp:
                history = json.loads(resp.read())
        except urllib.error.URLError:
            continue

        if prompt_id in history:
            status = history[prompt_id].get("status", {})
            if status.get("completed", True):
                return history[prompt_id]
            else:
                elapsed = int(time.time() - start)
                print(f"[INFO] 等待中... ({elapsed}s)", file=sys.stderr)

    print(f"ERROR: 超时 ({timeout}s)，任务可能仍在执行", file=sys.stderr)
    sys.exit(1)


def extract_output_paths(history_entry: dict) -> list:
    """从 history 条目中提取所有输出图片的本地路径"""
    paths = []
    outputs = history_entry.get("outputs", {})
    for node_id, node_output in outputs.items():
        for img in node_output.get("images", []):
            filename = img["filename"]
            subfolder = img.get("subfolder", "")
            if subfolder:
                path = f"{OUTPUT_DIR}/{subfolder}/{filename}"
            else:
                path = f"{OUTPUT_DIR}/{filename}"
            paths.append(path)
    return paths


def _find_prompt_node_ids(workflow: dict):
    """
    扫描 workflow，反查正向 / 负向 CLIPTextEncode 节点的 id。

    支持两种结构：
      A. KSampler / KSamplerAdvanced 直接挂 positive / negative
      B. SamplerCustomAdvanced.guider → CFGGuider/BasicGuider.positive/negative
    """
    positive_ids = set()
    negative_ids = set()
    sampler_found = False

    for node_id, node in workflow.items():
        ct = node.get("class_type", "")
        inputs = node.get("inputs", {})

        if ct in DIRECT_SAMPLER_CLASSES:
            sampler_found = True
            pos = inputs.get("positive")
            neg = inputs.get("negative")
            if isinstance(pos, list) and pos:
                positive_ids.add(str(pos[0]))
            if isinstance(neg, list) and neg:
                negative_ids.add(str(neg[0]))

        elif ct in CUSTOM_SAMPLER_CLASSES:
            sampler_found = True
            guider_ref = inputs.get("guider")
            if isinstance(guider_ref, list) and guider_ref:
                gid = str(guider_ref[0])
                gnode = workflow.get(gid, {})
                if gnode.get("class_type") in GUIDER_CLASSES:
                    g_inputs = gnode.get("inputs", {})
                    pos = g_inputs.get("positive")
                    neg = g_inputs.get("negative")
                    if isinstance(pos, list) and pos:
                        positive_ids.add(str(pos[0]))
                    if isinstance(neg, list) and neg:
                        negative_ids.add(str(neg[0]))

    return positive_ids, negative_ids, sampler_found


def load_workflow(path: str, prompt: str, negative=None, **overrides) -> dict:
    """加载 workflow 模板并注入参数

    支持两类 workflow 结构：KSampler 直接挂提示词，SamplerCustomAdvanced + CFGGuider 链式。
    """
    resolved = path
    if not os.path.isabs(path) and not os.path.exists(path):
        alt = os.path.join(_skill_dir(), path)
        if os.path.exists(alt):
            resolved = alt

    if not os.path.exists(resolved):
        print(f"ERROR: workflow 文件不存在: {path}", file=sys.stderr)
        sys.exit(1)

    with open(resolved, encoding="utf-8") as f:
        workflow = json.load(f)

    # 1. 找到正向 / 负向 CLIPTextEncode 节点 id
    positive_ids, negative_ids, sampler_found = _find_prompt_node_ids(workflow)

    # 2. 注入提示词，并按需覆盖 width/height/seed
    for node_id, node in workflow.items():
        class_type = node.get("class_type", "")
        inputs = node.get("inputs", {})

        if class_type == "CLIPTextEncode":
            if node_id in positive_ids:
                inputs["text"] = prompt
                print(f"[INFO] 已注入正向提示词到节点 {node_id}", file=sys.stderr)
            elif node_id in negative_ids and negative is not None:
                inputs["text"] = negative
                print(f"[INFO] 已注入负向提示词到节点 {node_id}", file=sys.stderr)

        if class_type in EMPTY_LATENT_CLASSES:
            if overrides.get("width") is not None:
                inputs["width"] = overrides["width"]
            if overrides.get("height") is not None:
                inputs["height"] = overrides["height"]

        if class_type in SEED_NODE_FIELDS and overrides.get("seed") is not None:
            field = SEED_NODE_FIELDS[class_type]
            inputs[field] = overrides["seed"]

    if not sampler_found:
        all_samplers = DIRECT_SAMPLER_CLASSES + CUSTOM_SAMPLER_CLASSES
        print(
            f"[WARN] workflow 中没有找到 {' / '.join(all_samplers)} 节点，"
            "提示词不会被注入。"
            "请检查 workflow 是否使用了非标准采样器节点。",
            file=sys.stderr,
        )
    elif not positive_ids:
        print(
            "[WARN] 采样器节点的 positive 字段没有解析到 CLIPTextEncode，提示词可能未注入",
            file=sys.stderr,
        )

    return workflow


def list_profiles():
    """打印所有 profile 信息。"""
    print(f"默认 profile: {DEFAULT_PROFILE}")
    if DEFAULT_PROFILE == "auto":
        cjk = AUTO_RULES.get("contains_cjk", "?")
        fb = AUTO_RULES.get("fallback", "?")
        print(f"  auto 规则：含中文 → {cjk}，否则 → {fb}")
    print()
    if not PROFILES:
        print("（config.json 中未定义任何 profile）")
        return
    print(f"{'NAME':<14} {'WORKFLOW':<46} DESCRIPTION")
    print("-" * 96)
    for name in sorted(PROFILES.keys()):
        p = PROFILES[name]
        marker = "* " if name == DEFAULT_PROFILE else "  "
        print(
            f"{marker}{name:<12} "
            f"{p.get('workflow', '(missing)'):<46} "
            f"{p.get('description', '')}"
        )


def main():
    parser = argparse.ArgumentParser(
        description="ComfyUI 生图 API Wrapper（profile 切换 + 中文自动判定）",
    )
    parser.add_argument("--prompt", help="正向提示词")
    parser.add_argument("--negative", default=None, help="负向提示词 (可选)")
    parser.add_argument(
        "--profile",
        default=None,
        help=f"模型档案名，默认 '{DEFAULT_PROFILE}'。'auto' 时根据 prompt 是否含中文自动选择",
    )
    parser.add_argument(
        "--workflow",
        default=None,
        help="直接指定 workflow 文件（优先于 --profile，向后兼容）",
    )
    parser.add_argument("--width", type=int, default=None, help="图片宽度 (覆盖模板默认值)")
    parser.add_argument("--height", type=int, default=None, help="图片高度 (覆盖模板默认值)")
    parser.add_argument("--seed", type=int, default=None, help="随机种子 (覆盖模板默认值)")
    parser.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_TIMEOUT,
        help=f"超时秒数 (默认: {DEFAULT_TIMEOUT})",
    )
    parser.add_argument(
        "--list-profiles",
        action="store_true",
        help="列出所有可用 profile 后退出",
    )
    args = parser.parse_args()

    if args.list_profiles:
        list_profiles()
        return

    if not args.prompt:
        parser.error("缺少必需参数 --prompt")

    # 解析 profile：先按显式名拿，"auto" 时再根据 prompt 判定
    profile = args.profile or DEFAULT_PROFILE
    profile = resolve_profile(profile, args.prompt)
    workflow_path = resolve_workflow_path(args.workflow, profile)

    overrides = {}
    if args.width is not None:
        overrides["width"] = args.width
    if args.height is not None:
        overrides["height"] = args.height
    if args.seed is not None:
        overrides["seed"] = args.seed

    workflow = load_workflow(
        workflow_path, args.prompt, negative=args.negative, **overrides
    )
    prompt_id = submit_prompt(workflow)
    result = wait_for_result(prompt_id, args.timeout)
    paths = extract_output_paths(result)
    if not paths:
        print("ERROR: 未找到输出图片", file=sys.stderr)
        sys.exit(1)

    for p in paths:
        print(p)


if __name__ == "__main__":
    main()
