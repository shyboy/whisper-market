"""Install the WorkBuddy skill for 窃语黑市 into the user-level skills directory.

Copies `skills/whisper-market` next to this script (or --source) into
`~/.workbuddy/skills/whisper-market`, keeps a timestamped backup of a differing
existing install, and verifies the rule engine runs before reporting success.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from datetime import datetime

SKILL_NAME = "whisper-market"
REQUIRED = ["SKILL.md", "scripts/engine.py", "scripts/panel.py", "scripts/story.py"]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def snapshot(root: Path) -> dict:
    return {p.relative_to(root).as_posix(): digest(p) for p in sorted(root.rglob("*")) if p.is_file()}


def skills_home() -> Path:
    override = os.environ.get("WORKBUDDY_SKILLS_DIR")
    if override:
        return Path(override)
    return Path.home() / ".workbuddy" / "skills"


def find_python(explicit: str | None) -> str:
    for candidate in ([explicit] if explicit else []) + [sys.executable, "python", "python3", "py -3"]:
        if not candidate:
            continue
        try:
            probe = subprocess.run([*candidate.split(), "-c",
                                    "import sys;print('%d.%d' % sys.version_info[:2])"],
                                   capture_output=True, text=True, timeout=60)
        except (OSError, subprocess.SubprocessError):
            continue
        if probe.returncode == 0:
            try:
                version = tuple(int(x) for x in probe.stdout.strip().split("."))
            except ValueError:
                continue
            if version >= (3, 11):
                return candidate
    raise RuntimeError("没有找到 Python 3.11 或以上。请先安装 Python，再重新运行本安装器。")


def main() -> int:
    parser = argparse.ArgumentParser(description="安装《窃语黑市》WorkBuddy 技能。")
    parser.add_argument("--source", help="技能源目录，默认取本脚本同级的 skills/whisper-market")
    parser.add_argument("--target", help="安装目标目录，默认 ~/.workbuddy/skills/whisper-market")
    parser.add_argument("--python", help="用于自检的 Python 解释器")
    parser.add_argument("--dry-run", action="store_true", help="只检查，不写入")
    options = parser.parse_args()

    source = Path(options.source).resolve() if options.source else Path(__file__).resolve().parent / "skills" / SKILL_NAME
    if not source.is_dir():
        source = Path(__file__).resolve().parent / "skills" / SKILL_NAME
    missing = [rel for rel in REQUIRED if not (source / rel).is_file()]
    if missing:
        print(json.dumps({"ok": False, "error": "技能源不完整，缺少：" + "、".join(missing),
                          "source": str(source)}, ensure_ascii=False, indent=2))
        return 2
    target = Path(options.target).resolve() if options.target else skills_home() / SKILL_NAME
    python = find_python(options.python)
    incoming = snapshot(source)
    backup = None
    if target.is_dir():
        if snapshot(target) == incoming:
            shutil.rmtree(target)
        else:
            backup = target.with_name(f"{target.name}.bak_{datetime.now():%Y%m%d_%H%M%S}")
            target.rename(backup)
    if not options.dry_run:
        shutil.copytree(source, target, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    check = subprocess.run([*python.split(), str(target / "scripts" / "engine.py"), "help"],
                           capture_output=True, text=True, timeout=120, encoding="utf-8")
    if check.returncode != 0 or "\"actions\"" not in check.stdout:
        print(json.dumps({"ok": False, "error": "规则引擎自检失败", "detail": check.stdout + check.stderr,
                          "target": str(target)}, ensure_ascii=False, indent=2))
        return 3
    print(json.dumps({
        "ok": True, "installed": str(target), "files": len(incoming),
        "backup": str(backup) if backup else None, "python": python,
        "dry_run": options.dry_run,
        "next": "新开一个 WorkBuddy 对话（必要时重启应用以载入新技能），说：开始玩窃语黑市。",
    }, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
