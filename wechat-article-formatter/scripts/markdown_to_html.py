#!/usr/bin/env python3
"""
公众号文章排版工具

将 Markdown 文章转换为微信公众号兼容的 HTML（所有样式 inline）。

主题文件位于 themes/ 目录，YAML 格式，包含 variables 和 styles 两部分。
用法：
    python markdown_to_html.py --input article.md                       主题默认 default
    python markdown_to_html.py --input article.md --theme grace         显式指定主题
    python markdown_to_html.py --input article.md --theme modern --color "#A93226"
    python markdown_to_html.py --input article.md --font-size 15px
    python markdown_to_html.py --list-themes                            列出可用主题
    python markdown_to_html.py --input article.md --preview             转换后在浏览器预览
"""

from __future__ import annotations

import argparse
import html as html_mod
import re
import sys
import webbrowser
from pathlib import Path

import yaml

SCRIPT_DIR = Path(__file__).parent
SKILL_DIR = SCRIPT_DIR.parent
THEMES_DIR = SKILL_DIR / "themes"

DEFAULT_VARIABLES = {
    "primary-color": "#0F4C81",
    "bg-accent-color": "#F0F4F8",
    "text-color": "#333333",
    "text-light": "#666666",
    "text-muted": "#999999",
    "bg-light": "#F7F7F7",
    "border-color": "#EEEEEE",
    "link-color": "#576B95",
    "font-size": "16px",
    "font-family": "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
    "line-height": "1.8",
    "paragraph-spacing": "1.5em",
}

DEFAULT_STYLES = {
    "h1": "text-align:center; font-size:22px; font-weight:bold; margin-bottom:24px;",
    "h2": "font-size:18px; font-weight:bold; margin-top:2em; margin-bottom:1em;",
    "h3": "font-size:16px; font-weight:bold; margin-top:1.5em; margin-bottom:0.8em;",
    "h4": "",
    "p": "",
    "strong": "",
    "em": "",
    "a": "",
    "blockquote": "border-left:3px solid #DDD; padding:8px 16px; margin:1em 0;",
    "ul": "",
    "ol": "",
    "li": "",
    "hr": "border:none; border-top:1px solid #EEE; margin:2em 0;",
    "img": "",
    "figcaption": "",
    "code": "",
    "pre": "",
    "strong-color": "#333333",
}


def _err(msg: str):
    print(f"[ERROR] {msg}", file=sys.stderr)
    sys.exit(1)


def _ok(msg: str):
    print(f"[OK] {msg}")


def _info(msg: str):
    print(f"[INFO] {msg}")


# ── 主题加载 ─────────────────────────────────────────────────

def _find_theme_file(name: str) -> Path | None:
    for ext in (".yaml", ".yml"):
        path = THEMES_DIR / f"{name}{ext}"
        if path.exists():
            return path
    return None


def _load_theme_file(path: Path) -> dict:
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    return data


def _load_theme(name: str) -> dict:
    path = _find_theme_file(name)
    if not path:
        available = ", ".join(t["name"] for t in _list_themes())
        _err(
            f"主题 '{name}' 不存在。\n"
            f"可用主题：{available}"
        )
    _info(f"加载主题: {path}")
    return _load_theme_file(path)


def _list_themes() -> list[dict]:
    themes = []
    if not THEMES_DIR.exists():
        return themes
    for f in sorted(THEMES_DIR.glob("*.yaml")) + sorted(THEMES_DIR.glob("*.yml")):
        name = f.stem
        data = _load_theme_file(f)
        themes.append({
            "name": name,
            "label": data.get("name", ""),
            "description": data.get("description", ""),
        })
    return themes


# ── 样式构建 ─────────────────────────────────────────────────

def _resolve_vars(template: str, variables: dict) -> str:
    result = template
    for _ in range(3):
        for key, val in variables.items():
            result = result.replace(f"{{{key}}}", str(val))
    return result


def _build_styles(theme: dict, overrides: dict | None = None) -> dict:
    variables = {**DEFAULT_VARIABLES}
    variables.update(theme.get("variables", {}))
    if overrides:
        variables.update(overrides)

    resolved = {}
    for key, val in variables.items():
        resolved[key] = _resolve_vars(str(val), variables)

    styles = {**DEFAULT_STYLES}
    styles.update(theme.get("styles", {}))
    for key, val in styles.items():
        resolved[key] = _resolve_vars(str(val), resolved)

    return resolved


# ── Markdown 预格式化 ─────────────────────────────────────────

