# Changelog

本项目自身版本号从 0.0.1 起递增（语义化迭代：Bug 修复 +0.0.1，重大功能 +0.1.0，架构变更 +1.0.0）。
Release 发布版本号另按对外接口冻结格式 `YYYY.MM.DD-NNN` 自动生成，两者独立。

## 0.3.0 — 2026-10-27

### 重大变更（打包完整性）
- 构建资产改为**i18n 发布包全量基底**：`fetch_i18n_release.py` 按版本组 × 内容组拉取 i18n 最新资源包（`releases/latest/download` 直链）解包为底座，`projects/` 覆盖其上，VP 包照旧——资源包从 6 个命名空间变为与 i18n 官方包等量的全量覆盖（实测 1.21 组 406 个命名空间）
- 资产映射配置 `config/merger/i18n-release.json`：1-20/1-21/26-1 及 -fabric 变体实测存在；26.2/26.3 暂回退 26-1 包（i18n 未分包），i18n 分包后改映射即可
- 原 file-selection 逐文件拉取降级为**增量补充**（发布包未单列的 create/botania 等自带官中 mod 的社区修正）
- `projects/` 用户翻译（如 slate_menu）经 overlay 覆盖进包，实测生效
- 自动重建触发条件：i18n **发布新资产**（daily-check 改以 release tag 为判据）或 `projects/`、`vaultpatcher/` 任一变更，均**全量重建全部版本组**（不只建变更组）

## 0.2.12 — 2026-10-27

### 修正（根因定谳）
- VP-GUIDE "部分生效/旧译残留"根因更正为 **VP 类变换缓存不失效翻译表**（源码实证：VPClassTransformer 缓存分支 + ClassCache.updated 仅比对原类 sha256），并给出解法：更新模块后清空 vaultpatcher/cache/ 或 use_cache:false（j20UpdateMod 侧应在部署后清缓存）
- 排查表与配置节同步加入"更新模块后必做"提示

## 0.2.11 — 2026-10-27

### 移除
- `vaultpatcher/modules/dangomusic.json`（DangoMusic 作者已自行提供官方汉化，不再需要本项目 VP 补丁）

### 文档（DangoMusic 实测结论）
- VP-GUIDE 补"按类分界"部分生效根因：VP 为类加载时变换，只能替换模块装载后首次加载的类，早加载的类无法回溯（实测铁证：同一键 Glow 在 SettingsPage 副本已翻、LyricsModule 副本未翻）
- 验证要求升级为逐界面逐条 + debug 日志对照；原文收集改"游戏内逐屏 + 反编译搜常量"双保险

## 0.2.10 — 2026-10-27

### 文档
- VP-GUIDE 排查表补"部署晚于加载"条目：VP 启动早期读模块而 j20UpdateMod 部署在其后，模块更新后需重启一次生效（实测 DangoMusic 案例定位）

## 0.2.9 — 2026-10-25

### 修正（对照 VP 源码实证）
- **pairs 格式纠正**：必须是 `[{"key":…,"value":…}]` 对象数组（Pairs.readJson 强制 beginArray()），此前文档/模块误用对象映射会导致 VP 加载失败——dangomusic.json 全量转换（160 条），VP-GUIDE/FORMATS 示例同步更正
- VP-GUIDE info 字段纠正：删除不存在的 match_mode/local_mode，改为源码实有的 method/local(模式前缀字母)/annotation/ordinal(数字|列表|区间)；补模块头 desc/dynamic/i18n 可选字段与各字段简写别名；新增 dynamic 动态替换说明
- check_vp_modules 校验加固：逐补丁体强制 pairs 数组形态与 key/value 对象（拒绝对象映射）

## 0.2.8 — 2026-10-24

### 文档
- 新增 docs/VP-GUIDE.md：Vault Patcher 硬编码汉化制作指南——七步流程、逐字段结构说明、DangoMusic 实战案例（可照抄模块配置）、拼接片段/同串多类/占位符技巧、调试排查表、info 进阶
- FORMATS.md / CONTRIBUTING.md 的 VP 节接入教程链接
- 首个 VP 模块 `vaultpatcher/modules/dangomusic.json`（DangoMusic 1.4.1+26.2）：160 条 pairs 按 29 组类分组，含 xlsx 补漏条目；模块含 21 条 AI 译文待人工确认

## 0.2.7 — 2026-10-23

### 文档
- CONTRIBUTING.md 补"一个 jar 多个 lang"真实案例（Slate Menu 套件 7 个命名空间）：多命名空间各翻各放、一次 PR 全带、只处理 en_us→zh_cn、原版命名空间不翻、多加载器 jar 只翻一次

## 0.2.6 — 2026-10-23

### 变更
- `projects/` 预建五个版本组目录（1.20 / 1.21 / 26.1 / 26.2 / 26.3）；确定汉化目录**只按游戏版本组组织、不按加载器细分**（语言文件与加载器无关，加载器差异由拉取层 -fabric 变体与打包层 copy_of 消化）

## 0.2.5 — 2026-10-23

### 文档
- CONTRIBUTING.md 重写为贡献者上手指南：三步速查、怎么汉化（原文获取/翻译规则/自检命令）、放哪与命名规范速查表（版本组/命名空间/文件名）、PR 流程、常见错误表
- CONTRIBUTING.md 补可照抄实战实例：词条对照（含格式码/占位符处理与反例）、目录树、自检与 PR 模板、术语库示例
- CONTRIBUTING.md 补未审核翻译说明与教程：`待审核/` 位置与目录结构、标注规则、从初翻到入库全流程命令、审核红线
- README 参与贡献入口直接指向上述速查表

## 0.2.4 — 2026-10-05

### 修正
- FORMATS.md 补全 Vault Patcher config.json 权威结构（实证自 VP 源码）：字段为 **`modules`**（非 `mods`）、路径固定 `config/vaultpatcher_asm/config.json`（不随模块迁移）、`load_all_modules` 等完整字段样例
- Release 版本 NNN 语义统一为**全局发布序号**（自 001 起每次发布 +1，不随日期重置），脚本与 README/DEVELOPMENT/FORMATS 口径一致

### 新增
- `src/packer/verify_release.py` 发布冒烟校验：CI 发布 Release 后逐资产下载 `release_url` 核对 md5/size，不通过即阻断 manifest 回写
- 仓库根 `sources.example.json` 下载渠道权威清单（j20UpdateMod 内置 sources.json 对齐模板）
- VP 包 zip 结构校验进 CI（`check_vp_zip.py`：仅 `vaultpatcher/modules/*.json` 一层、禁路径穿越）
- VP 模块 `_meta.last_verified` 入库强制（缺失拒绝打包入库）
- 文档补充 Release 清理策略（保留历史 manifest 引用资产）与本地构建产物禁提交规则

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
