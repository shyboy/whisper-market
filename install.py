#!/usr/bin/env python3
"""Install the unpacked sharing bundle through Codex's marketplace commands."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import uuid


def codex_command():
    executable = shutil.which("codex")
    if not executable:
        raise RuntimeError("未找到 Codex CLI。请在 Codex 中打开本分享包，按“安装说明.md”让 Codex 帮你安装；或安装官方 Codex CLI 后重试。")
    if os.name == "nt" and Path(executable).suffix.lower() in {".cmd", ".bat", ".ps1"}:
        script = Path(executable).parent / "node_modules/@openai/codex/bin/codex.js"
        node = shutil.which("node")
        if script.is_file() and node:
            return [node, str(script)]
        raise RuntimeError("找到 Codex 启动器，但没有找到对应 Node 入口。请在 Codex 终端手动执行安装说明中的两条命令。")
    return [executable]


def verify(root):
    manifest = json.loads((root / "SHA256.json").read_text(encoding="utf-8"))
    if not isinstance(manifest, dict) or not manifest:
        raise RuntimeError("分享包校验清单无效。")
    for name, digest in manifest.items():
        path = (root / name).resolve()
        if not path.is_relative_to(root) or not path.is_file():
            raise RuntimeError("分享包缺少文件或路径无效：" + name)
        if hashlib.sha256(path.read_bytes()).hexdigest() != digest:
            raise RuntimeError("分享包文件与校验清单不符：" + name + "。请重新解压原包。")
    return manifest


def prepare(source, target):
    source, target = Path(source).resolve(), Path(target).expanduser().resolve()
    manifest = verify(source)
    if target.exists():
        same = all((target / name).is_file() and hashlib.sha256((target / name).read_bytes()).hexdigest() == digest for name, digest in manifest.items())
        if same:
            return target
        target = target.with_name(target.name + "-" + uuid.uuid4().hex[:8])
    target.mkdir(parents=True, exist_ok=False)
    for name in [*manifest, "SHA256.json"]:
        destination = target / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source / name, destination)
    verify(target)
    return target


def main():
    parser = argparse.ArgumentParser(description="安装窃语黑市分享包；不会携带或改写游戏存档。")
    parser.add_argument("--target", type=Path, default=Path.home() / "Games/WhisperMarket/0.1.0")
    parser.add_argument("--prepare-only", action="store_true", help="只校验并复制，不注册到 Codex")
    args = parser.parse_args()
    if sys.version_info < (3, 11):
        raise RuntimeError("需要 Python 3.11 或以上。")
    source = Path(__file__).resolve().parent
    command = None if args.prepare_only else codex_command()
    target = prepare(source, args.target)
    if command:
        subprocess.run([*command, "plugin", "marketplace", "add", str(target)], check=True)
        subprocess.run([*command, "plugin", "add", "whisper-market@whisper-market-share"], check=True)
        print("安装完成。打开一个新的 Codex 对话，说：开始玩窃语黑市。")
    else:
        print("分享包校验与复制完成，尚未注册到 Codex。")
    print("游戏包：", target)
    print("存档与游戏包分开保存在用户本机；不需要作者的 API Key。")


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    try:
        main()
    except (OSError, ValueError, RuntimeError, subprocess.CalledProcessError) as error:
        print("安装未完成：" + str(error), file=sys.stderr)
        sys.exit(1)
