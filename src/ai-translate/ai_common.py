"""AI 初翻工具（待审核工作流）公共部分：技术串过滤、草稿目录约定、标注前缀。

待审核目录布局（在仓库外的 待审核/ 下，不入 git）：
    待审核/<mod_dir>/
        en_us.json        # 源文件
        zh_cn.json        # AI 初翻草稿（标注了 AI 翻译处）
        REVIEW-NOTES.md   # 逐条标注清单（AI 翻译的地方、术语、占位符核对）
        draft-meta.json   # 元数据（provider、时间、统计）
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import REPO_ROOT, load_json, save_json  # noqa: E402

AI_MARK = "【AI·待审核】"
DEFAULT_PENDING_ROOT = REPO_ROOT.parent / "待审核"

# 技术串：ID、布尔、纯数字、snake_case、命名空间 ID、颜色码等不需要翻译
TECHNICAL_RES = [
    re.compile(r"^[a-z0-9_.\-/:]+$"),                 # snake_case / namespaced id / 路径
    re.compile(r"^(true|false|on|off|yes|no)$", re.I),
    re.compile(r"^[-+]?[0-9.,：%°smhdx ]*$"),          # 纯数字/单位
    re.compile(r"^#[0-9a-fA-F]{3,8}$"),               # 颜色码
    re.compile(r"^[A-Z0-9_]+$"),                      # 常量名
]


def is_technical(value: str) -> bool:
    v = value.strip()
    return (not v) or any(rx.match(v) for rx in TECHNICAL_RES)


def draft_dir(pending_root: Path, mod_dir: str) -> Path:
    return pending_root / mod_dir


def load_glossary_pairs(glossary_dir: Path) -> list[dict]:
    entries = []
    for f in sorted(glossary_dir.glob("*.json")):
        data = load_json(f)
        entries.extend(data if isinstance(data, list) else [data])
    return entries


def mark_value(text: str) -> str:
    return text if text.startswith(AI_MARK) else AI_MARK + text


def strip_mark(text: str) -> str:
    return text[len(AI_MARK):] if text.startswith(AI_MARK) else text
