"""j20-i18n-linter：翻译质量自动校验（文档 4.4.3）。

用法：
    python src/linter/run.py projects/ [--json build/lint-report.json] [--tmx tm/]

检测项（错误=阻断构建，警告=记录并放行）：
    [错误] JSON 格式错误（非 UTF-8 无 BOM / 非法 JSON）
    [错误] 文件内重复键
    [错误] 占位符不一致（%s %d %1$s {0} {player} <item:...> 等缺失或数量不符）
    [错误] 格式码丢失（§a &l 等颜色/格式代码在译文中丢失）
    [警告] 术语违规（未使用 glossary 标准译法）
    [警告] 长度超限（短 UI 文本超出原文 ±15%，溢出/截断风险）
    [警告] 敏感词触发（低质网络用语）
    [警告] TM 一致性（相同原文在不同文件中译文不一致）
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import REPO_ROOT, save_json  # noqa: E402

# ---------- 正则 ----------

PLACEHOLDER_RES = [
    re.compile(r"%(?:\d+\$)?[sdfg]"),           # %s %d %2$s
    re.compile(r"%\{[^}]*\}"),                  # %{...}
    re.compile(r"\{[a-zA-Z0-9_.]+\}"),          # {0} {player} {item.id}
    re.compile(r"\{\{[^}]*\}\}"),               # {{...}}
    re.compile(r"<[a-zA-Z][a-zA-Z0-9_:./-]*>"), # <item:...> <br>
    re.compile(r"%[a-zA-Z][a-zA-Z0-9_]*%"),     # %msg%
]
FORMAT_CODE_RE = re.compile(r"(?:§|&)[0-9a-fk-orA-FK-OR]")
SENSITIVE_WORDS = ["脑残", "煞笔", "傻逼", "尼玛", "妈的", "垃圾玩意", "滚粗", "nmsl"]
TECHNICAL_VALUE_RE = re.compile(r"^[\w\-.:/ ]*$")  # 纯技术串：ID/布尔/数字/snake_case

# 短 UI 文本才做长度检查（长文本按 ±15% 卡会误伤正常中文表达）
UI_LENGTH_MAX_SRC = 40
LENGTH_TOLERANCE = 0.15


def extract_tokens(text: str, regexes) -> Counter:
    tokens: Counter = Counter()
    for rx in regexes:
        tokens.update(rx.findall(text))
    return tokens


def format_codes(text: str) -> Counter:
    return Counter(FORMAT_CODE_RE.findall(text))


def load_glossary(glossary_dir: Path) -> list[dict]:
    entries = []
    for f in sorted(glossary_dir.glob("*.json")):
        try:
            data = json.loads(f.read_text(encoding="utf-8"))
            entries.extend(data if isinstance(data, list) else [data])
        except ValueError as e:
            print(f"[WARN] 术语库解析失败 {f.name}: {e}", file=sys.stderr)
    return entries


def load_lang_pairs(path: Path) -> tuple[dict, list[str]]:
    """读取语言 JSON，返回 (数据, 错误列表)。带 object_pairs_hook 检测重复键。"""
    errors = []
    raw = path.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        errors.append("文件带 UTF-8 BOM")
        raw = raw[3:]
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as e:
        return {}, [f"非 UTF-8 编码：{e}"]
    dup_keys: list[str] = []

    def hook(pairs):
        seen = set()
        for k, _ in pairs:
            if k in seen:
                dup_keys.append(k)
            seen.add(k)
        return dict(pairs)

    try:
        data = json.loads(text, object_pairs_hook=hook)
    except ValueError as e:
        return {}, [f"JSON 非法：{e}"]
    errors.extend(f"重复键：{k}" for k in dup_keys)
    return data, errors


def check_file(zh_path: Path, en_data: dict | None, glossary: list[dict]) -> tuple[list[dict], dict]:
    """检查单个 zh_cn 文件，返回 (问题列表, {key: zh_text} 供 TM 一致性检查)。"""
    issues = []
    data, errors = load_lang_pairs(zh_path)
    for e in errors:
        issues.append({"file": str(zh_path), "key": "-", "severity": "error",
                       "type": "json", "message": e})

    for key, zh in data.items():
        if not isinstance(zh, str):
            continue
        en = (en_data or {}).get(key, "")

        # 占位符一致性
        if en:
            want = extract_tokens(en, PLACEHOLDER_RES)
            got = extract_tokens(zh, PLACEHOLDER_RES)
            for tok, n in want.items():
                if got.get(tok, 0) != n:
                    issues.append({"file": str(zh_path), "key": key, "severity": "error",
                                   "type": "placeholder",
                                   "message": f"占位符 {tok} 应出现 {n} 次，译文中 {got.get(tok, 0)} 次"})
            # 格式码保留
            fc_en, fc_zh = format_codes(en), format_codes(zh)
            for code, n in fc_en.items():
                if fc_zh.get(code, 0) != n:
                    issues.append({"file": str(zh_path), "key": key, "severity": "error",
                                   "type": "format_code",
                                   "message": f"格式码 {code} 应出现 {n} 次，译文中 {fc_zh.get(code, 0)} 次"})

            # 长度（仅短 UI 文本）
            if len(en) <= UI_LENGTH_MAX_SRC and not TECHNICAL_VALUE_RE.match(en):
                if len(zh) > len(en) * (1 + LENGTH_TOLERANCE):
                    issues.append({"file": str(zh_path), "key": key, "severity": "warning",
                                   "type": "length",
                                   "message": f"长度超限：原文 {len(en)} 字符，译文 {len(zh)} 字符（>{int(LENGTH_TOLERANCE*100)}%）"})
                elif len(en) >= 4 and len(zh) < len(en) * 0.5:
                    issues.append({"file": str(zh_path), "key": key, "severity": "warning",
                                   "type": "length",
                                   "message": f"译文过短：原文 {len(en)} 字符，译文 {len(zh)} 字符，注意是否截断"})

            # 术语违规
            for term in glossary:
                t = term.get("term", "")
                trans = term.get("translation", "")
                if not t or not trans:
                    continue
                if re.search(rf"\b{re.escape(t)}\b", en, re.IGNORECASE) and trans not in zh:
                    issues.append({"file": str(zh_path), "key": key, "severity": "warning",
                                   "type": "glossary",
                                   "message": f"术语「{t}」应译为「{trans}」（来源 {term.get('source', '?')}）"})

        # 敏感词
        for w in SENSITIVE_WORDS:
            if w in zh:
                issues.append({"file": str(zh_path), "key": key, "severity": "warning",
                               "type": "sensitive",
                               "message": f"触发敏感词「{w}」，请人工确认"})

    return issues, data


def check_tmx_consistency(all_texts: list[tuple[str, dict]]) -> list[dict]:
    """TM 一致性：相同原文（en）在不同文件里译文不一致 → 警告。"""
    issues = []
    en_index: dict[str, dict[str, list[str]]] = defaultdict(lambda: defaultdict(list))
    for label, (en_data, zh_data) in all_texts:
        for k, zh in zh_data.items():
            if isinstance(zh, str) and isinstance(en_data.get(k), str):
                en_index[en_data[k]][zh].append(f"{label}:{k}")
    for en, variants in en_index.items():
        if len(variants) > 1 and len(en) > 2:
            detail = "; ".join(f"「{zh}」×{len(locs)}" for zh, locs in variants.items())
            issues.append({"file": "(跨文件)", "key": en[:40], "severity": "warning",
                           "type": "tm_consistency",
                           "message": f"相同原文出现多种译法：{detail}"})
    return issues


def main() -> int:
    ap = argparse.ArgumentParser(description="翻译质量 Linter")
    ap.add_argument("target", help="检查目录（如 projects/）或单个文件")
    ap.add_argument("--glossary", default=str(REPO_ROOT / "glossary"))
    ap.add_argument("--json", dest="json_out", default=None, help="报告 JSON 输出路径")
    args = ap.parse_args()

    target = Path(args.target)
    files = sorted(target.rglob("zh_cn.*")) if target.is_dir() else [target]
    if not files:
        print(f"[WARN] 未找到任何 zh_cn.* 文件：{target}", file=sys.stderr)
    glossary = load_glossary(Path(args.glossary))
    print(f"[INFO] 已加载术语 {len(glossary)} 条，检查文件 {len(files)} 个")

    all_issues: list[dict] = []
    all_texts: list[tuple[str, tuple[dict, dict]]] = []
    for zh_path in files:
        en_path = zh_path.with_name("en_us" + zh_path.suffix)
        en_data = {}
        if en_path.exists():
            en_data, _ = load_lang_pairs(en_path)
        issues, zh_data = check_file(zh_path, en_data, glossary)
        all_issues.extend(issues)
        if en_data:
            all_texts.append((str(zh_path), (en_data, zh_data)))
    all_issues.extend(check_tmx_consistency(all_texts))

    n_err = sum(1 for i in all_issues if i["severity"] == "error")
    n_warn = len(all_issues) - n_err
    for i in all_issues:
        tag = "ERROR" if i["severity"] == "error" else "WARN "
        print(f"[{tag}] {i['file']} :: {i['key']} :: [{i['type']}] {i['message']}")

    report = {"files_checked": len(files), "glossary_entries": len(glossary),
              "errors": n_err, "warnings": n_warn, "issues": all_issues}
    if args.json_out:
        save_json(args.json_out, report)
    print(f"\nLinter 完成：错误 {n_err}，警告 {n_warn}")
    return 1 if n_err else 0


if __name__ == "__main__":
    raise SystemExit(main())
