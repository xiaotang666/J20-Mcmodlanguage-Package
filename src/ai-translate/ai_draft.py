"""AI 初步翻译：为未汉化模组生成 zh_cn.json 草稿并放入待审核文件夹。

用法：
    python src/ai-translate/ai_draft.py --mod-dir create --namespace create \
        [--i18n-version-dirs 1.20,1.18] [--en-us path/to/en_us.json] \
        [--provider api|glossary] [--inline-mark] [--batch-size 40]

provider:
    api      调用 OpenAI 兼容接口（环境变量 J20_AI_BASE_URL / J20_AI_API_KEY / J20_AI_MODEL）
    glossary 离线兜底：只套术语库，未匹配的词条以 【待翻译】原文 占位（绝不静默丢词条）

所有 AI 产出的译文都会记录到 REVIEW-NOTES.md（由 mark_draft.py 生成），--inline-mark 时
还会在译文值前加 【AI·待审核】 前缀，人工审核后由 approve.py 去除。
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import sys
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import REPO_ROOT, fetch_with_fallback, load_json, save_json  # noqa: E402
from ai_common import (DEFAULT_PENDING_ROOT, draft_dir, is_technical, load_glossary_pairs,
                       mark_value)  # noqa: E402

SYSTEM_PROMPT = (
    "你是 Minecraft 模组本地化译者，把 en_us.json 的英文值翻译成简体中文。"
    "规则：1) 保留所有占位符（%s %d {0} <item:...> 等）、§格式码、\\\\n 换行符原样不动；"
    "2) 使用给定术语表；3) UI 短文本简洁，按钮用「动词+宾语」；"
    "4) 只输出 JSON 对象 {key: 中文译文}，不要输出任何解释。"
)


def api_translate(pairs: list[tuple[str, str]], glossary: list[dict], batch_size: int) -> dict[str, str]:
    base = os.environ.get("J20_AI_BASE_URL", "").rstrip("/")
    key = os.environ.get("J20_AI_API_KEY", "")
    model = os.environ.get("J20_AI_MODEL", "")
    if not (base and key and model):
        raise SystemExit("[FATAL] api provider 需要环境变量 J20_AI_BASE_URL / J20_AI_API_KEY / J20_AI_MODEL")

    hints = "; ".join(f"{e['term']}={e['translation']}" for e in glossary[:80] if e.get("term"))
    out: dict[str, str] = {}
    for i in range(0, len(pairs), batch_size):
        batch = pairs[i:i + batch_size]
        payload = {"model": model, "temperature": 0.2,
                   "messages": [{"role": "system", "content": SYSTEM_PROMPT + f"\n术语表：{hints}"},
                                {"role": "user", "content": json.dumps(dict(batch), ensure_ascii=False)}]}
        req = urllib.request.Request(
            f"{base}/chat/completions", data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {key}"})
        with urllib.request.urlopen(req, timeout=300) as resp:
            content = json.loads(resp.read().decode("utf-8"))["choices"][0]["message"]["content"]
        # 容错：剥掉可能的 ```json 围栏
        content = content.strip().removeprefix("```json").removesuffix("```").strip()
        out.update(json.loads(content))
        print(f"[API] 已翻译 {min(i + batch_size, len(pairs))}/{len(pairs)}")
    return out


def glossary_translate(pairs: list[tuple[str, str]], glossary: list[dict]) -> dict[str, str]:
    out = {}
    for key, en in pairs:
        zh = en
        for entry in glossary:
            t, tr = entry.get("term", ""), entry.get("translation", "")
            if t and tr and t.lower() in en.lower():
                zh = zh.replace(t, tr)
        out[key] = f"【待翻译】{zh}" if zh == en else f"【术语机翻·待审核】{zh}"
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description="AI 初步翻译生成待审核草稿")
    ap.add_argument("--mod-dir", required=True, help="i18n 模组目录名，如 applied-energistics-2")
    ap.add_argument("--namespace", required=True, help="资源命名空间，如 appliedenergistics2")
    ap.add_argument("--i18n-version-dirs", default="1.20,1.18,1.16")
    ap.add_argument("--en-us", default=None, help="本地 en_us.json（缺省从 i18n 拉取）")
    ap.add_argument("--config", default=str(REPO_ROOT / "config" / "merger" / "i18n-source.json"))
    ap.add_argument("--provider", choices=["api", "glossary"], default="api")
    ap.add_argument("--inline-mark", action="store_true", help="译文加 【AI·待审核】 前缀")
    ap.add_argument("--batch-size", type=int, default=40)
    ap.add_argument("--pending-root", default=str(DEFAULT_PENDING_ROOT))
    args = ap.parse_args()

    # 1) 取源文件
    if args.en_us:
        raw = Path(args.en_us).read_bytes()
    else:
        config = load_json(args.config)
        mod = {"mod_dir": args.mod_dir, "namespace": args.namespace, "formats": ["json"]}
        raw = None
        for vdir in args.i18n_version_dirs.split(","):
            rel = config["file_path_pattern"].format(
                mod_dir=args.mod_dir, i18n_version_dir=vdir.strip(),
                namespace=args.namespace, file="en_us.json")
            raw, _, _ = fetch_with_fallback(rel, config)
            if raw is not None:
                break
        if raw is None:
            raise SystemExit(f"[FATAL] 无法获取 {args.mod_dir} 的 en_us.json")
    en_data = json.loads(raw.decode("utf-8"))

    # 2) 过滤技术串
    translatable = [(k, v) for k, v in en_data.items() if isinstance(v, str) and not is_technical(v)]
    skipped = [k for k in en_data if k not in dict(translatable)]
    print(f"[INFO] 条目 {len(en_data)}，可翻译 {len(translatable)}，技术串跳过 {len(skipped)}")

    # 3) 翻译
    glossary = load_glossary_pairs(REPO_ROOT / "glossary")
    if args.provider == "api":
        translated = api_translate(translatable, glossary, args.batch_size)
    else:
        translated = glossary_translate(translatable, glossary)

    # 4) 组装草稿
    draft = {}
    for k, v in en_data.items():
        if k in translated:
            draft[k] = mark_value(translated[k]) if args.inline_mark else translated[k]
        else:
            draft[k] = v  # 技术串原样保留

    out_dir = draft_dir(Path(args.pending_root), args.mod_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "en_us.json").write_bytes(raw)
    save_json(out_dir / "zh_cn.json", draft, indent=4)
    save_json(out_dir / "draft-meta.json", {
        "mod_dir": args.mod_dir, "namespace": args.namespace,
        "provider": args.provider, "inline_mark": args.inline_mark,
        "created_at": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "total_keys": len(en_data), "translated_keys": len(translated),
        "skipped_technical_keys": len(skipped),
    })
    print(f"[OK] 草稿已生成：{out_dir / 'zh_cn.json'}")
    print("下一步：python src/ai-translate/mark_draft.py --mod-dir", args.mod_dir, "生成标注清单")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
