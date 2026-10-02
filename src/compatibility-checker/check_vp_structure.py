"""VP 模块结构检查。用法: python src/compatibility-checker/check_vp_structure.py vaultpatcher/ [build/]"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from compat_lib import check_vp_modules, check_vp_zip_structure  # noqa: E402


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__, file=sys.stderr)
        return 2
    errors = check_vp_modules(Path(sys.argv[1]))
    if len(sys.argv) > 2:
        for z in sorted(Path(sys.argv[2]).glob("vp-modules-*.zip")):
            errors += check_vp_zip_structure(z)
    for e in errors:
        print(f"[FAIL] {e}", file=sys.stderr)
    if not errors:
        print("[PASS] VP 模块结构检查通过")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