def _preformat_markdown(text: str) -> str:
    # 中英文之间加空格
    text = re.sub(r"([\u4e00-\u9fff])([A-Za-z0-9])", r"\1 \2", text)
    text = re.sub(r"([A-Za-z0-9])([\u4e00-\u9fff])", r"\1 \2", text)

    # 中文与数字之间加空格
    text = re.sub(r"([\u4e00-\u9fff])(\d)", r"\1 \2", text)
    text = re.sub(r"(\d)([\u4e00-\u9fff])", r"\1 \2", text)

    # ASCII 引号 → 中文引号
    text = text.replace('"', '\u300c')
    # Simple heuristic: pair them up
    parts = text.split('\u300c')
    result = parts[0]
    for i, part in enumerate(parts[1:], 1):
        if i % 2 == 1:
            result += '\u300c' + part
        else:
            result += '\u300d' + part
    text = result

    # 连续多个空行 → 最多两个
    text = re.sub(r"\n{3,}", "\n\n", text)

    # 修复加粗标记中的空格问题
    text = re.sub(r"\*\* *(.+?) *\*\*", r"**\1**", text)

    return text


# ── Markdown → HTML ──────────────────────────────────────────

def _md_to_html(md_text: str, styles: dict) -> str:
    lines = md_text.strip().split("\n")
    html_parts = []
    in_list = None
    list_stack = []
    list_depth = -1
    in_blockquote = False
    in_code_block = False
    code_block_lines = []
    paragraph_lines = []
    first_h1_skipped = False

    def _p_style():
        theme_p = styles.get("p", "")
        if theme_p:
            return theme_p
        return (
            f'margin:0 0 {styles["paragraph-spacing"]} 0; '
            f'font-size:{styles["font-size"]}; '
            f'line-height:{styles["line-height"]}; '
            f'color:{styles["text-color"]};'
        )

    def flush_paragraph():
        if paragraph_lines:
            text = " ".join(paragraph_lines)
            text = _inline_format(text, styles)
            html_parts.append(f'<p style="{_p_style()}">{text}</p>')
            paragraph_lines.clear()

    def close_list():
        nonlocal in_list, list_depth
        while list_stack:
            html_parts.append(f"</{list_stack.pop()}>")
        list_depth = -1
        in_list = None

    def close_blockquote():
        nonlocal in_blockquote
        if in_blockquote:
            html_parts.append("</blockquote>")
            in_blockquote = False

    for line in lines:
        stripped = line.strip()

        # 围栏代码块
        if stripped.startswith("```"):
            if not in_code_block:
                flush_paragraph()
                close_list()
                close_blockquote()
                in_code_block = True
                code_block_lines = []
                continue
            else:
                pre_style = styles.get("pre", "") or (
                    "background:#f5f5f5; padding:16px; border-radius:4px; "
                    "font-size:13px; line-height:1.8; overflow-x:auto; color:#333;"
                )
                code_text = html_mod.escape("\n".join(code_block_lines))
                html_parts.append(
                    f'<pre style="{pre_style}"><code>{code_text}</code></pre>'
                )
                in_code_block = False
                code_block_lines = []
                continue

        if in_code_block:
            code_block_lines.append(line)
            continue

        if not stripped:
            flush_paragraph()
            close_list()
            close_blockquote()
            continue

        heading_match = re.match(r'^(#{1,4})\s+(.+)$', stripped)
        if heading_match:
            flush_paragraph()
            close_list()
            close_blockquote()
            level = len(heading_match.group(1))
            if level == 1 and not first_h1_skipped:
                first_h1_skipped = True
                continue
            text = _inline_format(heading_match.group(2), styles)
            tag = f"h{level}"
            style = styles.get(tag, "")
            html_parts.append(f'<{tag} style="{style}">{text}</{tag}>')
            continue

        if re.match(r'^---+$', stripped):
            flush_paragraph()
            close_list()
            close_blockquote()
            html_parts.append(f'<hr style="{styles.get("hr", "")}" />')
            continue

        # Markdown 表格
        if re.match(r'^\|.+\|$', stripped):
            flush_paragraph()
            close_list()
            close_blockquote()
            table_lines = [stripped]
            cur_idx = lines.index(line)
            lookahead = cur_idx + 1
            while lookahead < len(lines):
                next_s = lines[lookahead].strip()
                if re.match(r'^\|.+\|$', next_s):
                    table_lines.append(next_s)
                    lookahead += 1
                else:
                    break
            for skip_i in range(cur_idx + 1, lookahead):
                lines[skip_i] = ""
            tbl_style = styles.get("table", "") or (
                "width:100%; border-collapse:collapse; margin:1em 0; font-size:14px;"
            )
            th_style = styles.get("th", "") or (
                "background:#f5f5f5; padding:8px 14px; text-align:center; font-weight:bold;"
            )
            td_style = styles.get("td", "") or (
                "padding:8px 14px; border:1px solid #EEE; text-align:center;"
            )
            rows = []
            for tl in table_lines:
                cells = [c.strip() for c in tl.strip("|").split("|")]
                rows.append(cells)
            data_rows = [r for r in rows if not all(re.match(r'^-+$', c.strip()) for c in r)]
            if data_rows:
                table_html = f'<table style="{tbl_style}">'
                for ri, row in enumerate(data_rows):
                    table_html += "<tr>"
                    for cell in row:
                        tag = "th" if ri == 0 else "td"
                        st = th_style if ri == 0 else td_style
                        cell_text = _inline_format(cell, styles)
                        table_html += f'<{tag} style="{st}">{cell_text}</{tag}>'
                    table_html += "</tr>"
                table_html += "</table>"
                html_parts.append(table_html)
            continue

        img_match = re.match(r'^!\[(.*?)\]\((.+?)\)$', stripped)
        if img_match:
            flush_paragraph()
            alt = img_match.group(1)
            src = img_match.group(2)

            if ("封面" in alt) or alt.startswith("cover"):
                continue

            alt_escaped = html_mod.escape(alt)
            img_style = styles.get("img", "") or "max-width:100%; border-radius:4px;"
            html_parts.append(
                f'<p style="text-align:center; margin:1.5em 0;">'
                f'<img src="{src}" alt="{alt_escaped}" style="{img_style}" />'
                f'</p>'
            )
            if "：" in alt:
                caption = alt.split("：", 1)[1]
                fc_style = styles.get("figcaption", "") or (
                    f'text-align:center; font-size:14px; '
                    f'color:{styles["text-muted"]}; margin-top:-0.8em; margin-bottom:1.5em;'
                )
                html_parts.append(
                    f'<p style="{fc_style}">'
                    f'{html_mod.escape(caption)}</p>'
                )
            continue

        if stripped.startswith("> "):
            flush_paragraph()
            close_list()
            if not in_blockquote:
                html_parts.append(f'<blockquote style="{styles.get("blockquote", "")}">')
                in_blockquote = True
            text = _inline_format(stripped[2:], styles)
            html_parts.append(
                f'<p style="margin:0.3em 0; font-size:{styles["font-size"]}; '
                f'line-height:{styles["line-height"]};">{text}</p>'
            )
            continue
        elif in_blockquote:
            close_blockquote()

        # 列表项检测（支持嵌套）
        ul_match = re.match(r'^( *)[-*]\s+', line)
        ol_match = re.match(r'^( *)\d+\.\s+', line)
        if ul_match or ol_match:
            flush_paragraph()
            close_blockquote()
            list_match = ul_match or ol_match
            assert list_match is not None
            indent = len(list_match.group(1))
            level = indent // 2
            list_type = "ul" if ul_match else "ol"

            ul_style = styles.get("ul", "") or (
                f'margin:0.8em 0; padding-left:1.5em; color:{styles["text-color"]};'
            )
            ol_style = styles.get("ol", "") or (
                f'margin:0.8em 0; padding-left:1.5em; color:{styles["text-color"]};'
            )
            li_style = styles.get("li", "") or (
                f'margin:0.4em 0; font-size:{styles["font-size"]}; '
                f'line-height:{styles["line-height"]};'
            )

            while level > list_depth:
                tag = list_type
                st = ul_style if tag == "ul" else ol_style
                if list_depth >= 0:
                    st = re.sub(r'margin:[^;]+;?', '', st).strip()
                    if not st:
                        st = f'padding-left:1.5em; color:{styles["text-color"]};'
                html_parts.append(f'<{tag} style="{st}">')
                list_stack.append(tag)
                list_depth += 1

            while level < list_depth:
                if list_stack:
                    html_parts.append(f'</{list_stack.pop()}>')
                list_depth -= 1

            if list_stack and list_stack[-1] != list_type:
                html_parts.append(f'</{list_stack.pop()}>')
                st = ul_style if list_type == "ul" else ol_style
                html_parts.append(f'<{list_type} style="{st}">')
                list_stack.append(list_type)

            if not list_stack:
                st = ul_style if list_type == "ul" else ol_style
                html_parts.append(f'<{list_type} style="{st}">')
                list_stack.append(list_type)
                list_depth = 0

            if ul_match:
                raw_text = re.sub(r'^[-*]\s+', '', stripped).strip()
            else:
                raw_text = re.sub(r'^\d+\.\s+', '', stripped).strip()
            if not raw_text:
                continue
            text = _inline_format(raw_text, styles)
            html_parts.append(f'<li style="{li_style}">{text}</li>')
            in_list = list_type
            continue

        close_list()
        close_blockquote()
        paragraph_lines.append(stripped)

    flush_paragraph()
    close_list()
    close_blockquote()

    return "".join(html_parts)


