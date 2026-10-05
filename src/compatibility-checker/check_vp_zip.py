"""VP 模块包 zip 结构校验（命令行入口）。

用法：
    python src/compatibility-checker/check_vp_zip.py build/vp-modules-*.zip

规则（冻结）：zip 内只能是 vaultpatcher/modules/*.json（仅一层、无子目录），
禁止绝对路径与路径穿越字符（..、反斜杠、盘符）。
"""
from __future__ import annotations

import sys
from pathlib import Path

from compat_lib import check_vp_zip_structure


def main() -> int:
    paths = [Path(p) for p in sys.argv[1:]]
    if not paths:
        print("用法: python src/compatibility-checker/check_vp_zip.py <vp-modules-*.zip>...", file=sys.stderr)
        return 2
    errors: list[str] = []
    for p in paths:
        if not p.exists():
            errors.append(f"{p}: 文件不存在")
            continue
        errors.extend(check_vp_zip_structure(p))
    for e in errors:
        print(f"[FAIL] {e}")
    if errors:
        return 1
    print(f"[PASS] {len(paths)} 个 VP 包结构合规")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
