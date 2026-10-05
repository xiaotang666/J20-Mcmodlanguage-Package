# 目录与文件格式说明
## projects/ — J20 自有翻译（核心）

```
projects/<mc_version>/assets/<namespace>/lang/zh_cn.json
projects/<mc_version>/assets/<namespace>/lang/en_us.json   # 源文件（对照用，不打包）
```

- 打包时本目录文件**覆盖** i18n 拉取的同名文件（`overlay_j20.py`）；
- 新增翻译放入对应路径，或经 待审核/ 工作流由 `approve.py` 自动入库；
- 提交前必须过 `python src/linter/run.py projects/`（错误清零）；
- `<mc_version>` 为**版本组**（版本号前两段，如 `1.20`、`26.1`），必须在
  `config/packer/pack-config.json` 的 `pack_formats` 中有映射；组内小版本共用同一资源包。

## tm/ — 翻译记忆库（TMX）

- 每个模组一个 `<modid>.tmx`（OmegaT 项目的 `omegat/project_save.tmx` 直接复制）；
- 标准 TMX 1.4 格式，CI 用 `python src/tm-manager/validate_tmx.py tm/` 校验；
- 贡献翻译时把本目录 TMX 复制到 OmegaT 项目 `tm/auto/` 复用；
- Aaalice 词典导出用 `python src/tm-manager/dict_to_tmx.py <dict.json> <out.tmx>` 转换。

## vaultpatcher/modules/ — VP 硬编码补丁

每个模组一个 `<namespace>.json`，格式（冻结）：

```json
[
  {
    "name": "模组名称汉化补丁",
    "authors": "翻译者",
    "mods": "example-mod",
    "_meta": {
      "mod_version": "1.2.3",
      "mc_version": "1.20.1",
      "last_verified": "2026-10-04"
    }
  },
  {
    "target_classes": ["com.example.ExampleClass"],
    "pairs": {
      "This text is hardcoded": "这段文本是硬编码的",
      "Hardcoded GUI Title": "硬编码界面标题"
    }
  }
]
```

- `pairs` 的键必须与代码中的硬编码字符串**完全一致**（含空格、格式码）；
- **必须**含 `_meta`（`mod_version` / `mc_version` / `last_verified`）：`last_verified` 为最近一次反编译核对日期，入库强制（`check_vp_modules` 会拒绝缺失的模块）。模组更新后必须重新反编译核对并更新；
- 打包为 `vp-modules-{mc_version}.zip`（命名冻结），内部路径必须是 `vaultpatcher/modules/*.json`（仅一层、无子目录、无路径穿越字符，打包与 CI 双重校验）；
- **此包不是资源包**：Vault Patcher 模组只从文件夹加载模块——新版读游戏根目录下 `vaultpatcher/modules/`（旧版为 `config/vaultpatcher_asm/`，VP 会自动迁移），**不读 resourcepacks**。j20UpdateMod 下载后须把包内 `vaultpatcher/modules/` 解压到游戏根目录 `.minecraft/`（使 `.minecraft/vaultpatcher/modules/` 就位），直接丢进 `resourcepacks/` 不会生效；
- 条目仅放真实补丁文件，示例模板不入库。

### Vault Patcher config.json（VP 配置，结构实证自 VP 源码 VaultPatcherConfig.java / VaultPatcher.java）

配置文件位置固定为 **`config/vaultpatcher_asm/config.json`**（游戏目录下，**不随模块迁移**——只有模块文件从旧 `config/vaultpatcher_asm/*.json` 迁到 `vaultpatcher/modules/*.json`，配置仍留在原目录）。完整结构：

```json
{
  "modules": ["j20-create", "j20-mekanism"],
  "default_language": "en_us",
  "class_patch": false,
  "load_all_modules": false,
  "debug_mode": {
    "is_enable": false,
    "output_mode": 0,
    "output_node_debug": false,
    "pairs_hide_limit": 7,
    "export_class": false,
    "use_cache": true
  }
}
```

- **字段名是 `modules`（数组）**——`mods` 只是 VP 源码中的 Java 内部变量名，不是 JSON 字段；数组元素是**模块名，不带 `.json` 后缀**（VP 按 `模块名 + ".json"` 到 `vaultpatcher/modules/` 加载：`"j20-create"` → `j20-create.json`）；
- `load_all_modules: true` 时忽略 `modules` 列表，直接加载 `vaultpatcher/modules/` 下全部 `*.json`（j20UpdateMod 注入模块后二选一：写入 `modules` 数组，或开启 `load_all_modules`）；
- `default_language` 默认 `en_us`；`class_patch` 控制类补丁（读 `vaultpatcher/patch/`）；`debug_mode` 为调试子对象，字段如上，普通用户保持默认即可。

## 资源包固定内容

- `pack.png` — 资源包图标（打包器自动从 `branding/pack.png` 置入包根，游戏内资源包列表显示）；重新生成用 `branding/gen_pack_logo.ps1`。

## glossary/ — 三级术语库

条目格式（文档 4.4.1.2）：

```json
{
  "term": "chunk",
  "translation": "区块",
  "context": "调试命令中译为「区块（16×16×256格）」",
  "source": "vanilla",
  "modid": null,
  "priority": "high",
  "notes": "不要与「区域」「范围」混淆"
}
```

层级与查询优先级：`<modid>.json`（模组专属）→ `mods.json`（模组通用）→ `vanilla.json`（原版标准译名）。

## manifest.json — 版本清单（对外冻结接口）

由 CI 自动生成，j20UpdateMod 读取。冻结字段：`schema_version`、`latest.version`（`YYYY.MM.DD-NNN`）、`latest.packages[]` 的 `mc_version` / `loader` / `asset_name` / `release_url` / `md5` / `size`。`loader` 仅限 forge/fabric/neoforge；VP 包只进可选字段 `vp_packages`。只增不删，禁止改名/改含义。

版本号语义：`YYYY.MM.DD` 为发布日期（UTC），`NNN` 为**全局发布序号**——自 001 起每次发布 +1，不随日期重置（只冻结格式，序号连续递增便于比对新旧）。

## sources.example.json — 下载渠道清单（权威模板）

仓库根 `sources.example.json` 是 j20UpdateMod 内置 `sources.json` 的权威来源，渠道变更以本文件为准同步：

- `manifest_url` / `manifest_mirrors[]` — manifest.json 下载地址（jsdelivr 只能镜像 manifest 等**仓库内文件**，不能镜像 Release 资产）；
- `channels[]` — Release 资产下载渠道，资产 URL 拼法：`{channel.base_url}/{YYYY.MM.DD-NNN}/{asset_name}`，按 `priority` 升序依次回退；
- 一致性要求（模组侧断言，两侧共同遵守）：**先资产后 manifest** 下载；镜像资产必须与 GitHub Release **字节一致**（按 manifest 内 `md5` 校验），不一致即弃用该镜像。
