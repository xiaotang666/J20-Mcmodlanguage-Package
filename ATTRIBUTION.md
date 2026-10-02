# 署名与协议声明（ATTRIBUTION）

## 来源

J20-Mcmodlanguage-Package 的翻译资源整合自以下来源：

1. **CFPAOrg/Minecraft-Mod-Language-Package（i18n 库）**
   - 地址：https://github.com/CFPAOrg/Minecraft-Mod-Language-Package
   - 协议：CC BY-NC-SA 4.0
   - 使用方式：按 `j20-manifest/file-selection.json` 清单直接拉取指定模组的 `zh_cn` 语言文件
   - 资源包内保留其协议副本 `LICENSE-i18n`
2. **CFPAOrg/Glossary（术语表）**
   - 地址：https://github.com/CFPAOrg/Glossary
   - 用途：构建 `glossary/vanilla.json` 与 `glossary/mods.json` 三级术语库
3. 本项目自有翻译（社区贡献 + AI 初翻经人工审核）

## 对 i18n 库所做的修改

1. **选择性拉取**：不全量复制，仅按清单拉取指定模组的语言文件；
2. **覆盖同名文件**：J20 自有翻译覆盖 i18n 拉取的同名 `zh_cn` 文件；
3. **新增翻译**：补充 i18n 未收录模组的翻译（经 AI 初翻 + 人工审核流程）；
4. **打包整合**：与 Vault Patcher 硬编码补丁模块一并打包为最终资源包。

## 协议

- 合并后的整体资源包：**CC BY-NC-SA 4.0**（署名—非商业性使用—相同方式共享）
- **禁止商业用途**：本资源包不得用于任何商业场景
- 衍生作品必须以相同协议（CC BY-NC-SA 4.0）分发
- 原始协议全文见包内 `LICENSE-i18n` 与 `LICENSE-j20`

## 免责声明

本项目不暗示 i18n 作者或 CFPAOrg 为 J20-Mcmodlanguage-Package 背书。i18n 库版权归原作者所有，如有异议请联系本项目维护者，将立即处理。
