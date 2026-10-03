# Changelog

本项目自身版本号从 0.0.1 起递增（语义化迭代：Bug 修复 +0.0.1，重大功能 +0.1.0，架构变更 +1.0.0）。
Release 发布版本号另按对外接口冻结格式 `YYYY.MM.DD-NNN` 自动生成，两者独立。

## 0.2.3 — 2026-10-04

### 变更
- 图标重设计为平面海报风格（米白/油墨黑分割 + 朱红基条 + 跨界反转字形），去除 AI 味（零渐变/发光/圆角徽章/装饰点）；逐字固定定位规避 GDI+ 文本测量误差

## 0.2.2 — 2026-10-04

### 变更
- 图标改为蓝色渐变设计（深海军蓝 -> 亮天蓝 + 斜向光带 + 冰蓝分隔线），观感重做

## 0.2.1 — 2026-10-04

### 新增
- 资源包专属图标 `pack.png`（`branding/` 下 PowerShell 脚本生成，256×256），打包器自动置入包根，校验器纳入必检项
- 文档明确 VP 模块包用法：VP 只从游戏根目录 `vaultpatcher/modules/` 加载模块（不读资源包），`vp-modules-*.zip` 须解压到游戏目录而非 `resourcepacks/`

## 0.2.0 — 2026-10-02

### 新增
- `daily-check.yml`：每日 00:00（北京时间）检测 i18n 库是否更新（对比 `main` HEAD SHA 与 `config/merger/i18n-state.json` 记录）——有更新才触发重新打包发布，无更新跳过不打包
- `build.yml` 改为可复用工作流（`workflow_call`），构建时记录 i18n HEAD SHA 并随 manifest 回写仓库

## 0.1.0 — 2026-10-02

### 变更
- 版本矩阵重构（对齐 i18n 大版本分组）：`mc_version` 改为**版本组**（版本号前两段），覆盖 **1.20 / 1.21 / 26.1 / 26.2 / 26.3**（1.20.1 及以上全部 MC 版本），组内小版本共用同一资源包
- 三加载器矩阵：forge / fabric / neoforge 全覆盖；**NeoForge 与 Forge 共用同一份内容**（i18n "(Neo)Forge" 共包模式，产出同名字节副本）
- pack.mcmeta 按版本组分代生成：1.20 用 `pack_format:15`+`supported_formats:[15,32]`；1.21 双方案（旧客户端 `pack_format`+`supported_formats`，1.21.9+ `min_format`/`max_format`）；26.x 用 `min_format`/`max_format` 元组
- 拉取器按「版本组 × 内容组」分树（`build/i18n-extracted/<版本组>/<forge|fabric>/`），Fabric 内容自动优先 i18n 的 `-fabric` 版本目录；同 URL 只拉一次
- VP 打包器支持按 `vp_groups` 全量产出
- `ai_draft.py` 输出容错解析（剥离代码围栏 / 正则提取 JSON 对象）

### 删除
- 移除 1.16.5 目标包与 `pack_format_table` 旧映射结构（不再支持 1.20.1 以下版本）

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
