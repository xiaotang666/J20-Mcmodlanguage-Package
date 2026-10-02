# 待审核工作流（AI 初翻 → 人工审核 → 入库）

i18n 库里没有汉化的模组，先由 AI 初步翻译并**逐条标注 AI 翻译位置**，放入仓库外的 `待审核/` 文件夹；人工审核通过后才允许进入仓库 `projects/`，以保证汉化准确性。

## 流程命令

```bash
# 1) 找出 i18n 中未汉化/严重不全的模组（名单写入 待审核/_untranslated.json）
python src/ai-translate/find_untranslated.py \
    --manifest j20-manifest/file-selection.json \
    --config config/merger/i18n-source.json

# 2) AI 初翻（生成草稿；--inline-mark 会给译文加 【AI·待审核】 前缀）
#    api provider 需要环境变量 J20_AI_BASE_URL / J20_AI_API_KEY / J20_AI_MODEL
python src/ai-translate/ai_draft.py --mod-dir <mod_dir> --namespace <ns> --inline-mark

# 3) 生成逐条标注清单 待审核/<mod_dir>/REVIEW-NOTES.md
python src/ai-translate/mark_draft.py --mod-dir <mod_dir>

# 4) 人工审核：对照 REVIEW-NOTES.md 修改 待审核/<mod_dir>/zh_cn.json

# 5) 审核通过后入库（自动跑 Linter，有错误拒绝入库并回滚；草稿归档 _approved/）
#    --mc-version 填版本组（1.20 / 1.21 / 26.1 / 26.2 / 26.3）
python src/ai-translate/approve.py --mod-dir <mod_dir> --namespace <ns> --mc-version 1.20
```

## 标注规则

- AI 翻译条目带 `【AI·待审核】` 前缀（`--inline-mark`）；术语库机翻标 `【术语机翻·待审核】`；术语匹配不到的标 `【待翻译】`；
- 技术串（ID、布尔、纯数字、snake_case、命名空间 ID）原样保留不翻译不标注；
- `REVIEW-NOTES.md` 逐条列出：键、原文、译文、标注（含占位符核对结果）。

## 审核红线

- 占位符/格式码 100% 保留（Linter 卡错误）；
- 仍有 `【待翻译】` 占位的草稿禁止入库（`approve.py` 自动拒绝）；
- 游戏机制、UI 布局、文化语境条目必须逐条人工确认；
- 审核人在 REVIEW-NOTES.md 末尾追加审核记录（审核人/日期/修改条数）；
- **AI 译文不得未经人工审核直接提交或入库。**
