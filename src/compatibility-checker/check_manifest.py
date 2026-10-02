"""manifest 冻结契约检查。用法: python src/compatibility-checker/check_manifest.py manifest.json [--build-dir build/]"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import load_json  # noqa: E402
from compat_lib import check_manifest, check_asset_names, check_md5  # noqa: E402


def main() -> int:
    if len(sys.argv) < 2:
        print(__doc__, file=sys.stderr)
        return 2
    manifest = load_json(sys.argv[1])
    errors = check_manifest(manifest)
    if "--build-dir" in sys.argv:
        build_dir = Path(sys.argv[sys.argv.index("--build-dir") + 1])
        errors += check_asset_names(build_dir)
        errors += check_md5(manifest, build_dir)
    for e in errors:
        print(f"[FAIL] {e}", file=sys.stderr)
    if not errors:
        print("[PASS] manifest 冻结契约检查通过")
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
