"""
Lanzador nativo de escritorio para LoL Draft Analyzer.
Corre el servidor FastAPI en segundo plano y abre la app en su propia ventana
nativa de Windows (sin navegador ni barra de direcciones), con modo 'Siempre encima'.
"""

import ctypes
import os
import socket
import sys
import threading
import time
from pathlib import Path

# Constantes Win32 para "Siempre encima", Barra Oscura e Ícono nativo
HWND_TOPMOST = -1
HWND_NOTOPMOST = -2
SWP_NOMOVE = 0x0002
SWP_NOSIZE = 0x0001
SWP_NOACTIVATE = 0x0010
DWMWA_USE_IMMERSIVE_DARK_MODE = 20
WM_SETICON = 0x0080
ICON_SMALL = 0
ICON_BIG = 1
IMAGE_ICON = 1
LR_LOADFROMFILE = 0x0010
WINDOW_TITLE = "NoFlash — Live LoL Coach"


def _resource_dir() -> Path:
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS)
    return Path(__file__).resolve().parent


def _apply_native_windows_theme() -> None:
    """Aplica barra de título oscura de Windows 10/11 e ícono Hextech a la ventana."""
    icon_path = str(_resource_dir() / "static" / "app.ico")
    user32 = ctypes.windll.user32
    dwmapi = ctypes.windll.dwmapi

    # Esperar hasta que la ventana exista (máx 5s)
    hwnd = 0
    for _ in range(50):
        hwnd = user32.FindWindowW(None, WINDOW_TITLE)
        if hwnd:
            break
        time.sleep(0.1)

    if not hwnd:
        return

    # 1. Activar barra de título oscura nativa de Windows
    try:
        dark_mode = ctypes.c_int(1)
        dwmapi.DwmSetWindowAttribute(
            hwnd,
            DWMWA_USE_IMMERSIVE_DARK_MODE,
            ctypes.byref(dark_mode),
            ctypes.sizeof(dark_mode),
        )
    except Exception:
        pass

    # 2. Reemplazar el ícono de Python por nuestro ícono Hextech
    try:
        if Path(icon_path).exists():
            hicon = user32.LoadImageW(
                0, icon_path, IMAGE_ICON, 0, 0, LR_LOADFROMFILE
            )
            if hicon:
                user32.SendMessageW(hwnd, WM_SETICON, ICON_SMALL, hicon)
                user32.SendMessageW(hwnd, WM_SETICON, ICON_BIG, hicon)
    except Exception:
        pass

# Cargar .env si existe
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).resolve().parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    pass


class DesktopAPI:
    """Funciones nativas expuestas al frontend cuando corre como app de escritorio."""

    def __init__(self) -> None:
        self._window = None
        self._on_top = False

    def set_window(self, window) -> None:
        self._window = window

    def toggle_on_top(self) -> bool:
        """Alterna el modo 'Siempre encima' usando Win32 SetWindowPos (sin deadlock)."""
        self._on_top = not self._on_top
        target_state = self._on_top

        def _apply() -> None:
            try:
                user32 = ctypes.windll.user32
                hwnd = user32.FindWindowW(None, WINDOW_TITLE)
                if hwnd:
                    flag = HWND_TOPMOST if target_state else HWND_NOTOPMOST
                    user32.SetWindowPos(
                        hwnd,
                        flag,
                        0,
                        0,
                        0,
                        0,
                        SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE,
                    )
            except Exception:
                pass

        threading.Thread(target=_apply, daemon=True).start()
        return self._on_top


def _is_port_in_use(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex((host, port)) == 0


def _start_backend(host: str, port: int) -> None:
    """Inicia el backend FastAPI en un thread daemon si el puerto está libre."""
    if _is_port_in_use(host, port):
        return  # Ya está corriendo en segundo plano

    import uvicorn
    from app.main import app as fastapi_app

    uvicorn.run(
        fastapi_app,
        host=host,
        port=port,
        reload=False,
        log_level="warning",
    )


def main() -> None:
    import webview

    # Identificador propio en la barra de tareas de Windows (no agrupar como Python)
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(
            "NoFlash.Desktop.1"
        )
    except Exception:
        pass

    host = "127.0.0.1"
    port = 8080
    url = f"http://{host}:{port}"

    # 1. Levantar backend en segundo plano si no está corriendo
    server_thread = threading.Thread(
        target=_start_backend, args=(host, port), daemon=True
    )
    server_thread.start()

    # Esperar hasta que el servidor esté listo (máx 6 seg)
    for _ in range(30):
        if _is_port_in_use(host, port):
            break
        time.sleep(0.2)

    # 2. Crear ventana nativa de escritorio
    api = DesktopAPI()
    window = webview.create_window(
        title=WINDOW_TITLE,
        url=url,
        js_api=api,
        width=1220,
        height=820,
        min_size=(900, 620),
        background_color="#0a0a1a",
        resizable=True,
    )
    api.set_window(window)

    # Aplicar barra oscura + ícono Hextech apenas aparezca la ventana
    threading.Thread(target=_apply_native_windows_theme, daemon=True).start()

    # Iniciar loop gráfico nativo (Edge WebView2 en Windows)
    webview.start()


if __name__ == "__main__":
    main()
