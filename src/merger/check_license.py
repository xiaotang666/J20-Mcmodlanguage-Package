"""协议合规检查器（CC BY-NC-SA 4.0）。

用法：
    python src/merger/check_license.py build/pack-1.20.1-forge.zip [more.zip ...]
    python src/merger/check_license.py --repo   # 检查仓库根的合规文件

检查项（对应文档附录 F）：
- 资源包内 LICENSE-i18n / LICENSE-j20 / ATTRIBUTION.md 存在
- pack.mcmeta description 含 i18n 来源署名与协议标注
- ATTRIBUTION.md 含 i18n 来源、协议、修改说明、禁止商业用途声明
- 未暗示 CFPAOrg 背书（检查违禁表述）
"""
from __future__ import annotations

import json
import sys
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import REPO_ROOT  # noqa: E402

REQUIRED_IN_PACK = ("LICENSE-i18n", "LICENSE-j20", "ATTRIBUTION.md")
REQUIRED_IN_REPO = ("LICENSE", "LICENSE-i18n", "ATTRIBUTION.md", "README.md")
ATTRIBUTION_MUST_CONTAIN = ("CFPAOrg", "CC BY-NC-SA 4.0", "禁止商业", "修改")
FORBIDDEN_CLAIMS = ("CFPAOrg 官方", "官方认证", "CFPAOrg endorsed", "officially endorsed")


def check_text(label: str, text: str, errors: list[str]) -> None:
    for needle in ATTRIBUTION_MUST_CONTAIN:
        if needle not in text:
            errors.append(f"{label} 缺少必备内容：「{needle}」")
    for bad in FORBIDDEN_CLAIMS:
        if bad in text:
            errors.append(f"{label} 含暗示背书的违禁表述：「{bad}」")


def check_zip(path: Path, errors: list[str]) -> None:
    with zipfile.ZipFile(path) as zf:
        names = zf.namelist()
        for req in REQUIRED_IN_PACK:
            if req not in names:
                errors.append(f"{path.name}: 包内缺少 {req}")
        if "ATTRIBUTION.md" in names:
            check_text(f"{path.name}/ATTRIBUTION.md",
                       zf.read("ATTRIBUTION.md").decode("utf-8", "replace"), errors)
        if "pack.mcmeta" in names:
            desc = json.dumps(json.loads(zf.read("pack.mcmeta").decode("utf-8"))
                              .get("pack", {}).get("description", ""), ensure_ascii=False)
            if "i18n" not in desc or "CC BY-NC-SA 4.0" not in desc:
                errors.append(f"{path.name}: pack.mcmeta 署名不完整（需含 i18n 来源与协议）")


def main() -> int:
    errors: list[str] = []
    if "--repo" in sys.argv:
        for req in REQUIRED_IN_REPO:
            if not (REPO_ROOT / req).exists():
                errors.append(f"仓库根缺少 {req}")
        if (REPO_ROOT / "ATTRIBUTION.md").exists():
            check_text("ATTRIBUTION.md", (REPO_ROOT / "ATTRIBUTION.md").read_text(encoding="utf-8"), errors)
    else:
        zips = [Path(a) for a in sys.argv[1:] if not a.startswith("--")]
        if not zips:
            print("用法: python src/merger/check_license.py <zip> [zip ...] | --repo", file=sys.stderr)
            return 2
        for z in zips:
            if z.exists():
                check_zip(z, errors)
            else:
                errors.append(f"{z} 不存在")

    if errors:
        for e in errors:
            print(f"[FAIL] {e}", file=sys.stderr)
        return 1
    print("[PASS] 协议合规检查通过")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
