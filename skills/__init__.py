"""
技能注册中心 - 统一加载和管理所有技能模块
"""

from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent


def list_skills() -> list[str]:
    return [d.name for d in SKILL_DIR.iterdir() if d.is_dir() and (d / "__init__.py").exists()]
