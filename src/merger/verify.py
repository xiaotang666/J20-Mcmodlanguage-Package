"""最终资源包校验器。

用法：
    python src/merger/verify.py build/pack-1.20-forge.zip [more.zip ...]

检查项：
- pack.mcmeta 存在、合法 JSON、格式声明合法（pack_format 整数，或 min_format/max_format
  新方案——整数或 [major, minor] 元组）、description 含 i18n 署名
- assets/<namespace>/lang/zh_cn.* 至少存在一份
- LICENSE-i18n / LICENSE-j20 / ATTRIBUTION.md 均在包内
- vaultpatcher/modules/ 若存在则结构正确（.json 直接位于该目录下）
"""
from __future__ import annotations

import json
import sys
import zipfile
from pathlib import Path

REQUIRED = ("pack.png", "LICENSE-i18n", "LICENSE-j20", "ATTRIBUTION.md")


def _fmt_value_ok(v) -> bool:
    """格式版本值：整数，或 [major, minor] 元组。"""
    if isinstance(v, int) and not isinstance(v, bool):
        return True
    return (isinstance(v, list) and len(v) == 2
            and all(isinstance(x, int) and not isinstance(x, bool) for x in v))


def verify_zip(path: Path) -> list[str]:
    errors = []
    with zipfile.ZipFile(path) as zf:
        names = zf.namelist()
        if "pack.mcmeta" not in names:
            errors.append("缺少 pack.mcmeta")
        else:
            try:
                meta = json.loads(zf.read("pack.mcmeta").decode("utf-8"))
                pack = meta.get("pack", {})
                legacy = isinstance(pack.get("pack_format"), int) and not isinstance(pack.get("pack_format"), bool)
                modern = _fmt_value_ok(pack.get("min_format")) and _fmt_value_ok(pack.get("max_format"))
                if not (legacy or modern):
                    errors.append("pack.mcmeta 格式声明非法（需整数 pack_format，或 min_format+max_format）")
                desc = json.dumps(pack.get("description", ""), ensure_ascii=False)
                if "i18n" not in desc:
                    errors.append("pack.mcmeta description 缺少 i18n 署名")
            except (ValueError, UnicodeDecodeError) as e:
                errors.append(f"pack.mcmeta 解析失败：{e}")

        lang = [n for n in names if n.startswith("assets/") and "/lang/zh_cn." in n]
        if not lang:
            errors.append("没有任何 assets/*/lang/zh_cn.* 语言文件")

        for req in REQUIRED:
            if req not in names:
                errors.append(f"缺少 {req}")

        vp = [n for n in names if n.startswith("vaultpatcher/")]
        bad_vp = [n for n in vp if not (n.startswith("vaultpatcher/modules/") and n.endswith(".json"))]
        if bad_vp:
            errors.append(f"vaultpatcher/ 下存在非法路径：{bad_vp}")
    return errors


def main() -> int:
    if len(sys.argv) < 2:
        print("用法: python src/merger/verify.py <zip> [zip ...]", file=sys.stderr)
        return 2
    failed = False
    for arg in sys.argv[1:]:
        path = Path(arg)
        if not path.exists():
            print(f"[FAIL] {path} 不存在", file=sys.stderr)
            failed = True
            continue
        errors = verify_zip(path)
        if errors:
            failed = True
            print(f"[FAIL] {path.name}")
            for e in errors:
                print(f"       - {e}", file=sys.stderr)
        else:
            print(f"[PASS] {path.name}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
