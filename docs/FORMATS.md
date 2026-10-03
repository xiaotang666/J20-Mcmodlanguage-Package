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
    "mods": "example-mod"
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
- 建议追加 `_meta`（`mod_version` / `mc_version` / `last_verified`）标记补丁对应模组版本，模组更新后重新反编译核对；
- 打包为 `vp-modules-{mc_version}.zip`（命名冻结），内部路径必须是 `vaultpatcher/modules/*.json`；
- **此包不是资源包**：Vault Patcher 模组只从文件夹加载模块——新版读游戏根目录下 `vaultpatcher/modules/`（旧版为 `config/vaultpatcher_asm/`，VP 会自动迁移），**不读 resourcepacks**。j20UpdateMod 下载后须把包内 `vaultpatcher/modules/` 解压到游戏根目录 `.minecraft/`（使 `.minecraft/vaultpatcher/modules/` 就位），直接丢进 `resourcepacks/` 不会生效；VP 的 `config.json` 的 `mods` 列表需包含对应模块名（或开启 `load_all_modules`）；
- 条目仅放真实补丁文件，示例模板不入库。

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
