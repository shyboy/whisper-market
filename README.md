# 窃语黑市 · Whisper Market

由杨老师制作的中文单人叙事游戏，在 Codex 或 WorkBuddy 对话中用自己的话行动。当前提供第一章《失窃的账本》，附场景插画、本地记录和自动存档。

![窃语黑市场景插画](plugins/whisper-market/assets/inn.png)

## 选择你的版本

**按自己使用的软件下载一个版本即可，不必两个都装。** 两个版本使用相同的剧情与规则，同一台电脑上共用默认存档目录。

| 你使用的软件 | 下载 v0.1.1 | 安装说明 |
|---|---|---|
| Codex | [下载 Codex 版 ZIP](https://github.com/shyboy/whisper-market/releases/download/v0.1.1/whisper-market-codex-v0.1.1.zip) | [Codex 安装说明](安装说明.md) |
| WorkBuddy | [下载 WorkBuddy 版 ZIP](https://github.com/shyboy/whisper-market/releases/download/v0.1.1/whisper-market-workbuddy-v0.1.1.zip) | [WorkBuddy 安装说明](WorkBuddy版.md) |

两个版本都需要 **Python 3.11 或以上**，不需要 Python 第三方库。请完整解压下载包，再打开解压后的文件夹。游戏使用你在对应应用中选择的模型和自己的额度，不包含模型或作者的 API Key。

安装完成后，在对应应用中**新开一个对话**，说：**“开始玩窃语黑市。”** 基本操作见[玩家指南](玩家指南.md)，指南不提供剧情攻略。

## Codex 安装

有 Codex CLI 时，也可以直接从 GitHub 安装：

```text
codex plugin marketplace add shyboy/whisper-market
codex plugin add whisper-market@whisper-market-share
```

通过 ZIP 安装时，Windows 可双击 `Windows安装.cmd`；自动安装需要 Python 和 Codex CLI。只有桌面应用时，按[安装说明](安装说明.md)让 Codex 协助安装。

## WorkBuddy 安装

Windows 可双击解压目录中的 `WorkBuddy安装.cmd`，或在 WorkBuddy 中打开解压目录，说：

> 请读取 WorkBuddy版.md，为我安装窃语黑市技能。

终端安装使用 `python install-workbuddy.py`。只检查、不安装使用 `python install-workbuddy.py --dry-run`。详细步骤见[WorkBuddy 安装说明](WorkBuddy版.md)。

## 当前版本与验证范围

v0.1.1 是安装与分发更新：提供两个独立下载包，修复 WorkBuddy 检查模式改动已有安装、Python 路径含空格等问题。第一章游戏规则和存档格式沿用 v0.1.0。

提供自然语言交互、自动存档、独立新开局与检查点恢复；交易与资源由本地程序结算，对话由所在应用的模型生成。面板用于查看已有记录，行动在对话中输入。

这是早期版本。发布前检查包括游戏规则、安装回归和下载包校验；WorkBuddy 应用内技能触发、连续对话和预览，以及 macOS/Linux 安装体验仍待实测。后续章节尚未开放。

## 存档与分享

Windows 默认存档位于 `%LOCALAPPDATA%/WhisperMarket`；macOS/Linux 位于 `~/.local/share/WhisperMarket`。存档与插件目录分开，更新或分享游戏包时不要附带存档。

[Releases](https://github.com/shyboy/whisper-market/releases) 同时提供两个 ZIP 和各自的 `.sha256` 文件；包内 `SHA256.json` 用于核对文件完整性，不是数字签名。

仓库只包含可分发的插件、素材、安装器和玩家说明。`plugins/whisper-market` 是 Codex 插件，`skills/whisper-market` 是从同一源码生成的 WorkBuddy 技能；其中主持人规则包含剧情细节，想保留探索体验可以直接开始游戏。
