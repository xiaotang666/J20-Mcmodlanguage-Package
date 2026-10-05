# 开发与构建说明（开发者文档）

本文档面向维护者与贡献者，包含本地构建、脚本用法与 CI 说明。普通用户请看仓库根 README。

## 环境要求

- Python 3.11+（仅用标准库，无需 pip 安装依赖）
- Git
- 网络：`raw.githubusercontent.com` 在国内被墙时走 `ghproxy.net` / `jsdelivr` 回退（已内置于拉取器）

## 本地构建全流程

```bash
# 1. 按清单从 i18n 仓库拉取指定模组的翻译文件（含镜像回退 + 重试；按版本组 × 内容组分树）
python src/merger/fetch_i18n_files.py \
    --manifest j20-manifest/file-selection.json \
    --config config/merger/i18n-source.json \
    --pack-config config/packer/pack-config.json \
    --output build/i18n-extracted/

# 2. J20 自有翻译覆盖 i18n 拉取结果（自动遍历 projects/ 全部版本组）
python src/merger/overlay_j20.py --source projects/ --target build/i18n-extracted/

# 3. 打包 VP 模块与最终资源包（按 pack-config 的 vp_groups / packs 全量产出）
python src/packer/build_vp.py --output build/
python src/packer/build_final.py --lang-dir build/i18n-extracted/ --output build/

# 4. 校验产物与协议合规
python src/merger/verify.py build/pack-*.zip
python src/merger/check_license.py build/pack-*.zip

# 5. 生成 manifest 与兼容性报告
python src/packer/gen_manifest.py --build-dir build/
python src/compatibility-checker/run_all.py build/
```

产物（命名冻结，禁止更改）：`build/pack-{版本组}-{loader}.zip`、`build/vp-modules-{版本组}.zip`。

> **注意**：本地构建产出的 `manifest.json` / `compatibility-report.json` **禁止提交**（详见文末"接口冻结红线"）。

## 版本组规则（对齐 i18n 大版本分组）

`mc_version` = 版本号**前两段**（`1.20.1`→`1.20`，`1.21.11`→`1.21`，`26.1.2`→`26.1`）；组内小版本共用同一资源包。当前覆盖 **1.20 / 1.21 / 26.1 / 26.2 / 26.3**（即 1.20.1 及以上的所有 MC 正式版）。

| 版本组 | 覆盖 | pack.mcmeta 方案 |
| --- | --- | --- |
| `1.20` | 1.20 – 1.20.6 | `pack_format:15` + `supported_formats:[15,32]` |
| `1.21` | 1.21 – 1.21.11 | 双方案：`pack_format:34` + `supported_formats:[34,64]`（≤1.21.8）+ `min_format:[69,0]/max_format:[75,9]`（≥1.21.9） |
| `26.1` | 26.1 – 26.1.2 | `min_format:[65,0]/max_format:[84,9]` |
| `26.2` | 26.2 | `min_format:[85,0]/max_format:[88,9]` |
| `26.3` | 26.3 | `min_format:[89,0]/max_format:[97,9]` |

加载器共享（对齐 i18n）：Forge 与 NeoForge 共用同一份内容（`copy_of: "forge"`，字节级副本改名产出），Fabric 独立（拉取时自动优先 i18n 的 `-fabric` 版本目录）。新增版本组时：在 `pack_formats` 加格式声明 + `packs[]` 加三个目标包 + `vp_groups` 加组名 + `file-selection.json` 加版本组配置即可。

## 脚本清单

| 脚本 | 职责 |
| --- | --- |
| `src/merger/fetch_i18n_files.py` | 按清单从 i18n 仓库 Raw 链接拉取指定文件（多镜像回退） |
| `src/merger/overlay_j20.py` | J20 自有翻译覆盖拉取结果（同名覆盖） |
| `src/merger/verify.py` | 校验最终资源包结构（pack.mcmeta/语言文件/LICENSE/VP 路径） |
| `src/merger/check_license.py` | 协议合规检查（包内/仓库，含防背书表述检查） |
| `src/packer/build_vp.py` | 打包 VP 模块为 `vp-modules-{mc_version}.zip` |
| `src/packer/build_final.py` | 打包最终资源包（含 pack.mcmeta 署名） |
| `src/packer/gen_manifest.py` | 生成 manifest.json（版本 `YYYY.MM.DD-NNN`：日期 + 全局发布序号） |
| `src/packer/verify_release.py` | 发布冒烟校验（逐资产下载 release_url 核对 md5/size） |
| `src/linter/run.py` | 翻译质量 Linter（错误阻断构建） |
| `src/compatibility-checker/*` | 冻结契约检查（manifest/资产/pack_format/VP/协议） |
| `src/ai-translate/*` | 待审核工作流（见 docs/REVIEW-WORKFLOW.md） |
| `src/tm-manager/validate_tmx.py` | TMX 校验（XML/tuid/srclang） |
| `src/tm-manager/dict_to_tmx.py` | Aaalice 词典导出转 TMX |
| `src/tm-manager/import_cfpa_glossary.py` | 从 CFPAOrg/Glossary 导入三级术语库 |
| `src/formatter/json2properties.py` / `properties2json.py` | JSON ↔ OmegaT .properties |

