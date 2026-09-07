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
import tempfile
import uuid
from datetime import datetime

SKILL_NAME = "whisper-market"
REQUIRED = ["SKILL.md", "scripts/engine.py", "scripts/panel.py", "scripts/story.py",
            "assets/inn.png", "assets/alley.png", "assets/guard.png"]


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def snapshot(root: Path) -> dict:
    return {p.relative_to(root).as_posix(): digest(p) for p in sorted(root.rglob("*"))
            if p.is_file() and "__pycache__" not in p.relative_to(root).parts and p.suffix != ".pyc"}


def skills_home() -> Path:
    override = os.environ.get("WORKBUDDY_SKILLS_DIR")
    if override:
        return Path(override)
    return Path.home() / ".workbuddy" / "skills"


def find_python(explicit: str | None) -> list[str]:
    candidates = [[explicit]] if explicit else [[sys.executable], ["python"], ["python3"], ["py", "-3"]]
    for candidate in candidates:
        if not candidate[0]:
            continue
        try:
            probe = subprocess.run([*candidate, "-B", "-c",
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


def check_engine(python: list[str], root: Path) -> None:
    check = subprocess.run([*python, "-B", str(root / "scripts/engine.py"), "help"],
                           capture_output=True, text=True, timeout=120, encoding="utf-8")
    if check.returncode != 0:
        raise RuntimeError("规则引擎自检失败：" + check.stdout + check.stderr)
    output = json.loads(check.stdout)
    if not isinstance(output, dict) or "actions" not in output:
        raise RuntimeError("规则引擎自检未返回行动清单。")


def install(source: Path, target: Path, python: list[str], dry_run: bool = False) -> dict:
    source, target = source.resolve(), target.resolve()
    if target.is_relative_to(source) or source.is_relative_to(target):
        raise RuntimeError("技能源和安装目标不能相同或互相包含。")
    missing = [rel for rel in REQUIRED if not (source / rel).is_file()]
    if missing:
        raise RuntimeError("技能源不完整，缺少：" + "、".join(missing))
    if target.exists() and not target.is_dir():
        raise RuntimeError("安装目标已存在且不是目录。")
    incoming = snapshot(source)
    same = target.is_dir() and snapshot(target) == incoming
    result = {"ok": True, "target": str(target), "files": len(incoming),
              "backup": None, "python": python, "dry_run": dry_run,
              "changed": False, "installed": None}
    if dry_run:
        check_engine(python, source)
        result["next"] = "检查通过，未写入安装目录。去掉 --dry-run 后安装。"
        return result
    if not same:
        target.parent.mkdir(parents=True, exist_ok=True)
        # Validate a complete staged copy before moving an existing installation.
        with tempfile.TemporaryDirectory(prefix=".whisper-market-", dir=target.parent) as folder:
            staged = Path(folder) / SKILL_NAME
            shutil.copytree(source, staged, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
            check_engine(python, staged)
            backup = None
            if target.exists():
                backup = target.with_name(f"{target.name}.bak_{datetime.now():%Y%m%d_%H%M%S}_{uuid.uuid4().hex[:8]}")
                target.rename(backup)
            try:
                staged.rename(target)
            except OSError:
                if backup is not None:
                    backup.rename(target)
                raise
            result.update(changed=True, backup=str(backup) if backup else None)
    else:
        check_engine(python, target)
    result.update(installed=str(target),
                  next="新开一个 WorkBuddy 对话（必要时重启应用以载入新技能），说：开始玩窃语黑市。")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="安装《窃语黑市》WorkBuddy 技能。")
    parser.add_argument("--source", help="技能源目录，默认取本脚本同级的 skills/whisper-market")
    parser.add_argument("--target", help="安装目标目录，默认 ~/.workbuddy/skills/whisper-market")
    parser.add_argument("--python", help="用于自检的 Python 解释器")
    parser.add_argument("--dry-run", action="store_true", help="只检查，不写入")
    options = parser.parse_args()

    source = Path(options.source).resolve() if options.source else Path(__file__).resolve().parent / "skills" / SKILL_NAME
    target = Path(options.target).resolve() if options.target else skills_home() / SKILL_NAME
    try:
        result = install(source, target, find_python(options.python), options.dry_run)
    except (OSError, RuntimeError, ValueError, subprocess.SubprocessError) as error:
        print(json.dumps({"ok": False, "error": str(error)}, ensure_ascii=False, indent=2))
        return 2
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    sys.exit(main())
