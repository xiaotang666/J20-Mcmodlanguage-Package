# 贡献指南

感谢参与 J20-Mcmodlanguage-Package 的翻译与校对！

**三件事速查**：[怎么汉化](#3-怎么汉化翻译怎么做) → [放到哪](#4-放到哪里目录结构) → [怎么命名](#42-命名规范速查表)。想直接照着做一遍，看 [第 2 节完整实例](#2-完整实例跟着做一遍create-120)。

## 1. 太长不看：三步提交

1. **翻译**：从 mod 的 `en_us.json` 翻出 `zh_cn.json`（规则见第 3 节）；
2. **放对位置**：按命名规范放进 `projects/<版本组>/assets/<命名空间>/lang/`（规则见第 4 节）；
3. **自检后提 PR**：跑 `python src/linter/run.py projects/` 错误清零，提交 Pull Request（流程见第 5 节）。

合并后 CI 自动构建发布，玩家端通过 j20UpdateMod 自动获取。

## 2. 完整实例：跟着做一遍（Create 1.20）

### 2.1 例 1：一份词条从原文到定稿

mod jar 里 `assets/create/lang/en_us.json` 的原文：

```json
{
  "item.create.zinc_ingot": "Zinc Ingot",
  "create.tooltip.stressImpact": "Stress Impact: %s",
  "create.tooltip.capacity": "Capacity: %1$s/%2$s mB",
  "create.gui.confirm": "Confirm",
  "create.gui.title.stressometer": "§6Stressometer§r"
}
```

翻译后的 `zh_cn.json`——**键一个没动，只翻值**：

```json
{
  "item.create.zinc_ingot": "锌锭",
  "create.tooltip.stressImpact": "应力影响：%s",
  "create.tooltip.capacity": "容量：%1$s/%2$s mB",
  "create.gui.confirm": "确认",
  "create.gui.title.stressometer": "§6应力表§r"
}
```

逐条对照：

| 条目 | 处理 | 原因 |
| --- | --- | --- |
| `Zinc Ingot` → `锌锭` | 名词短译 | 术语风格对齐 `glossary/vanilla.json` |
| `Stress Impact: %s` | `%s` 原样保留 | 占位符数量与位置不能动 |
| `%1$s/%2$s mB` | 顺序占位符保留，单位 `mB` 不翻 | 技术单位/ID 保留原文 |
| `Confirm` → `确认` | 按钮统一"动词+宾语" | UI 规范 |
| `§6Stressometer§r` | `§6`、`§r` 保留 | 格式码 100% 保留 |

**反例（直接拒收）**：`"create.tooltip.stressImpact": "应力影响："`（丢 `%s`）、`"create.gui.title.stressometer": "应力表"`（删 `§6`/`§r`）。

### 2.2 例 2：文件放哪

Create 1.20.1 → 版本组取前两段 `1.20`；命名空间看 jar 里 `assets/` 下的目录名 `create`：

```
projects/
└── 1.20/                          ← 版本组（1.20.1 的前两段）
    └── assets/
        └── create/                ← 命名空间（jar 内 assets/ 下的目录名）
            └── lang/
                ├── en_us.json     ← 对照（建议附，不打包）
                └── zh_cn.json     ← 译文（必交）
```

同一 mod 还要支持 1.21.1？把同两份文件再放一份到 `projects/1.21/assets/create/lang/`（内容可以相同）。

### 2.3 例 3：自检与 PR

```bash
python src/linter/run.py projects/
```

输出示意（以实际运行为准）：每个文件一行结果，**错误必须为 0**；警告（术语/长度/敏感词/TM）建议修掉。

PR 标题示例：`翻译: Create 1.20.1 简体中文（版本组 1.20）`

PR 描述模板（照抄改数字）：

```
模组：Create 1.20.1
MC 版本：1.20.1（版本组 1.20）
内容：新增 zh_cn.json（123 条），附 en_us.json 对照
AI 辅助：否
自检：linter 错误 0
```

### 2.4 例 4：术语库条目怎么写

给 Create 提交模组专属术语，放 `glossary/create.json`（对象数组，字段与 `glossary/mods.json` 一致）：

```json
[
  {
    "term": "Stress",
    "translation": "应力",
    "context": "Create 机械动力系统的负荷单位",
    "source": "create",
    "modid": "create",
    "priority": "high",
    "notes": "不要译作「压力」"
  }
]
```

通用术语进 `glossary/mods.json`，原版译名进 `glossary/vanilla.json`（新增条目追加到数组末尾即可）。

## 3. 怎么汉化（翻译怎么做）

### 3.1 拿到原文

- 用压缩软件打开 mod 的 `.jar`，找到 `assets/<命名空间>/lang/en_us.json`，这就是原文（键值对格式，**键不要动，只翻译值**）；
- 把它复制出来当底稿，逐条把值翻译成中文，存为同目录结构下的 `zh_cn.json`；
- 补翻场景：i18n 库已有部分翻译时，可从 i18n 取对应 `zh_cn.json` 做底稿，补全缺漏、修正错译（本项目打包时会覆盖 i18n 同名文件）。

### 3.2 翻译规则（完整规范见 [style-guide/README.md](style-guide/README.md)）

- **意译优先**：先理解物品/机制/界面语境再翻译，拒绝逐词机翻腔；
- **格式符 100% 保留**（红线，违反即拒收）：`§a`、`&l`、`%s`、`%d`、`%2$s`、`{0}`、`%msg%`、`\n`、`<br>` 原样保留在译文对应位置，数量不得增减；
- **长度控制**：按钮/标签等短文本译文控制在原文 ±15% 长度内，优先半角标点；
- **术语一致**：以 `glossary/` 三级术语库为准（查询优先级：`<modid>.json` → `mods.json` → `vanilla.json` → [zh.minecraft.wiki](https://zh.minecraft.wiki) 标准译名）；中英文之间加空格，按钮统一"动词+宾语"；
- 不使用低质网络用语；彩蛋二创需标注"创意译文"。

### 3.3 工具（可选，纯文本编辑器也能做）

- [OmegaT](https://omegat.sourceforge.io)：管理翻译记忆（TM），模糊匹配复用旧译；
- Aaalice MC Translator：快速初翻（产出必须人工校对）；
- 翻译记忆提交为 `tm/<modid>.tmx`（OmegaT 项目里的 `omegat/project_save.tmx` 复制改名即可）。

## 4. 放到哪里（目录结构）

### 4.1 路径模板

```
projects/<版本组>/assets/<命名空间>/lang/zh_cn.json   ← 必交：中文译文
projects/<版本组>/assets/<命名空间>/lang/en_us.json   ← 建议附：英文原文（对照用，不打包）
```

完整示例见 [第 2 节](#2-完整实例跟着做一遍create-120)。

### 4.2 命名规范速查表

| 内容 | 位置/命名 | 依据 | 示例 |
| --- | --- | --- | --- |
| 版本组目录 | `projects/<版本组>/`，取 **MC 版本号前两段** | MC 版本 → 版本组 | `1.20.1`→`1.20`，`1.21.11`→`1.21`，`26.1.2`→`26.1` |
| 命名空间目录 | `assets/<命名空间>/`，取 mod jar 内 `assets/` 下的目录名 | mod 资源命名空间 | `create`、`mekanism`、`appliedenergistics2` |
| 译文文件名 | 固定 `zh_cn.json`（简体中文语言键） | MC 语言文件约定 | `zh_cn.json` |
| 对照原文文件名 | 固定 `en_us.json`（不打包，仅对照） | MC 语言文件约定 | `en_us.json` |
| 翻译记忆 | `tm/<modid>.tmx` | mod 标识 | `create.tmx` |
| 术语库 | `glossary/<modid>.json`（模组专属）/ `glossary/mods.json` / `glossary/vanilla.json` | mod 标识 | `create.json` |
| VP 硬编码补丁 | `vaultpatcher/modules/<命名空间>.json`，模块头必须含 `_meta.last_verified` | 命名空间 | `create.json` |

**版本组对照**（当前覆盖 1.20.1 及以上全部正式版）：

| 版本组 | 覆盖的 MC 版本 |
| --- | --- |
| `1.20` | 1.20 – 1.20.6 |
| `1.21` | 1.21 – 1.21.11 |
| `26.1` | 26.1 – 26.1.2 |
| `26.2` | 26.2 |
| `26.3` | 26.3 |

### 4.3 关键概念

- **版本组 = MC 版本号前两段**：同组小版本共用同一份翻译（1.20.1 和 1.20.2 都放 `projects/1.20/`）；一个 mod 同时支持多个版本组时，**每个版本组目录各放一份**（内容可以相同）；
- **命名空间 ≠ 模组文件名**：以 mod jar 内 `assets/` 下的目录名为准（拿不准就看 jar 里语言文件的实际路径，或游戏内物品 ID 的前缀）。常见坑：`applied-energistics-2` 的命名空间是 `appliedenergistics2`，`Mekanism` 是 `mekanism`（全小写）；
- **文件格式**：UTF-8 编码（无 BOM）、标准 JSON——一个扁平对象，`"键": "值"` 逐行排列；**只翻译值，键名一个字符都不能改**；同一文件禁止重复键。

### 4.4 硬编码补丁（VP，进阶）

语言文件覆盖不到的硬编码文本走 Vault Patcher 补丁：放 `vaultpatcher/modules/<命名空间>.json`，`pairs` 的键必须与代码中硬编码字符串**完全一致**（含空格、格式码），模块头**必须**含 `_meta`（`mod_version` / `mc_version` / `last_verified`）。格式与 VP 配置说明见 [docs/FORMATS.md](docs/FORMATS.md)；制作前建议先开 Issue 讨论。

## 5. 提交流程（PR）

1. Fork 本仓库并新建分支（如 `translate/create-1.20`）；
2. 按第 4 节放好文件，跑 `python src/linter/run.py projects/` 确认错误清零；
3. 提 Pull Request，描述里写明：**模组名与版本、对应 MC 版本、是否使用 AI 辅助**（模板见 2.3）；
4. CI 自动跑 Linter 与冻结契约检查；同行审核 → 维护者终审 → 游戏内抽测 → 合并；
5. 合并后 CI 自动构建发布，j20UpdateMod 端自动更新。

**提交时不要碰**：`manifest.json` / `compatibility-report.json`（CI 生成物）、`build/` 产物、以及第 9 节的冻结接口。

## 6. 未审核翻译放哪（待审核/ 工作流与教程）

**原则**：一切**未经人工审核**的译文——AI 初翻稿、拿不准想请人复核的半成品——都先进 `待审核/`，**不入 git 仓库、不进 `projects/`**。审核通过后才由工具入库。

### 6.1 放哪

仓库外、与仓库目录**同级**的 `待审核/` 文件夹（维护者机器上即 `MC汉化库\待审核\`，不随仓库分发、不提交 git）。每个模组一个目录 `<mod_dir>/`：

```
待审核/
└── <mod_dir>/
    ├── zh_cn.json          ← 待审核译文（AI 初翻稿逐条带标注）
    ├── en_us.json          ← 英文原文（对照用）
    ├── REVIEW-NOTES.md     ← 逐条标注清单（键 / 原文 / 译文 / 标注 / 占位符核对结果）
    └── _approved/          ← 入库后自动归档草稿（工具生成，不用手建）
```

**外部贡献者**没有维护者机器的 `待审核/` 目录：按上面结构整理好稿件后开 Issue 联系维护者同步；普通人工翻译直接走 PR 即可（PR 本身就是待审核状态），不需要走 `待审核/`。

### 6.2 标注规则（待审核稿必须遵守）

- AI 译文加 `【AI·待审核】` 前缀；术语库机翻加 `【术语机翻·待审核】`；术语匹配不到的加 `【待翻译】`；
- 技术串（ID、布尔值、纯数字、snake_case、命名空间 ID）原样保留，不翻译不标注；
- `REVIEW-NOTES.md` 逐条列出：键、原文、译文、标注（含占位符核对结果）。

### 6.3 教程：从初翻到入库（维护者/审核人照抄）

```bash
# 1) 找出 i18n 中未汉化/严重不全的模组（名单写入 待审核/_untranslated.json）
python src/ai-translate/find_untranslated.py \
    --manifest j20-manifest/file-selection.json \
    --config config/merger/i18n-source.json

# 2) AI 初翻（生成 待审核/<mod_dir>/zh_cn.json；--inline-mark 自动加标注）
#    需要环境变量 J20_AI_BASE_URL / J20_AI_API_KEY / J20_AI_MODEL
python src/ai-translate/ai_draft.py --mod-dir <mod_dir> --namespace <ns> --inline-mark

# 3) 生成逐条标注清单 待审核/<mod_dir>/REVIEW-NOTES.md
python src/ai-translate/mark_draft.py --mod-dir <mod_dir>

# 4) 人工审核：对照 REVIEW-NOTES.md 逐条修改 待审核/<mod_dir>/zh_cn.json
#    （去掉全部【AI·待审核】/【术语机翻·待审核】前缀，处理掉【待翻译】条目）

# 5) 审核通过后入库（自动跑 Linter，有错误拒绝入库并回滚；草稿归档 _approved/）
#    --mc-version 填版本组（1.20 / 1.21 / 26.1 / 26.2 / 26.3）
python src/ai-translate/approve.py --mod-dir <mod_dir> --namespace <ns> --mc-version 1.20
```

入库后的文件落在 `projects/<版本组>/assets/<命名空间>/lang/`（即第 4 节的标准位置），之后走正常 PR/审核流程。

### 6.4 审核红线

- 占位符/格式码 100% 保留（Linter 卡错误）；
- 仍有 `【待翻译】` 占位的草稿**禁止入库**（`approve.py` 自动拒绝）；
- 游戏机制、UI 布局、文化语境条目必须逐条人工确认；
- 审核人在 `REVIEW-NOTES.md` 末尾追加审核记录（审核人 / 日期 / 修改条数）；
- **AI 译文不得未经人工审核直接提交或入库。**

更多细节见 [docs/REVIEW-WORKFLOW.md](docs/REVIEW-WORKFLOW.md)。

## 7. 常见错误（拒收重灾区）

| 错误 | 后果 | 正确做法 |
| --- | --- | --- |
| 放错版本组（1.20.1 的翻译放进 `1.21/`） | 玩家端加载不到 | 版本组 = MC 版本前两段，查 4.2 对照表 |
| 命名空间抄成模组文件名 | 打包后路径无效 | 以 jar 内 `assets/` 目录名为准 |
| 删改格式码/占位符 | 游戏内乱码/报错 | `§` `%s` `{0}` `\n` 等原样保留 |
| 改了键名或留下重复键 | 对应文本失效 | 只翻译值 |
| AI 译文直接提交 | 拒收 | 走 待审核/ 工作流人工审核 |
| 顺手提交 manifest/build 产物 | CI 冲突 | CI 生成物，还原勿提交 |

## 8. 翻译质量红线（违反即拒收）

- **严禁删改格式符**：`§`/`&` 格式码、`%s %d %2$s`、`{0}`、`{{...}}`、`<item:...>`、`\n` 必须完整保留（违者需三人交叉校验才可合入）；
- UI 文本长度控制在原文 ±15% 以内（短文本），按钮统一"动词+宾语"；
- 中英文之间加空格，菜单项无空格连接，半角标点优先；
- 遵循 Minecraft 标准译名（zh.minecraft.wiki），术语以 `glossary/` 为准；
- 不使用低质网络用语。

完整规范见 [style-guide/README.md](style-guide/README.md)。

## 9. 接口冻结提醒

`manifest.json` 字段、Release 资产命名（`pack-{mc_version}-{loader}.zip` / `vp-modules-{mc_version}.zip`）、资源包与 VP 包内部结构为对 j20UpdateMod 的**冻结接口**，禁止在贡献中变更。新增 MC 版本只新增 package，不改旧 package。详见 [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) 的"接口冻结红线"。
