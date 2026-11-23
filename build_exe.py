"""
Script de compilación para generar RiftMind.exe (standalone para Windows)
usando PyInstaller. Incluye todos los archivos estáticos, ícono Hextech y módulos.
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def main() -> None:
    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--noconfirm",
        "--onefile",
        "--windowed",
        "--name",
        "RiftMind",
        "--icon",
        str(ROOT / "static" / "app.ico"),
        "--add-data",
        f"{ROOT / 'static'};static",
        "--add-data",
        f"{ROOT / 'app' / 'data'};app/data",
        "--hidden-import",
        "uvicorn.logging",
        "--hidden-import",
        "uvicorn.loops",
        "--hidden-import",
        "uvicorn.loops.auto",
        "--hidden-import",
        "uvicorn.protocols",
        "--hidden-import",
        "uvicorn.protocols.http",
        "--hidden-import",
        "uvicorn.protocols.http.auto",
        "--hidden-import",
        "uvicorn.protocols.websockets",
        "--hidden-import",
        "uvicorn.protocols.websockets.auto",
        "--hidden-import",
        "uvicorn.lifespan",
        "--hidden-import",
        "uvicorn.lifespan.on",
        "--hidden-import",
        "edge_tts",
        "--hidden-import",
        "webview",
        str(ROOT / "desktop_app.py"),
    ]
    print("Compilando RiftMind.exe...")
    subprocess.run(cmd, cwd=str(ROOT), check=True)
    exe_path = ROOT / "dist" / "RiftMind.exe"
    if exe_path.exists():
        size_mb = exe_path.stat().st_size / (1024 * 1024)
        print(f"OK! Generado: {exe_path} ({size_mb:.1f} MB)")


if __name__ == "__main__":
    main()
