"""Aaalice 词典导出 → TMX 转换器（文档 4.4.2.8）。

用法: python src/tm-manager/dict_to_tmx.py <aaalice_export.json> <output.tmx>
输入为 {"English": "中文", ...} 的 JSON 对象；输出标准 TMX 1.4，可放入 OmegaT tm/auto/。
"""
from __future__ import annotations

import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


def dict_to_tmx(dict_file: Path, tmx_file: Path, source_lang: str = "en", target_lang: str = "zh-CN") -> int:
    entries = json.loads(dict_file.read_text(encoding="utf-8"))
    tmx = ET.Element("tmx", version="1.4")
    ET.SubElement(tmx, "header", creationtool="J20-Dict-Converter",
                  creationtoolversion="0.0.1", srclang=source_lang,
                  adminlang=source_lang, segtype="sentence")
    body = ET.SubElement(tmx, "body")
    for key, value in entries.items():
        tu = ET.SubElement(body, "tu", tuid=key)
        seg_src = ET.SubElement(ET.SubElement(tu, "tuv", **{"xml:lang": source_lang}), "seg")
        seg_src.text = key
        seg_tgt = ET.SubElement(ET.SubElement(tu, "tuv", **{"xml:lang": target_lang}), "seg")
        seg_tgt.text = value
    tree = ET.ElementTree(tmx)
    ET.indent(tree, space="  ")
    tree.write(tmx_file, encoding="utf-8", xml_declaration=True)
    return len(entries)


def main() -> int:
    if len(sys.argv) != 3:
        print(__doc__, file=sys.stderr)
        return 2
    n = dict_to_tmx(Path(sys.argv[1]), Path(sys.argv[2]))
    print(f"已转换 {n} 条 -> {sys.argv[2]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
