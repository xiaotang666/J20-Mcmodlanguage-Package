"""标注 AI 初翻草稿：生成 REVIEW-NOTES.md，逐条标注 AI 翻译的地方供人工审核。

用法：
    python src/ai-translate/mark_draft.py --mod-dir create [--pending-root ../待审核]

REVIEW-NOTES.md 内容：
- 统计（总条目 / AI 翻译 / 术语机翻 / 未翻译占位 / 技术串跳过）
- 逐条标注表：键、原文、AI 译文、标记（占位符核对结果、术语命中、长度提示）
- 审核指引（改完译文后跑 approve.py 入库）
"""
from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import load_json  # noqa: E402
from ai_common import AI_MARK, DEFAULT_PENDING_ROOT, draft_dir  # noqa: E402

PLACEHOLDER_RX = re.compile(r"%(?:\d+\$)?[sdfg]|\{[a-zA-Z0-9_.]+\}|\{\{[^}]*\}\}|<[a-zA-Z][\w:./-]*>|%[a-zA-Z]\w*%|(?:§|&)[0-9a-fk-orA-FK-OR]")


def placeholders(text: str) -> list[str]:
    return PLACEHOLDER_RX.findall(text)


def main() -> int:
    ap = argparse.ArgumentParser(description="生成 AI 草稿标注清单")
    ap.add_argument("--mod-dir", required=True)
    ap.add_argument("--pending-root", default=str(DEFAULT_PENDING_ROOT))
    args = ap.parse_args()

    d = draft_dir(Path(args.pending_root), args.mod_dir)
    en = load_json(d / "en_us.json")
    zh = load_json(d / "zh_cn.json")
    meta = load_json(d / "draft-meta.json") if (d / "draft-meta.json").exists() else {}

    rows, stats = [], {"ai": 0, "ai_marked": 0, "term_draft": 0, "todo": 0, "unchanged": 0, "placeholder_warn": 0}
    for key, en_v in en.items():
        zh_v = zh.get(key, "")
        if not isinstance(en_v, str) or not isinstance(zh_v, str):
            continue
        flags = []
        if zh_v.startswith(AI_MARK):
            stats["ai_marked"] += 1
            flags.append("AI·已内联标注")
            zh_v_body = zh_v[len(AI_MARK):]
        else:
            zh_v_body = zh_v
        if zh_v_body.startswith("【待翻译】"):
            stats["todo"] += 1
            flags.append("⚠未翻译占位")
        elif zh_v_body.startswith("【术语机翻·待审核】"):
            stats["term_draft"] += 1
            flags.append("术语机翻")
        elif zh_v_body != en_v:
            stats["ai"] += 1
            flags.append("AI 翻译")
        else:
            stats["unchanged"] += 1
            flags.append("技术串/未改动")

        if zh_v_body != en_v:
            want, got = placeholders(en_v), placeholders(zh_v_body)
            if sorted(want) != sorted(got):
                stats["placeholder_warn"] += 1
                flags.append(f"⚠占位符不一致(原:{want} 译:{got})")
        rows.append((key, en_v, zh_v_body, "；".join(flags)))

    lines = [
        f"# AI 初翻审核清单 — {args.mod_dir}",
        "",
        f"- 生成时间：{dt.datetime.now(dt.timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        f"- Provider：{meta.get('provider', '?')}    内联标注：{meta.get('inline_mark', False)}",
        f"- 总条目：{len(en)}    AI 翻译：{stats['ai']}（内联标注 {stats['ai_marked']}）    "
        f"术语机翻：{stats['term_draft']}    未翻译占位：{stats['todo']}    技术串：{stats['unchanged']}",
        f"- 占位符警告：{stats['placeholder_warn']} 条（必须逐条人工核对）",
        "",
        "## 审核指引",
        "1. 逐条核对下表译文，重点处理 ⚠ 标记的条目；",
        "2. 直接修改 `zh_cn.json`（如带 【AI·待审核】 前缀，审核时保留前缀，approve.py 入库时自动去除）；",
        "3. 术语按 `glossary/` 三级术语库校正；",
        "4. 审核完成后运行：`python src/ai-translate/approve.py --mod-dir "
        f"{args.mod_dir} --mc-version <版本>` 入库（自动跑 Linter，有错误则拒绝入库）。",
        "",
        "## 逐条标注",
        "",
        "| 键 | 原文 | 译文 | 标注 |",
        "| --- | --- | --- | --- |",
    ]
    for key, en_v, zh_v, flags in rows:
        esc = lambda s: s.replace("|", "\\|").replace("\n", "<br>")
        lines.append(f"| `{esc(key)}` | {esc(en_v)} | {esc(zh_v)} | {esc(flags)} |")

    (d / "REVIEW-NOTES.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"[OK] 标注清单：{d / 'REVIEW-NOTES.md'}")
    print(f"     AI 翻译 {stats['ai']} + 内联标注 {stats['ai_marked']}，"
          f"术语机翻 {stats['term_draft']}，未翻译 {stats['todo']}，占位符警告 {stats['placeholder_warn']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
