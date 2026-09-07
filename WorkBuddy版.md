# 窃语黑市 · WorkBuddy 版

同一个游戏，换一个能玩的地方。《窃语黑市》原本是 Codex 插件，这里提供 **WorkBuddy 技能**版本：在 WorkBuddy 对话里用自己的话行动，规则、存档和剧情与 Codex 版完全一致。

![窃语黑市场景插画](skills/whisper-market/assets/inn.png)

## 需要什么

- 已安装并能正常对话的 WorkBuddy。
- Python 3.11 或以上，负责本地规则与存档，**不需要任何第三方库**。

游戏使用当前对话的模型，不需要作者的 API Key。游玩会消耗你自己的模型额度。游戏内金币是虚构资源。

## 安装

先[下载 WorkBuddy 版 ZIP](https://github.com/shyboy/whisper-market/releases/download/v0.1.1/whisper-market-workbuddy-v0.1.1.zip)，完整解压后打开里面的文件夹。不要下载 Codex 版 ZIP，也不要只取出一个安装脚本。

### 方式一：让 WorkBuddy 帮你装（推荐）

在 WorkBuddy 里打开解压后的目录（或本仓库目录），说：

> 请运行 `install-workbuddy.py` 为我安装窃语黑市技能，安装后告诉我怎么开始。

安装器会先验证完整副本，再复制到用户级技能目录。内容相同的已有安装保持不动；更新不同内容时保留旧版备份，替换失败会尝试恢复。存档目录不参与安装。

### 方式二：命令行

```text
python install-workbuddy.py
```

Windows 也可以双击 `WorkBuddy安装.cmd`。

只检查而不安装：`python install-workbuddy.py --dry-run`。该模式不创建或改动安装目录。Python 路径含空格时，可用 `--python "C:\Program Files\Python311\python.exe"` 指定完整路径。

### 方式三：手动复制

把 `skills/whisper-market/` 整个文件夹复制到技能目录：

| 系统 | 技能目录 |
|---|---|
| Windows | `%USERPROFILE%\.workbuddy\skills\whisper-market` |
| macOS / Linux | `~/.workbuddy/skills/whisper-market` |

复制后目录里应当有 `SKILL.md`、`scripts/` 和 `assets/`。**不要只复制 `SKILL.md`**，规则程序在 `scripts/` 里。

## 开始玩

安装后**新开一个 WorkBuddy 对话**（必要时重启应用让新技能载入），说：

> 开始玩窃语黑市

之后用自己的话描述想做的事或想说的话即可，不需要记命令。说出口的话和心里的想法请表达清楚，例如"我对他说……"和"我心想……"。

- **继续**：`继续我的窃语黑市存档`
- **查看记录**：`查看记录`（情报面板会用预览面板打开，刷新看最新）
- **回到先前进度**：`查看检查点`
- **另开一局**：`重新开一局`（旧局保留）
- 基本操作见[玩家指南](玩家指南.md)，指南不含剧情攻略。

## 存档与 Codex 版的关系

两端共用同一个默认存档目录：Windows `%LOCALAPPDATA%/WhisperMarket`，macOS / Linux `~/.local/share/WhisperMarket`。同一台电脑上，Codex 版和 WorkBuddy 版的进度互通，说"继续"即可接上。

想分开测试，可以在子命令前加 `--home <目录>`，例如 `python scripts/engine.py --home D:\验收\tmp start`（`--home` 必须放在子命令前）。

分享游戏包时不要附带存档目录。

## 卸载

删除技能目录即可，例如 Windows 上删除 `%USERPROFILE%\.workbuddy\skills\whisper-market`。卸载不会删除存档，重新装上还能继续。

## 维护者：如何重建本目录

Codex 插件 `plugins/whisper-market/`（主项目里的 `whisper-market/`）是唯一真源，**不要手改 `skills/` 下的生成文件**。主项目里运行：

```text
python tools/build_workbuddy.py
```

它会复制规则程序与素材，只改写技能 frontmatter、路径规则和平台措辞，然后输出到公开仓库工作目录，同时生成独立 WorkBuddy ZIP 及校验文件；若上游措辞变化导致改写点找不到，构建会直接报错而不是静默产出旧版。安装器、本文档及首页一并由该脚本同步。
