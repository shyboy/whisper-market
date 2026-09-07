# 窃语黑市 · Whisper Market

由杨老师制作的中文单人叙事游戏，在 Codex 或 WorkBuddy 对话中用自己的话行动。当前提供第一章《失窃的账本》，附场景插画、本地记录和自动存档。

![窃语黑市场景插画](plugins/whisper-market/assets/inn.png)

## 开始游玩

需要已登录且有可用模型额度的 Codex，以及 Python 3.11 或以上。游戏使用玩家自己选择的 Codex 模型，不需要作者的 API Key。游玩会使用你的 Codex 额度。

**有 Codex CLI：**

```text
codex plugin marketplace add shyboy/whisper-market
codex plugin add whisper-market@whisper-market-share
```

安装后打开一个新的 Codex 对话，说：**“开始玩窃语黑市。”**

**通过文件安装：**

从 [Releases](https://github.com/shyboy/whisper-market/releases) 下载分享 ZIP 并解压，按[安装说明](安装说明.md)操作。Windows 可双击 `Windows安装.cmd`；自动安装需要可用的 Python 和 Codex CLI。只有桌面应用时，安装说明也提供了让 Codex 协助安装的方法。

基本操作见[玩家指南](玩家指南.md)。指南不提供剧情攻略。

## 在 WorkBuddy 中游玩

同一个游戏也做成了 WorkBuddy 技能，在 WorkBuddy 对话里玩，规则、剧情和存档与 Codex 版一致。需要 WorkBuddy 与 Python 3.11 或以上。

```text
python install-workbuddy.py
```

Windows 也可以双击 `WorkBuddy安装.cmd`；或把 `skills/whisper-market` 整个文件夹复制到 `~/.workbuddy/skills/whisper-market`。安装后**新开一个对话**，说：**“开始玩窃语黑市。”**

详情见[WorkBuddy版说明](WorkBuddy版.md)。两端共用同一存档目录，同一台电脑上进度互通。

## 本版本

- 第一章内容、场景插画与本地只读情报面板。
- 自然语言交互、自动保存、独立新开局与检查点恢复。
- 交易及资源变化由本地程序结算，角色对话由 Codex 或 WorkBuddy 的模型生成。

这是早期版本。规则与发行相关的 21 项测试已通过，Windows 上已验证本地安装与隔离安装。真实玩家体验、不同模型的对话效果以及 macOS/Linux 安装仍待验证；后续章节尚未开放。

## 存档与文件

Windows 默认存档位于 `%LOCALAPPDATA%/WhisperMarket`；macOS/Linux 位于 `~/.local/share/WhisperMarket`，与插件版本目录分开。更新或分享游戏包不需要附带存档。

本仓库只包含可分发的插件、素材、安装器和玩家说明。`SHA256.json` 核对发行文件完整性，不是数字签名。保留原始换行格式是校验的一部分。

`plugins/whisper-market` 和 `skills/whisper-market` 中的规则和主持人文件含剧情细节；想保留探索体验，直接开始游戏即可。两份内容同源：Codex 插件是唯一真源，WorkBuddy 技能由它生成。
