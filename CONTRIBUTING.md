# 贡献指南

感谢参与 J20-Mcmodlanguage-Package 的翻译与校对！

## 翻译贡献流程

1. **认领任务**：在 Issue 中认领模组；
2. **准备**：安装 OmegaT（omegat.sourceforge.io），可选 Aaalice MC Translator 快速初翻；
3. **翻译**：转换语言文件后在 OmegaT 中逐条翻译，复用 `tm/` 下的翻译记忆库，术语以 `glossary/` 三级术语库为准（查询优先级：模组专属 → 模组通用 → 原版 → zh.minecraft.wiki）；
4. **导出**：译文还原为 `zh_cn.json` 放入 `projects/<mc_version>/assets/<namespace>/lang/`，翻译记忆导出为 `tm/<modid>.tmx`；
5. **自检**：提交前通过翻译质量校验（错误清零）；
6. **提交 PR**：包含译文与翻译记忆，注明是否使用 AI 辅助；
7. **审核**：同行审核 → 维护者终审 → 游戏内测试 → 合并（CI 自动构建发布）。

各步骤的详细操作命令与工具用法见 [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md)。

## 待审核工作流（AI 初翻）

i18n 未收录/未汉化的模组**不直接入库**：先由 AI 初翻并逐条标注，放入仓库外的 `待审核/` 文件夹，人工审核通过后才允许进入 `projects/`。**AI 译文不得未经人工审核直接提交。** 流程详见 [docs/REVIEW-WORKFLOW.md](docs/REVIEW-WORKFLOW.md)。

## 翻译质量红线（违反即拒收）

- **严禁删改格式符**：`§`/`&` 格式码、`%s %d %2$s`、`{0}`、`{{...}}`、`<item:...>`、`\n` 必须完整保留（违者需三人交叉校验才可合入）；
- UI 文本长度控制在原文 ±15% 以内（短文本），按钮统一"动词+宾语"；
- 中英文之间加空格，菜单项无空格连接，半角标点优先；
- 遵循 Minecraft 标准译名（zh.minecraft.wiki），术语以 `glossary/` 为准；
- 不使用低质网络用语。

完整规范见 [style-guide/README.md](style-guide/README.md)。

## 接口冻结提醒

`manifest.json` 字段、Release 资产命名（`pack-{mc_version}-{loader}.zip` / `vp-modules-{mc_version}.zip`）、资源包与 VP 包内部结构为对 j20UpdateMod 的**冻结接口**，禁止在贡献中变更。新增 MC 版本只新增 package，不改旧 package。详见 [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) 的"接口冻结红线"。
