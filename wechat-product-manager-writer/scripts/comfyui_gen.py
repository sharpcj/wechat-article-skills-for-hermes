#!/usr/bin/env python3
"""
ComfyUI 生图 API Wrapper
用法:
    python3 comfyui_gen.py --prompt "你的提示词" --workflow /path/to/workflow.json
    python3 comfyui_gen.py --prompt "..." --workflow ... --width 1024 --height 768 --seed 42
"""

import argparse
import json
import os
import sys
import time
import urllib.request
import urllib.error


# 配置加载优先级：环境变量 > skill 内 config.json > 内置默认值
_DEFAULTS = {
    "comfyui_url": "http://localhost:6677",
    "comfyui_output_dir": os.path.expanduser("~/comfyui_output"),
}


def _load_config() -> dict:
    """读取 skill 根目录的 config.json（脚本位于 <skill>/scripts/ 下）。"""
    cfg = dict(_DEFAULTS)
    cfg_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "config.json",
    )
    try:
        with open(cfg_path, encoding="utf-8") as f:
            data = json.load(f)
        for k in _DEFAULTS:
            if data.get(k):
                cfg[k] = data[k]
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    # 环境变量优先级最高
    cfg["comfyui_url"] = os.environ.get("COMFYUI_URL", cfg["comfyui_url"])
    cfg["comfyui_output_dir"] = os.environ.get(
        "COMFYUI_OUTPUT_DIR", cfg["comfyui_output_dir"]
    )
    # 允许配置 / 环境变量中用 ~ 或 $HOME 写法
    cfg["comfyui_output_dir"] = os.path.expanduser(
        os.path.expandvars(cfg["comfyui_output_dir"])
    )
    return cfg


_CONFIG = _load_config()
COMFYUI_URL = _CONFIG["comfyui_url"]
OUTPUT_DIR = _CONFIG["comfyui_output_dir"]
POLL_INTERVAL = 2  # 秒
DEFAULT_TIMEOUT = 600  # 秒


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
        print(f"ERROR: 无法连接 ComfyUI ({COMFYUI_URL})，请确认 ComfyUI 已启动", file=sys.stderr)
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


def extract_output_paths(history_entry: dict) -> list[str]:
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


def load_workflow(path: str, prompt: str, negative: "str | None" = None, **overrides) -> dict:
    """加载 workflow 模板并注入参数

    提示词注入策略：通过 KSampler 节点的 positive / negative 引用反查出真正的
    正向 / 负向 CLIPTextEncode 节点，精确注入。不依赖节点 text 是否为空，
    因此对“模板里正负向提示词都留空”的工作流同样有效。
    """
    # 相对路径优先按当前 cwd 解析；找不到时回退到 skill 目录（脚本上级），
    # 这样不论在哪个 cwd 调用都能找到本 skill 自带的 templates/。
    resolved = path
    if not os.path.isabs(path) and not os.path.exists(path):
        skill_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        alt = os.path.join(skill_dir, path)
        if os.path.exists(alt):
            resolved = alt

    with open(resolved, encoding="utf-8") as f:
        workflow = json.load(f)

    # 1. 先定位 KSampler，拿到正向/负向提示词节点的 id
    positive_ids = set()
    negative_ids = set()
    for node_id, node in workflow.items():
        if node.get("class_type") == "KSampler":
            inputs = node.get("inputs", {})
            pos = inputs.get("positive")
            neg = inputs.get("negative")
            # 引用形如 ["76:67", 0]
            if isinstance(pos, list) and pos:
                positive_ids.add(str(pos[0]))
            if isinstance(neg, list) and neg:
                negative_ids.add(str(neg[0]))

    # 2. 注入提示词
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

        # 覆盖 width/height（EmptySD3LatentImage 或 EmptyLatentImage）
        if class_type in ("EmptySD3LatentImage", "EmptyLatentImage"):
            if "width" in overrides and overrides["width"] is not None:
                inputs["width"] = overrides["width"]
            if "height" in overrides and overrides["height"] is not None:
                inputs["height"] = overrides["height"]

        # 覆盖 seed（KSampler 节点）
        if class_type == "KSampler":
            if "seed" in overrides and overrides["seed"] is not None:
                inputs["seed"] = overrides["seed"]

    if not positive_ids:
        print("[WARN] 未找到 KSampler 的 positive 引用，提示词可能未注入", file=sys.stderr)

    return workflow


def main():
    parser = argparse.ArgumentParser(description="ComfyUI 生图 API Wrapper")
    parser.add_argument("--prompt", required=True, help="正向提示词")
    parser.add_argument("--negative", default=None, help="负向提示词 (可选)")
    parser.add_argument("--workflow", default="templates/image_z_image.json", help="Workflow 模板文件路径（默认: templates/image_z_image.json，相对路径找不到时回退到 skill 目录）")
    parser.add_argument("--width", type=int, default=None, help="图片宽度 (覆盖模板默认值)")
    parser.add_argument("--height", type=int, default=None, help="图片高度 (覆盖模板默认值)")
    parser.add_argument("--seed", type=int, default=None, help="随机种子 (覆盖模板默认值)")
    parser.add_argument("--timeout", type=int, default=DEFAULT_TIMEOUT, help=f"超时秒数 (默认: {DEFAULT_TIMEOUT})")
    args = parser.parse_args()

    # 构建 overrides
    overrides = {}
    if args.width is not None:
        overrides["width"] = args.width
    if args.height is not None:
        overrides["height"] = args.height
    if args.seed is not None:
        overrides["seed"] = args.seed

    # 1. 加载并注入
    workflow = load_workflow(args.workflow, args.prompt, negative=args.negative, **overrides)

    # 2. 提交
    prompt_id = submit_prompt(workflow)

    # 3. 等待
    result = wait_for_result(prompt_id, args.timeout)

    # 4. 输出路径
    paths = extract_output_paths(result)
    if not paths:
        print("ERROR: 未找到输出图片", file=sys.stderr)
        sys.exit(1)

    for p in paths:
        print(p)


if __name__ == "__main__":
    main()