def _inline_format(text: str, styles: dict) -> str:
    # strong
    strong_style = styles.get("strong", "")
    if not strong_style:
        strong_color = styles.get("strong-color", styles.get("primary-color", "#333"))
        strong_style = f"color:{strong_color}; font-weight:bold;"
    text = re.sub(
        r'\*\*(.+?)\*\*',
        rf'<strong style="{strong_style}">\1</strong>',
        text,
    )
    # em
    em_style = styles.get("em", "")
    if em_style:
        text = re.sub(r'\*(.+?)\*', rf'<em style="{em_style}">\1</em>', text)
    else:
        text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
    # strikethrough
    del_style = styles.get("del", "") or "text-decoration:line-through; color:#999;"
    text = re.sub(r'~~(.+?)~~', rf'<del style="{del_style}">\1</del>', text)
    # inline code
    code_style = styles.get("code", "")
    if not code_style:
        code_style = (
            f'background:{styles.get("bg-light", "#F7F7F7")}; padding:2px 6px; '
            f'border-radius:3px; font-size:0.9em; color:{styles.get("primary-color", "#333")};'
        )
    text = re.sub(
        r'`(.+?)`',
        rf'<code style="{code_style}">\1</code>',
        text,
    )
    # link
    a_style = styles.get("a", "")
    if not a_style:
        a_style = f'color:{styles.get("link-color", "#576B95")}; text-decoration:none;'
    text = re.sub(
        r'\[(.+?)\]\((.+?)\)',
        rf'<a style="{a_style}" href="\2">\1</a>',
        text,
    )
    return text


