import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
EXE_NAME = "MemeStudio"


def main() -> int:
    pyinstaller = shutil.which("pyinstaller")
    command = [
        pyinstaller or sys.executable,
        *(["-m", "PyInstaller"] if pyinstaller is None else []),
        "--noconfirm",
        "--clean",
        "--onefile",
        "--name",
        EXE_NAME,
        "--distpath",
        str(ROOT / "dist"),
        "--workpath",
        str(ROOT / "build" / "meme_studio"),
        "--specpath",
        str(ROOT / "build" / "meme_studio"),
        "--add-data",
        f"{ROOT / 'tools' / 'meme_studio' / 'web'};tools/meme_studio/web",
        str(ROOT / "meme_studio_launcher.py"),
    ]
    result = subprocess.run(command, cwd=str(ROOT))
    if result.returncode != 0:
        return result.returncode

    exe_path = ROOT / "dist" / f"{EXE_NAME}.exe"
    print(f"EXE 已生成: {exe_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
