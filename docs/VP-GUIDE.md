# Vault Patcher 硬编码汉化制作指南

> 本指南教你从零做出可用的 VP 汉化模块。零基础按第 3 节七步走；想直接抄，跳到 [第 4 节实战案例](#4-实战案例dangomusic可照抄)。

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

## 2. 模块文件结构（逐字段）

文件放 `vaultpatcher/modules/<命名空间>.json`（命名空间一般取 modid），整体是一个数组：

```json
[
  {
    "name": "Dango Music 汉化补丁",
    "authors": "小坣",
    "mods": "dangomusic",
    "_meta": {
      "mod_version": "1.4.1",
      "mc_version": "26.2",
      "last_verified": "2026-10-24"
    }
  },
  {
    "target_classes": ["me.sorihiko.dango.ui.PartyPage"],
    "pairs": {
      "Create a room": "创建房间",
      "Leave room": "离开房间"
    }
  }
]
```

| 字段 | 位置 | 必填 | 说明 |
| --- | --- | --- | --- |
| `name` | 模块头（数组第 1 项） | ✅ | 补丁名，随意起 |
| `authors` | 模块头 | ✅ | 作者/翻译者 |
| `mods` | 模块头 | ✅ | 对应 mod 的 modid |
| `_meta` | 模块头 | ✅（本项目强制） | `mod_version` 补丁对应模组版本 / `mc_version` MC 版本 / `last_verified` 最近一次反编译核对日期（**模组更新后必须重新核对并更新**） |
| `target_classes` | 补丁体（数组第 2 项起） | ✅ | 要替换的 Java 类名列表，**点分格式**：`me.sorihiko.dango.ui.PartyPage`（不是 `me/sorihiko/...`） |
| `pairs` | 补丁体 | ✅ | `{"代码里的原文": "译文"}`，**键必须与代码字符串完全一致**（含空格、大小写、标点、占位符） |
| `info` | 补丁体 | ❌ | 进阶精确定位（method/local/ordinal/match_mode），一般用不到，见第 6 节 |

一条 `pairs` 可以有多组补丁体：数组第 2、3、4… 项各自带自己的 `target_classes` + `pairs`，
按类分组写，方便管理。

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
7. **进游戏验证**：逐条检查界面；不生效的条目按第 5 节排查。

## 4. 实战案例：DangoMusic（可照抄）

对象：`DangoMusic-1.4.1+26.2-fabric-2.jar`——**没有 lang 文件，全部文本硬编码**，典型的 VP 适用模组。

### 4.1 收集到的原文与翻译（节选）

| 代码中的原文（键） | 译文 | 出现位置（类） |
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
    "authors": "小坣",
    "mods": "dangomusic",
    "_meta": {
      "mod_version": "1.4.1",
      "mc_version": "26.2",
      "last_verified": "2026-10-24"
    }
  },
  {
    "target_classes": ["me.sorihiko.dango.ui.PartyPage"],
    "pairs": {
      "Create a room": "创建房间",
      "OR JOIN WITH A ROOM CODE": "或使用房间码加入",
      "ROOM CODE": "房间码",
      "Join": "加入",
      "Leave room": "离开房间",
      "Listen Together is not set up (missing firebase.properties)": "未配置一起听（缺少 firebase.properties）",
      "IN THIS ROOM · ": "房间内 · ",
      "Following ": "正在跟随 ",
      "  (you)": "（你）"
    }
  },
  {
    "target_classes": ["me.sorihiko.dango.module.SongCardModule"],
    "pairs": {
      "Horizontal position (or drag it with chat open)": "水平位置（或在聊天框打开时拖动）",
      "Vertical position (or drag it with chat open)": "垂直位置（或在聊天框打开时拖动）"
    }
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
- **键唯一**：同一原文在表格里出现多次（比如多处都是 `"no response"`）→ `pairs` 里**只能有一条**，
  JSON 不允许重复键，翻译取统一版本。
- **大写常量**：`"NOW PLAYING"`、`"MY PLAYLISTS"` 这类装饰性全大写文本照常替换；含 `·`、`…`、
  全角标点的键一定从代码里**原样复制**，别手敲。

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
| 模块没被加载 | 整个模块无效 | `config.json` 的 `modules` 加了模块名？（不带 `.json`）或开 `load_all_modules` |
| 文件放错位置 | 整个模块无效 | 必须是游戏根目录 `vaultpatcher/modules/<名>.json`（不是 resourcepacks，不是 config） |
| 键不一致 | 单条无效 | 空格/大小写/标点/占位符逐字符核对，**从代码或 xlsx 原样复制** |
| 同串多类 | 换了 A 界面没换 B 界面 | `target_classes` 补上另一个类 |
| 动态拼接 | 显示"3 首歌曲"这类没换 | 替换的是片段常量，检查片段键是否正确 |
| 想看 VP 到底替换了什么 | — | `debug_mode.is_enable: true`，日志会打印 `Trying replacing! '原文' -> '译文' in <类>` |

`debug_mode.output_mode`：`0` 只显示实际发生替换的条目；`1` 显示全部尝试（排查键不一致时用 1）。

## 6. 进阶：`info` 精确定位（极少用）

同一类里相同文本出现在多个方法、或需要按操作序数（ordinal）区分时，用 `info` 限定范围：

```json
{
  "target_classes": ["com.example.ExampleClass"],
  "info": {
    "method": "renderHover",
    "match_mode": "FULL",
    "local_mode": "GLOBAL_VARIABLE",
    "local": "exampleName",
    "ordinal": 24
  },
  "pairs": { "This text is hardcoded": "这段文本是硬编码的" }
}
```

字段含义：`method` 目标方法名 / `match_mode` FULL 精确匹配 / `local` 局部变量名 /
`ordinal` 操作序数（VP debug 日志里会打印 `[24]` 这样的序数，填进来即可）/ `local_mode` 变量匹配模式。
**99% 的补丁用不到 `info`**，先用最简结构，匹配不到再加。

## 7. 提交到本项目

- 模块文件放 `vaultpatcher/modules/<命名空间>.json`（模块头必须带 `_meta`，CI 强制检查）；
- 按模块文件名（不带 `.json`）在 PR 描述里说明；配套的 `pairs` 原文/译文对照表建议一并附上（xlsx/md 均可）；
- 打包器会自动把模块打进 `vp-modules-{版本组}.zip`，j20UpdateMod 端解压到游戏根目录生效。