def _wrap_document(body_html: str, styles: dict) -> str:
    return (
        f'<section style="'
        f'font-family:{styles.get("font-family", "sans-serif")}; '
        f'font-size:{styles["font-size"]}; '
        f'line-height:{styles["line-height"]}; '
        f'color:{styles["text-color"]}; '
        f'padding:16px; text-align:left;'
        f'">\n'
        f'<!-- 标题请在微信公众号编辑器中单独填写，HTML 中已自动移除 H1 标题 -->\n'
        f'{body_html}\n'
        f'</section>'
    )


# ── CLI ──────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="公众号文章排版工具 — Markdown 转微信兼容 HTML",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("-i", "--input", help="Markdown 文件路径")
    parser.add_argument(
        "--theme",
        default="default",
        help="主题名：default（经典蓝）/ grace（优雅紫）/ modern（暖橙）/ simple（极简黑），默认 default",
    )
    parser.add_argument("--color", help="覆盖主色（如 #0F4C81）")
    parser.add_argument("--font-size", help="覆盖字号（如 16px）")
    parser.add_argument("-o", "--output", help="输出路径（默认同名 .html）")
    parser.add_argument("--no-preformat", action="store_true", help="跳过 Markdown 预格式化")
    parser.add_argument("--list-themes", action="store_true", help="列出可用主题")
    parser.add_argument("-p", "--preview", action="store_true", help="转换后在浏览器打开预览")

    args = parser.parse_args()

    if args.list_themes:
        print("可用主题：")
        for t in _list_themes():
            label = f" ({t['label']})" if t["label"] else ""
            desc = f" - {t['description']}" if t["description"] else ""
            print(f"  {t['name']}{label}{desc}")
        return

    if not args.input:
        parser.print_help()
        sys.exit(0)

    input_path = Path(args.input).resolve()
    if not input_path.exists():
        _err(f"文件不存在: {input_path}")

    md_text = input_path.read_text(encoding="utf-8")

    if not args.no_preformat:
        md_text = _preformat_markdown(md_text)
        _info("Markdown 预格式化完成（中英文间距、引号、空行）")

    theme = _load_theme(args.theme)

    overrides = {}
    if args.color:
        overrides["primary-color"] = args.color
    if args.font_size:
        overrides["font-size"] = args.font_size

    _info(f"主题: {args.theme}")
    styles = _build_styles(theme, overrides)
    body_html = _md_to_html(md_text, styles)

    # 文末 closing.md
    closing_md_path = input_path.parent / "closing.md"
    if closing_md_path.exists():
        closing_md = closing_md_path.read_text(encoding="utf-8")
        closing_html = _md_to_html(closing_md, styles)
        body_html = f'{body_html}\n\n<div style="margin-top:1.5em"></div>\n{closing_html}'
        _info(f"已追加文末区块: {closing_md_path}")

    full_html = _wrap_document(body_html, styles)

    output_path = Path(args.output) if args.output else input_path.with_suffix(".html")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(full_html, encoding="utf-8")
    _ok(f"已保存: {output_path}")

    if args.preview:
        webbrowser.open(f"file://{output_path.absolute()}")
        _info("已在浏览器中打开预览")


if __name__ == "__main__":
    main()
