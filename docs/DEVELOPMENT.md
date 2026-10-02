# 开发与构建说明（开发者文档）

本文档面向维护者与贡献者，包含本地构建、脚本用法与 CI 说明。普通用户请看仓库根 README。

## 环境要求

- Python 3.11+（仅用标准库，无需 pip 安装依赖）
- Git
- 网络：`raw.githubusercontent.com` 在国内被墙时走 `ghproxy.net` / `jsdelivr` 回退（已内置于拉取器）

## 本地构建全流程

```bash
# 1. 按清单从 i18n 仓库拉取指定模组的翻译文件（含镜像回退 + 重试）
python src/merger/fetch_i18n_files.py \
    --manifest j20-manifest/file-selection.json \
    --config config/merger/i18n-source.json \
    --output build/i18n-extracted/

# 2. J20 自有翻译覆盖 i18n 拉取结果
python src/merger/overlay_j20.py --source projects/ --target build/i18n-extracted/

# 3. 打包 VP 模块与最终资源包
python src/packer/build_vp.py --mc-version 1.20.1 --output build/
python src/packer/build_final.py --lang-dir build/i18n-extracted/ --output build/

# 4. 校验产物与协议合规
python src/merger/verify.py build/pack-*.zip
python src/merger/check_license.py build/pack-*.zip

# 5. 生成 manifest 与兼容性报告
python src/packer/gen_manifest.py --build-dir build/
python src/compatibility-checker/run_all.py build/
```

产物（命名冻结，禁止更改）：`build/pack-{mc_version}-{loader}.zip`、`build/vp-modules-{mc_version}.zip`。

## 脚本清单

| 脚本 | 职责 |
| --- | --- |
| `src/merger/fetch_i18n_files.py` | 按清单从 i18n 仓库 Raw 链接拉取指定文件（多镜像回退） |
| `src/merger/overlay_j20.py` | J20 自有翻译覆盖拉取结果（同名覆盖） |
| `src/merger/verify.py` | 校验最终资源包结构（pack.mcmeta/语言文件/LICENSE/VP 路径） |
| `src/merger/check_license.py` | 协议合规检查（包内/仓库，含防背书表述检查） |
| `src/packer/build_vp.py` | 打包 VP 模块为 `vp-modules-{mc_version}.zip` |
| `src/packer/build_final.py` | 打包最终资源包（含 pack.mcmeta 署名） |
| `src/packer/gen_manifest.py` | 生成 manifest.json（版本 `YYYY.MM.DD-NNN` 自动递增） |
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
2. **Release 发布版本**：`YYYY.MM.DD-NNN`（对外接口冻结格式），由 `gen_manifest.py` 自动生成，NNN 为当日构建序号。

## CI 工作流

| 工作流 | 触发 | 作用 |
| --- | --- | --- |
| `build.yml` | main 推送（翻译/配置/脚本变更） | Lint → 兼容性检查 → 拉取 → 覆盖 → 打包 → 校验 → 发布 Release → 回写 manifest |
| `compatibility-check.yml` | PR | Lint + 全部冻结契约检查 + TMX 校验 |
| `sync-mirror.yml` | build 成功后 / 每日定时 | 先资产后 manifest 同步镜像（渠道待接入，见 TODO） |

## 接口冻结红线（改前必读）

- manifest.json 冻结字段、`YYYY.MM.DD-NNN` 版本格式
- Release 资产命名 `pack-{mc_version}-{loader}.zip` / `vp-modules-{mc_version}.zip`
- 资源包内部结构 `pack.mcmeta + assets/<ns>/lang/zh_cn.*`
- VP 包内部结构 `vaultpatcher/modules/*.json`

只增不删；破坏性变更必须发版通知 j20UpdateMod，并保留旧资产（最近 10 个 Release 不删）。

## 调整拉取清单

编辑 `j20-manifest/file-selection.json`：i18n 真实路径是 `projects/assets/<mod_dir>/<版本目录>/<namespace>/lang/`，**mod_dir 与 namespace 常见不一致**（如 `applied-energistics-2` → `appliedenergistics2`），且版本目录是粗粒度（`1.20`/`1.18`/…，可能带 `-fabric` 后缀），`i18n_version_dirs` 按优先级排列候选。拉取清单变更不影响 j20UpdateMod（属低风险变更），更新 merge_info 即可。
