"""启动脚本 - 微信公众号全自动发布智能体"""

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"


def main():
    sys.path.insert(0, str(SRC_DIR))
    from src.main import main as app_main
    app_main()


if __name__ == "__main__":
    main()
