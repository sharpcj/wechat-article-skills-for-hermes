#!/usr/bin/env python3
"""
ComfyUI 生图 API Wrapper

用法:
    # 推荐：Agent 根据"图里是否需要渲染汉字"显式指定 profile
    python3 comfyui_gen.py --prompt "..." --profile z-image   # 图里要画中文
    python3 comfyui_gen.py --prompt "..." --profile flux2     # 图里不画中文

    # 兜底：不传 --profile 时走 default_profile=auto，
    # auto 用启发式判断 prompt 是否要在"图里"渲染中文（不是 prompt 本身有没有中文字符）：
    #   - prompt 里有 "引号包裹的中文文本"          → z-image
    #   - prompt 里有 'in Chinese' / '用中文写' 等  → z-image
    #   - 其他情况                                  → flux2
    # 启发式可能漏判，所以 Agent 调用时尽量显式传 --profile。

    # 直接指定 workflow 文件（跳过 profile，向后兼容）
    python3 comfyui_gen.py --prompt "..." --workflow templates/image_z_image.json

    # 列出 profile
    python3 comfyui_gen.py --list-profiles

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
        # 启发式命中（引号包裹的中文 / 显式关键词）走哪个 profile
        "render_cjk_text": "z-image",
        # 启发式未命中走哪个 profile
        "fallback": "flux2",
    },
    "profiles": {
        "z-image": {
            "workflow": "templates/image_z_image.json",
            "description": "Z-Image (Qwen3-4B CLIP + AuraFlow), 图里需要渲染中文字符时用",
        },
        "flux2": {
            "workflow": "templates/image_flux2_text_to_image_9b.json",
            "description": "FLUX.2 9B, 图里不需要渲染中文字符时用，画质更好",
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

# auto 启发式：判断 prompt 是否需要"在图里渲染中文字符"。
# 注意：不是判断 prompt 本身有没有中文 —— 中文描述纯英文场景不算。
CJK_CHAR = re.compile(r"[\u3400-\u9fff]")
# 各类引号配对：英文单/双/反引号、中文直角引号、弯引号
_QUOTE_PAIRS = [
    ("\"", "\""),
    ("'", "'"),
    ("`", "`"),
    ("\u201c", "\u201d"),  # “ ”
    ("\u2018", "\u2019"),  # ‘ ’
    ("\u300c", "\u300d"),  # 「 」
    ("\u300e", "\u300f"),  # 『 』
]
# 显式声明"图里要画中文"的关键词，命中即视为需要渲染中文。
# 注意：只放"主动表达要画中文"的短语，不要放泛指词（如"中文文字"），否则会误命中
# "无中文文字"这类否定表达。
_EXPLICIT_CJK_HINTS = re.compile(
    r"(?i)("
    r"in chinese|chinese text|chinese characters|chinese words|chinese title|chinese subtitle|"
    r"chinese label|chinese caption|simplified chinese|"
    r"含中文|中文标题|中文副标题|中文字符|画上中文|写着.*汉字|写有.*汉字|用中文写"
    r")"
)


def prompt_implies_cjk_render(text: str) -> bool:
    """启发式：prompt 是否表达"要在图里画出中文字符"。

    命中条件（任一即可）：
      1. prompt 中存在被引号包裹的中文文本（Agent 通常用 'title "标题"' 或
         `text "世界杯足球"` 这种格式表达"这段字要画进图里"）
      2. prompt 中出现明确关键词（in Chinese / chinese text / 用中文写 等）

    不命中的典型场景：
      - 整段中文 prompt 描述一只猫 —— 没有引号包裹的中文文本，没有关键词
      - 整段英文 prompt 描述一辆车 —— 没有任何中文
    """
    if not text:
        return False

    # 1. 引号配对扫描
    for left, right in _QUOTE_PAIRS:
        idx = 0
        while True:
            start = text.find(left, idx)
            if start < 0:
                break
            end = text.find(right, start + len(left))
            # 对称引号（如 ' ' " " `）find 同字符会找到自己，需找下一个
            if left == right:
                end = text.find(right, start + len(left))
            if end < 0:
                break
            inner = text[start + len(left): end]
            if "\n" not in inner and CJK_CHAR.search(inner):
                return True
            idx = end + len(right)

    # 2. 显式关键词
    if _EXPLICIT_CJK_HINTS.search(text):
        return True

    return False


def resolve_profile(profile_name: str, prompt: str) -> str:
    """处理 'auto' 档：用启发式判断 prompt 是否需要在图里渲染中文。其他名字直接返回。"""
    if profile_name != "auto":
        return profile_name

    # 兼容旧字段名 contains_cjk（语义相同，仅命名调整）
    target_cjk = AUTO_RULES.get("render_cjk_text") or AUTO_RULES.get("contains_cjk")
    target_fallback = AUTO_RULES.get("fallback")

    if prompt_implies_cjk_render(prompt):
        chosen = target_cjk
        reason = "prompt 中检测到要在图里渲染的中文文本"
    else:
        chosen = target_fallback
        reason = "prompt 未声明要在图里渲染中文"

    if not chosen or chosen not in PROFILES:
        available = ", ".join(sorted(p for p in PROFILES.keys() if p != "auto")) or "(空)"
        print(
            f"ERROR: auto 规则解析失败（{reason} → '{chosen}'），"
            f"该 profile 未在 profiles 中定义。\n       可用 profile: {available}",
            file=sys.stderr,
        )
        sys.exit(1)

    print(f"[INFO] auto 选择 profile: {chosen}（{reason}）", file=sys.stderr)
    print(
        "[HINT] 若不准确，请在调用时显式指定 --profile z-image / --profile flux2",
        file=sys.stderr,
    )
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
        cjk = AUTO_RULES.get("render_cjk_text") or AUTO_RULES.get("contains_cjk", "?")
        fb = AUTO_RULES.get("fallback", "?")
        print(f"  auto 规则：")
        print(f"    prompt 中有引号包裹的中文 / 出现 'in Chinese' 等关键词 → {cjk}")
        print(f"    其他情况                                              → {fb}")
        print(f"  注意：这只是启发式兜底，建议 Agent 显式传 --profile")
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
