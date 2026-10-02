"""人工审核通过后，把待审核草稿正式入库到 projects/。

用法：
    python src/ai-translate/approve.py --mod-dir create --namespace create --mc-version 1.20.1 \
        [--pending-root ../待审核] [--skip-lint]

流程：
1. 草稿 zh_cn.json 必须存在 REVIEW-NOTES.md（未标注不给入库）；
2. 去除 【AI·待审核】 / 【待翻译】 / 【术语机翻·待审核】 前缀——存在【待翻译】占位则直接拒绝；
3. 跑 Linter（src/linter/run.py），有错误拒绝入库，警告放行并打印；
4. 写入 projects/<mc_version>/assets/<namespace>/lang/zh_cn.json（en_us.json 一并入库）；
5. 草稿目录归档到 待审核/_approved/<mod_dir>-<日期>/。
"""
from __future__ import annotations

import argparse
import datetime as dt
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from common import REPO_ROOT, load_json, save_json  # noqa: E402
from ai_common import AI_MARK, DEFAULT_PENDING_ROOT, draft_dir  # noqa: E402

STRIP_PREFIXES = (AI_MARK, "【待翻译】", "【术语机翻·待审核】")


def strip_prefixes(v: str) -> tuple[str, str | None]:
    for p in STRIP_PREFIXES:
        if v.startswith(p):
            return v[len(p):], p
    return v, None


def main() -> int:
    ap = argparse.ArgumentParser(description="审核通过的草稿入库")
    ap.add_argument("--mod-dir", required=True)
    ap.add_argument("--namespace", required=True)
    ap.add_argument("--mc-version", required=True)
    ap.add_argument("--pending-root", default=str(DEFAULT_PENDING_ROOT))
    ap.add_argument("--skip-lint", action="store_true")
    args = ap.parse_args()

    d = draft_dir(Path(args.pending_root), args.mod_dir)
    zh_path = d / "zh_cn.json"
    if not zh_path.exists():
        print(f"[FATAL] 草稿不存在：{zh_path}", file=sys.stderr)
        return 1
    if not (d / "REVIEW-NOTES.md").exists():
        print("[FATAL] 缺少 REVIEW-NOTES.md 标注清单，先跑 mark_draft.py 再入库", file=sys.stderr)
        return 1

    zh = load_json(zh_path)
    clean, leftovers = {}, []
    for k, v in zh.items():
        if not isinstance(v, str):
            clean[k] = v
            continue
        new_v, stripped = strip_prefixes(v)
        if stripped == "【待翻译】":
            leftovers.append(k)
        clean[k] = new_v
    if leftovers:
        print(f"[FATAL] 仍有 {len(leftovers)} 条未翻译占位：{leftovers[:10]} ...", file=sys.stderr)
        return 1

    # 入库（先写入 projects，再对入库文件跑 Linter）
    lang_dir = REPO_ROOT / "projects" / args.mc_version / "assets" / args.namespace / "lang"
    lang_dir.mkdir(parents=True, exist_ok=True)
    save_json(lang_dir / "zh_cn.json", clean, indent=4)
    if (d / "en_us.json").exists():
        shutil.copy2(d / "en_us.json", lang_dir / "en_us.json")

    if not args.skip_lint:
        r = subprocess.run([sys.executable, str(REPO_ROOT / "src" / "linter" / "run.py"), str(lang_dir)],
                           capture_output=True, text=True)
        print(r.stdout)
        if r.returncode != 0:
            print("[FATAL] Linter 有错误，入库回滚", file=sys.stderr)
            (lang_dir / "zh_cn.json").unlink(missing_ok=True)
            (lang_dir / "en_us.json").unlink(missing_ok=True)
            return 1

    # 归档草稿
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d")
    archive = Path(args.pending_root) / "_approved" / f"{args.mod_dir}-{stamp}"
    archive.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(d), str(archive))
    print(f"[OK] 已入库：{lang_dir / 'zh_cn.json'}")
    print(f"[OK] 草稿归档：{archive}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
