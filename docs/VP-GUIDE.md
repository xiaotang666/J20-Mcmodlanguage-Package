# Vault Patcher 硬编码汉化制作指南

> 本指南教你从零做出可用的 VP 汉化模块。零基础按第 3 节七步走；想直接抄，跳到 [第 4 节实战案例](#4-实战案例dangomusic可照抄)。
> 格式细节已对照 VP 源码（`Pairs.java` / `ModuleInfo.java` / `TargetClassInfo.java`）核实。

## 0. 什么时候需要 VP

模组文本有两种存在方式：

| 存在方式 | 特征 | 汉化手段 |
| --- | --- | --- |
| 语言文件 | jar 里有 `assets/<ns>/lang/en_us.json` | 资源包（`projects/` 提交 `zh_cn.json`，见 CONTRIBUTING） |
| **硬编码** | 文本写死在 .class 里，**没有 lang 文件或文本不在 lang 里** | **VP 模块（本文档）** |

判断方法：游戏里把语言切成英文、开一个只有你汉化的资源包——**不受资源包影响、依然显示英文的文本就是硬编码**。

## 1. 原理（30 秒版）

Vault Patcher 是一个 Fabric/Forge/NeoForge 模组，启动时读取模块文件（JSON），按你给的
`目标类 + 原文` 清单，在**字节码加载前**把类常量池里的英文字符串原位替换成中文。
所以：它不改 mod 文件本身、对所有加载器生效，但**只认常量字符串的精确匹配**。

**时机决定一切（重要）**：VP 在启动早期装载模块，随后只对**首次加载**的类做字节码替换——
**已经加载过的类无法回溯替换**。因此会出现"按类分界"的部分生效现象（例如同一个词 `Glow`
在 UI 类的副本被翻了、在模块定义类的副本没翻）。要全部生效，必须满足两个"早于"：
① 模块文件部署 **早于** VP 装载（见排查表"部署晚于加载"）；② 目标类首次加载 **晚于** VP 装载。

## 2. 模块文件结构（逐字段）

文件放 `vaultpatcher/modules/<命名空间>.json`（命名空间一般取 modid），整体是一个数组：
第 1 项是**模块头**（元信息），第 2 项起是**补丁体**（可多组）。VP 会忽略不认识的字段
（所以本项目强制的 `_meta` 可以安全地写在模块头里）。

```json
[
  {
    "name": "Dango Music 汉化补丁",
    "desc": "Dango Music 1.4.1 硬编码文本汉化",
    "authors": "小坣",
    "mods": "dangomusic",
    "_meta": {
      "mod_version": "1.4.1",
      "mc_version": "26.2",
      "last_verified": "2026-10-24"
    }
  },
  {
    "target_classes": ["me.sorihiko.dango.musicui.PartyPage"],
    "pairs": [
      { "key": "Create a room", "value": "创建房间" },
      { "key": "Leave room", "value": "离开房间" }
    ]
  }
]
```

### 模块头字段

| 字段（简写） | 必填 | 说明 |
| --- | --- | --- |
| `name`（`n`） | ✅ | 补丁名，随意起 |
| `authors`（`a`） | ✅ | 作者/翻译者 |
| `mods`（`m`） | ✅ | 对应 mod 的 modid |
| `desc`（`d`） | — | 描述（缺省 "No description"） |
| `dynamic`（`y`/`dyn`） | — | 动态替换模式，见 6.2（默认 `false`） |
| `i18n`（`i`） | — | `value` 作为 VP 自带 i18n 的键解析，一般不用（默认 `false`） |
| `_meta` | ✅（本项目强制） | `mod_version` / `mc_version` / `last_verified`（最近一次反编译核对日期；**模组更新后必须重新核对**）。VP 不认识此字段但会忽略，安全 |

### 补丁体字段（数组第 2 项起，每组独立）

| 字段（简写） | 必填 | 说明 |
| --- | --- | --- |
| `target_classes`（`t`/`s`/`target_class`） | ✅ | 要替换的 Java 类名数组，**点分格式** `me.sorihiko.dango.musicui.PartyPage`（不是 `me/sorihiko/...`）。**省略 = 全局替换一切类，危险别省** |
| `pairs`（`p`） | ✅ | **`{"key","value"} 对象的数组`**（不是 JSON 对象映射！写成对象 VP 加载时直接报错）；`k`/`v` 是简写别名。**key 必须与代码字符串完全一致**（含空格、大小写、标点、占位符），key/value 顺序可颠倒 |
| `info`（`i`） | ❌ | 进阶精确定位，字段见第 6 节，一般用不到 |

## 3. 制作流程（七步）

1. **收集原文**：游戏内把界面过一遍，把不受资源包影响的英文抄下来（截图/记事本都行）。
2. **定位类名**：用反编译工具（推荐 [Recaf](https://recaf.coley.software)）打开 jar，搜索字符串，
   在对应类上右键 → `Copy Path`，把 `/` 换成 `.` 就是 `target_classes` 的值。
3. **写 pairs**：一条原文一条译文；原文照抄，一个字符都不能差。
4. **一串多类**：同一段文本出现在多个类里（常量在每个用到的类里都有一份）→ `target_classes`
   把这些类全列上，否则只有一处生效。
5. **写 `_meta`**：`mod_version` / `mc_version` / `last_verified` 三个都填。
6. **放置与启用**：文件命名 `<命名空间>.json` 放 `vaultpatcher/modules/`（游戏根目录）；
   VP 配置 `config/vaultpatcher_asm/config.json` 里把模块名（**不带 .json**）加进 `modules` 数组，
   或直接开 `"load_all_modules": true`（加载 modules 目录下全部 json，最省事）。
7. **进游戏验证（必须逐界面逐条）**：每个设置页、弹窗、按钮、提示都过一遍，对照
   `debug_mode` 的 `Trying replacing` 日志；**只看一两个界面不算验证完成**——
   "按类分界"的部分生效只有全界面排查才能发现（见第 5 节排查表）。不生效的条目按第 5 节排查。

## 4. 实战案例：DangoMusic（可照抄）

对象：`DangoMusic-1.4.1+26.2-fabric-2.jar`——**没有 lang 文件，全部文本硬编码**，典型的 VP 适用模组。

### 4.1 收集到的原文与翻译（节选）

| 代码中的原文（key） | 译文（value） | 出现位置（类） |
| --- | --- | --- |
| `Create a room` | 创建房间 | PartyPage |
| `Your playlists` | 你的歌单 | MusicScreen |
| `Horizontal position (or drag it with chat open)` | 水平位置（或在聊天框打开时拖动） | SongCardModule |
| `How far away 3D lyrics appear (blocks)` | 3D 歌词出现的距离（格） | LyricsModule |
| `Listen Together is not set up (missing firebase.properties)` | 未配置一起听（缺少 firebase.properties） | PartyPage |

### 4.2 完整模块文件（`vaultpatcher/modules/dangomusic.json`）

```json
[
  {
    "name": "Dango Music 汉化补丁",
    "desc": "Dango Music 1.4.1 硬编码文本汉化",
    "authors": "小坣",
    "mods": "dangomusic",
    "_meta": {
      "mod_version": "1.4.1",
      "mc_version": "26.2",
      "last_verified": "2026-10-24"
    }
  },
  {
    "target_classes": ["me.sorihiko.dango.musicui.PartyPage"],
    "pairs": [
      { "key": "Create a room", "value": "创建房间" },
      { "key": "OR JOIN WITH A ROOM CODE", "value": "或使用房间码加入" },
      { "key": "ROOM CODE", "value": "房间码" },
      { "key": "Join", "value": "加入" },
      { "key": "Leave room", "value": "离开房间" },
      { "key": "Listen Together is not set up (missing firebase.properties)", "value": "未配置一起听（缺少 firebase.properties）" },
      { "key": "IN THIS ROOM · ", "value": "房间内 · " },
      { "key": "Following ", "value": "正在跟随 " },
      { "key": "  (you)", "value": "（你）" }
    ]
  },
  {
    "target_classes": ["me.sorihiko.dango.module.impls.music.SongCardModule"],
    "pairs": [
      { "key": "Horizontal position (or drag it with chat open)", "value": "水平位置（或在聊天框打开时拖动）" },
      { "key": "Vertical position (or drag it with chat open)", "value": "垂直位置（或在聊天框打开时拖动）" }
    ]
  }
]
```

**逐点讲解这个案例里的关键技巧**：

- **拼接片段直接翻片段本身**：像 `"  (you)"`、`" of "`、`" songs"`、`" charts"` 这类是代码
  **运行时拼接**用的常量片段（如 `"3" + " songs"`）。拼接结果没法整体匹配，但**片段常量本身可以替换**：
  `" songs"` → `" 首歌曲"`。注意**保留前导空格**（拼接靠它分隔）。
- **同串多类**：`"Dango Music"` 在 `DangoMusic.class` 和 `ModernMusicScreen.class` 都有 →
  `target_classes` 两个类都写，或分两组补丁体各写一个类。
- **占位符照抄**：`"Dango Music: graphics backend is {}, ..."` 里的 `{}` 必须原样保留在译文里。
- **key 建议去重**：`pairs` 是数组，同一 key 写两条不报错，但**后一条会覆盖前一条**；
  模棱两可不如去重，翻译取统一版本。
- **大写常量**：`"NOW PLAYING"`、`"MY PLAYLISTS"` 这类装饰性全大写文本照常替换；含 `·`、`…`、
  全角标点的 key 一定从代码里**原样复制**，别手敲。
- **收集原文要"双保险"**：游戏内**逐屏截图抄录** + 反编译**搜常量**核对，两条路取并集——
  纯靠脚本关键词过滤容易漏（装饰性全大写、无空格短词都可能被过滤器误杀，如 `DISCOVER`）。

### 4.3 VP 配置（`config/vaultpatcher_asm/config.json`）

```json
{
  "modules": ["dangomusic"],
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

最省事的开法：把 `"load_all_modules"` 改成 `true`，`modules` 数组留空都行——
VP 会加载 `vaultpatcher/modules/` 下全部 `.json`。

## 5. 调试与排查

替换不生效时，按顺序查：

| 检查项 | 症状 | 处理 |
| --- | --- | --- |
| **部署晚于加载（首次启动无效）** | **模块刚部署/更新后的第一次启动全英文** | VP 在启动最初几秒读模块，j20UpdateMod 等部署动作在其后——**重启一次游戏**即可；每次更新模块都遵循"第二次启动生效" |
| **部分类翻了、部分类没翻** | 同一个词的两个副本一翻一翻不翻（如组标题中文、设置项英文） | 未翻的类在 VP 装载**前**就已被 mod 提前加载（加载时变换无法回溯）——重启一次通常解决；顽固不生效的说明该 mod 初始化过早，需 mod 侧提前部署模块或延迟初始化，并开 debug 对照 `Trying replacing` 日志确认类名 |
| 模块没被加载 | 整个模块无效 | `config.json` 的 `modules` 加了模块名？（不带 `.json`）或开 `load_all_modules` |
| 文件放错位置 | 整个模块无效 | 必须是游戏根目录 `vaultpatcher/modules/<名>.json`（不是 resourcepacks，不是 config） |
| **pairs 写成了对象** | **整个模块加载报错/无效** | **必须是 `[{"key":…,"value":…}]` 数组**，对象映射 `{"原文":"译文"}` 会解析失败 |
| 键不一致 | 单条无效 | 空格/大小写/标点/占位符逐字符核对，**从代码或 xlsx 原样复制** |
| 同串多类 | 换了 A 界面没换 B 界面 | `target_classes` 补上另一个类 |
| 动态拼接 | 显示"3 首歌曲"这类没换 | 替换的是片段常量，检查片段键是否正确 |
| 想看 VP 到底替换了什么 | — | `debug_mode.is_enable: true`，日志会打印 `Trying replacing! '原文' -> '译文' in <类>` |

`debug_mode.output_mode`：`0` 只显示实际发生替换的条目；`1` 显示全部尝试（排查键不一致时用 1）。

## 6. 进阶：`info` 精确定位与动态替换（极少用）

### 6.1 `info` 限定替换范围

同一类里相同文本出现在多个方法、或需要按操作序数（ordinal）区分时，用 `info` 限定。
**字段只有这些**（不存在 `match_mode`/`local_mode` 之类的独立字段）：

| 字段（简写） | 说明 |
| --- | --- |
| `method`（`m`） | 只替换该方法内的常量 |
| `local`（`l`） | 按变量定位。**首字母是模式前缀**：`V`=局部变量、`M`=方法返回值、`R`=调用返回值、`G`/`F`=全局变量、`A`=数组元素，其余=不限。例：`"GresearchName"` 定位全局变量 `researchName` |
| `annotation` | 按注解定位，对象：`{"desc": "注解描述符", "ak": "注解键", "type": "CLASS/FIELD/METHOD/ALL"}`（`descriptor`/`annokey` 同义） |
| `ordinal`（`o`） | 操作序数：数字 `24`；或字符串 `"24,30"`（多个）、`"24-30"`（区间）、`"24-e"`（到末尾）。序数看 debug 日志里的 `[24]` 标记 |

示例（取自 VP wiki）：

```json
{
  "target_classes": ["com.example.ResearchWidget"],
  "info": {
    "method": "renderHover",
    "local": "GresearchName",
    "ordinal": 24
  },
  "pairs": [
    { "key": "Backpacks", "value": "小背包" }
  ]
}
```

### 6.2 动态替换（`dynamic` 模式）

模块头写 `"dynamic": true` 后语义变化：`target_classes` 的元素变成"动态名"——
`@` 前缀=前缀匹配、`#` 前缀=后缀匹配、无前缀=全匹配；`pairs` 的 value 以 `@` 开头表示半匹配替换。
适用于文本按变量拼接、无法整串匹配的复杂场景。**99% 的补丁用不到**，先用最简结构，匹配不到再考虑。

## 7. 提交到本项目

- 模块文件放 `vaultpatcher/modules/<命名空间>.json`（模块头必须带 `_meta`，CI 强制检查）；
- 按模块文件名（不带 `.json`）在 PR 描述里说明；配套的 `pairs` 原文/译文对照表建议一并附上（xlsx/md 均可）；
- 打包器会自动把模块打进 `vp-modules-{版本组}.zip`，j20UpdateMod 端解压到游戏根目录生效。
