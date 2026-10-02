"""构建资产检查：命名规范 + 与 manifest 的 MD5/size 一致性。用法: python src/compatibility-checker/check_assets.py build/ [manifest.json]"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import REPO_ROOT, load_json  # noqa: E402
from compat_lib import check_asset_names, check_md5, check_pack_zip_structure, check_vp_zip_structure  # noqa: E402


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__, file=sys.stderr)
        return 2
    build_dir = Path(sys.argv[1])
    errors = check_asset_names(build_dir)
    for z in sorted(build_dir.glob("pack-*.zip")):
        errors += check_pack_zip_structure(z)
    for z in sorted(build_dir.glob("vp-modules-*.zip")):
        errors += check_vp_zip_structure(z)
    manifest_path = Path(sys.argv[2]) if len(sys.argv) > 2 else REPO_ROOT / "manifest.json"
    if manifest_path.exists():
        errors += check_md5(load_json(manifest_path), build_dir)
    for e in errors:
        print(f"[FAIL] {e}", file=sys.stderr)
    if not errors:
        print("[PASS] 构建资产检查通过")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
