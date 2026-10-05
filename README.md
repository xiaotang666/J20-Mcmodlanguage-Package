# J20-Mcmodlanguage-Package

面向 Minecraft 模组的中文汉化资源包项目。

本项目收集整理各模组的语言文件，组织社区翻译、校对与审核，整合 CFPAOrg i18n 库的翻译资源与 Vault Patcher 硬编码汉化补丁，打包为可直接使用的汉化资源包，并通过 GitHub Release 与国内镜像分发，支持 j20UpdateMod 自动下载与更新。

## 功能特性

- **模组语言汉化**：整合 i18n 库指定模组翻译 + 本项目自有翻译（覆盖合并）
- **硬编码汉化**：内置 Vault Patcher 补丁模块，汉化语言文件覆盖不到的硬编码文本
- **自动更新**：提供 `manifest.json` 版本清单，j20UpdateMod 可自动获取、下载并注入游戏
- **国内镜像**：GitHub Release 之外提供国内加速下载渠道
- **质量保障**：三级术语库、翻译记忆库（TMX）、风格指南与自动校验，AI 初翻必须经人工审核后才入库

## 下载与使用

- **资源包**：前往 [Releases](https://github.com/xiaotang666/J20-Mcmodlanguage-Package/releases) 下载对应版本的资源包，放入 `.minecraft/resourcepacks/` 后在游戏内启用；
- **自动更新**：使用 j20UpdateMod 的玩家无需手动下载，模组会自动获取最新汉化并注入游戏；
- **下载渠道**：国内用户优先使用镜像源，失败时自动回退 GitHub。

资源包命名规则（固定不可更改）：

| 资产 | 说明 |
| --- | --- |
| `pack-{mc_version}-{loader}.zip` | 最终汉化资源包（按 MC 版本组与加载器区分） |
| `vp-modules-{mc_version}.zip` | Vault Patcher 硬编码补丁模块包 |

`mc_version` 为 MC 版本组（版本号前两段），当前覆盖 **1.20 / 1.21 / 26.1 / 26.2 / 26.3**（即 1.20.1 及以上的所有 MC 版本）：组内小版本共用同一资源包（如 1.20.1 与 1.20.2 都用 `pack-1.20-*`），Forge 与 NeoForge 共用同一份内容（对齐 i18n 库的打包方式）。Release 版本号格式为 `YYYY.MM.DD-NNN`（发布日期 + 全局发布序号）。

## 翻译来源与致谢

- [CFPAOrg/Minecraft-Mod-Language-Package](https://github.com/CFPAOrg/Minecraft-Mod-Language-Package)（i18n 库）—— 模组翻译的主要来源
- [CFPAOrg/Glossary](https://github.com/CFPAOrg/Glossary) —— 术语库基础
- 所有参与翻译、校对与审核的社区贡献者

## 参与贡献

欢迎参与翻译与校对！贡献流程、翻译质量红线见 [CONTRIBUTING.md](CONTRIBUTING.md)，翻译规范见 [style-guide/README.md](style-guide/README.md)。

开发构建、工具脚本与内部格式说明见 [docs/](docs/)（面向维护者，普通用户无需关注）。

## 协议声明与修改说明

本项目遵循 **CC BY-NC-SA 4.0**（署名—非商业性使用—相同方式共享）协议，**禁止任何商业用途**。

本项目基于 CFPAOrg i18n 库改编，所做的修改包括：按清单选择性拉取指定模组的翻译文件（非全量复制）、用自有翻译覆盖同名文件、新增 i18n 未收录的翻译、追加 Vault Patcher 硬编码补丁模块。资源包内保留 i18n 库协议副本（`LICENSE-i18n`）、本项目协议（`LICENSE-j20`）与署名文件（`ATTRIBUTION.md`）。

衍生作品必须以相同协议分发。本项目不暗示 i18n 作者或 CFPAOrg 为本项目背书。完整署名与修改说明见 [ATTRIBUTION.md](ATTRIBUTION.md)。
