"""pack_format 映射检查。用法: python src/compatibility-checker/check_pack_format.py projects/ [config/packer/pack-config.json]"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import REPO_ROOT, load_json  # noqa: E402
from compat_lib import check_pack_format  # noqa: E402


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__, file=sys.stderr)
        return 2
    projects_dir = Path(sys.argv[1])
    cfg_path = Path(sys.argv[2]) if len(sys.argv) > 2 else REPO_ROOT / "config" / "packer" / "pack-config.json"
    errors = check_pack_format(projects_dir, load_json(cfg_path))
    for e in errors:
        print(f"[FAIL] {e}", file=sys.stderr)
    if not errors:
        print("[PASS] pack_format 映射检查通过")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
