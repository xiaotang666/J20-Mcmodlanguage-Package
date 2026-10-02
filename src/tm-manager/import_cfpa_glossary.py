"""从 CFPAOrg/Glossary 导入术语库，生成 glossary/vanilla.json 与 glossary/mods.json。

用法：
    python src/tm-manager/import_cfpa_glossary.py <glossary-src 目录>

输入文件（CFPAOrg/Glossary 仓库）：
    Archives/Minecraft Standard Terms form Wiki 1.18.2.csv  -> glossary/vanilla.json
    Mod/模组简体中文翻译指南.tsv                             -> glossary/mods.json
    Mod/模组材料简体中文翻译指南.tsv                         -> glossary/mods.json

输出条目格式（文档 4.4.1.2）：
    {"term", "translation", "context", "source", "modid", "priority", "notes"}
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import REPO_ROOT, save_json  # noqa: E402


def load_vanilla(src: Path) -> list[dict]:
    entries = []
    with open(src, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        header = next(reader, None)
        for row in reader:
            if len(row) < 4:
                continue
            category, term, translation = row[0].strip(), row[1].strip(), row[3].strip()
            remark = row[6].strip() if len(row) > 6 else ""
            example = row[9].strip() if len(row) > 9 else ""
            if not term or not translation or term == translation:
                continue
            entries.append({
                "term": term,
                "translation": translation,
                "context": f"{category}；{example}" if example else category,
                "source": "vanilla",
                "modid": None,
                "priority": "high",
                "notes": remark or None,
            })
    return entries


def load_mod_tsv(src: Path, source_tag: str) -> list[dict]:
    entries = []
    with open(src, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f, delimiter="\t")
        header = next(reader, None)
        for row in reader:
            if len(row) < 2:
                continue
            term, translation = row[0].strip(), row[1].strip()
            remark = row[2].strip() if len(row) > 2 else ""
            origin = row[3].strip() if len(row) > 3 else ""
            if not term or not translation:
                continue
            entries.append({
                "term": term,
                "translation": translation,
                "context": origin or None,
                "source": source_tag,
                "modid": None,
                "priority": "medium",
                "notes": remark or None,
            })
    return entries


def main() -> int:
    if len(sys.argv) != 2:
        print(__doc__, file=sys.stderr)
        return 2
    src = Path(sys.argv[1])
    glossary_dir = REPO_ROOT / "glossary"
    glossary_dir.mkdir(exist_ok=True)

    vanilla_path = src / "Archives" / "Minecraft Standard Terms form Wiki 1.18.2.csv"
    if vanilla_path.exists():
        vanilla = load_vanilla(vanilla_path)
        save_json(glossary_dir / "vanilla.json", vanilla)
        print(f"vanilla.json: {len(vanilla)} 条")

    mods = []
    for name, tag in (("模组简体中文翻译指南.tsv", "CFPAOrg-Glossary-Mod"),
                      ("模组材料简体中文翻译指南.tsv", "CFPAOrg-Glossary-Mod-Materials")):
        p = src / "Mod" / name
        if p.exists():
            batch = load_mod_tsv(p, tag)
            mods.extend(batch)
            print(f"{name}: {len(batch)} 条")
    if mods:
        save_json(glossary_dir / "mods.json", mods)
        print(f"mods.json: {len(mods)} 条")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
