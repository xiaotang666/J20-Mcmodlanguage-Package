"""运行全部兼容性/合规检查，输出 compatibility-report.json。

用法: python src/compatibility-checker/run_all.py [build/]
不通过（任何 FAIL）时退出码为 1，可直接阻断 CI 发布。
"""
from __future__ import annotations

import datetime as dt
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import REPO_ROOT, save_json  # noqa: E402

CHECKS = [
    ("manifest_contract", [sys.executable, "src/compatibility-checker/check_manifest.py", "manifest.json"]),
    ("pack_format", [sys.executable, "src/compatibility-checker/check_pack_format.py", "projects/"]),
    ("vp_structure", [sys.executable, "src/compatibility-checker/check_vp_structure.py", "vaultpatcher/"]),
    ("license_repo", [sys.executable, "src/merger/check_license.py", "--repo"]),
]


def main() -> int:
    build_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else REPO_ROOT / "build"
    checks = list(CHECKS)
    if build_dir.is_dir():
        checks.append(("assets", [sys.executable, "src/compatibility-checker/check_assets.py", str(build_dir)]))
        checks.append(("license_packs", [sys.executable, "src/merger/check_license.py"]
                       + [str(z) for z in sorted(build_dir.glob("pack-*.zip"))]))
        checks.append(("verify_packs", [sys.executable, "src/merger/verify.py"]
                       + [str(z) for z in sorted(build_dir.glob("pack-*.zip"))]))

    results = []
    all_ok = True
    for name, cmd in checks:
        r = subprocess.run(cmd, cwd=str(REPO_ROOT), capture_output=True, text=True)
        ok = r.returncode == 0
        all_ok = all_ok and ok
        results.append({"check": name, "passed": ok,
                        "output": (r.stdout + r.stderr).strip()[-2000:]})
        print(f"[{'PASS' if ok else 'FAIL'}] {name}")

    report = {
        "generated_at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "passed": all_ok,
        "checks": results,
    }
    save_json(REPO_ROOT / "compatibility-report.json", report)
    print(f"\n兼容性报告：compatibility-report.json（{'全部通过' if all_ok else '存在失败项'}）")
    return 0 if all_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