## Linter 使用

```bash
python src/linter/run.py projects/ --json build/lint-report.json
```

错误（阻断）：JSON 非法、重复键、占位符不一致、格式码丢失；
警告（放行）：术语违规、长度超限、敏感词、TM 一致性。

## 版本号管理（两套，勿混淆）

1. **项目版本**：从 `0.0.1` 起语义化递增（Bug 修复 +0.0.1 / 重大功能 +0.1.0 / 架构变更 +1.0.0），记录于 `CHANGELOG.md`；
2. **Release 发布版本**：`YYYY.MM.DD-NNN`（对外接口冻结格式），由 `gen_manifest.py` 自动生成：日期为发布日（UTC），**NNN 为全局发布序号**——自 001 起每次发布 +1，不随日期重置。

## CI 工作流

| 工作流 | 触发 | 作用 |
| --- | --- | --- |
| `build.yml` | main 推送（翻译/配置/脚本变更）/ daily-check 调用 / 手动 | Lint → 兼容性检查 → 记录 i18n HEAD → 拉取 → 覆盖 → 打包 → 校验 → 发布 Release → **发布冒烟校验（逐资产下载核对 md5）** → 回写 manifest |
| `daily-check.yml` | 每日 00:00（北京时间，UTC 16:00）/ 手动 | 对比 i18n `main` HEAD SHA 与 `config/merger/i18n-state.json` 记录：有更新才触发 `build.yml` 重新打包，无更新直接跳过 |
| `compatibility-check.yml` | PR | Lint + 全部冻结契约检查 + TMX 校验 |
| `sync-mirror.yml` | build 成功后 / 每日定时 | 先资产后 manifest 同步镜像（渠道待接入，权威渠道清单见仓库根 `sources.example.json`） |

## 接口冻结红线（改前必读）

- manifest.json 冻结字段、`YYYY.MM.DD-NNN` 版本格式
- Release 资产命名 `pack-{mc_version}-{loader}.zip` / `vp-modules-{mc_version}.zip`
- 资源包内部结构 `pack.mcmeta + assets/<ns>/lang/zh_cn.*`
- VP 包内部结构 `vaultpatcher/modules/*.json`

只增不删；破坏性变更必须发版通知 j20UpdateMod（最近 10 个 Release 不删）。**Release 清理策略**：清理更旧版本时，历史 `manifest.json` 曾引用过的资产必须全部保留（j20UpdateMod 离线回退使用缓存 manifest 指向旧资产），仅可删除从未被任何 manifest 引用的资产。

**本地构建产物禁提交**：`manifest.json` / `compatibility-report.json` 由 CI 发布后回写，本地手动跑 packer 生成的版本号对应并不存在的 Release，提交会使 manifest 指向 404 资产。本地测试后请 `git checkout -- manifest.json compatibility-report.json` 还原。CI 侧由发布冒烟校验（`verify_release.py`）兜底：任一 `release_url` 不可下载或 md5/size 不符即阻断回写。

## 调整拉取清单

编辑 `j20-manifest/file-selection.json`：i18n 真实路径是 `projects/assets/<mod_dir>/<版本目录>/<namespace>/lang/`，**mod_dir 与 namespace 常见不一致**（如 `applied-energistics-2` → `appliedenergistics2`），且版本目录是粗粒度（`1.20`/`1.18`/…，可能带 `-fabric` 后缀），`i18n_version_dirs` 按优先级排列候选。拉取清单变更不影响 j20UpdateMod（属低风险变更），更新 merge_info 即可。
