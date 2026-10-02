# Changelog

本项目自身版本号从 0.0.1 起递增（语义化迭代：Bug 修复 +0.0.1，重大功能 +0.1.0，架构变更 +1.0.0）。
Release 发布版本号另按对外接口冻结格式 `YYYY.MM.DD-NNN` 自动生成，两者独立。

## 0.0.1 — 2026-10-02

### 新增
- 首版基础设施（文档阶段一）：仓库目录结构、i18n 拉取/覆盖/打包/校验全链路脚本（纯标准库）
- `j20-manifest/file-selection.json` 与 `config/merger/i18n-source.json`：按 i18n 真实目录结构（`projects/assets/<mod_dir>/<版本>/<namespace>/lang/`）修正拉取路径模式
- 三级术语库：`glossary/vanilla.json`（1648 条）+ `glossary/mods.json`（1705 条），自 CFPAOrg/Glossary 导入
- Linter：占位符/格式码/术语/长度/敏感词/TM 一致性检查
- 兼容性检查器：manifest 冻结契约、资产命名、pack_format 映射、VP 结构、协议合规
- CI：build.yml（构建发布）、compatibility-check.yml（PR 检查）、sync-mirror.yml（镜像同步骨架）
- 待审核工作流：find_untranslated / ai_draft / mark_draft / approve（AI 初翻 + 逐条标注 + 人工审核入库）
- 协议合规文件：LICENSE / LICENSE-i18n / ATTRIBUTION.md（CC BY-NC-SA 4.0，含 i18n 署名与修改说明）
