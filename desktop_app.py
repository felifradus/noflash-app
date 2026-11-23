"""
Lanzador nativo de escritorio para LoL Draft Analyzer.
Corre el servidor FastAPI en segundo plano y abre la app en su propia ventana
nativa de Windows (sin navegador ni barra de direcciones), con modo 'Siempre encima'.
"""

import ctypes
import os
import socket
import subprocess
import sys
import threading
import time
from pathlib import Path

try:
    import winreg
except ImportError:
    winreg = None

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
RUN_REG_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"
RUN_REG_NAME = "NoFlashAutoLaunch"
SW_MINIMIZE = 6
SW_MAXIMIZE = 3
SW_RESTORE = 9
WM_CLOSE = 0x0010
CREATE_NO_WINDOW = 0x08000000
DETACHED_PROCESS = 0x00000008


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


def _build_launch_args(watch_lol: bool = False) -> list[str]:
    """Construye el comando para lanzar NoFlash (soporta .exe congelado o Python source)."""
    if getattr(sys, "frozen", False):
        cmd = [sys.executable]
    else:
        py_exe = Path(sys.executable)
        pythonw = py_exe.with_name("pythonw.exe")
        exe = str(pythonw if pythonw.exists() else py_exe)
        cmd = [exe, str(Path(__file__).resolve())]
    if watch_lol:
        cmd.append("--watch-lol")
    return cmd


def is_auto_launch_enabled() -> bool:
    """Devuelve True si el watcher automático al abrir LoL está registrado en Windows."""
    if winreg is None:
        return False
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_REG_PATH, 0, winreg.KEY_READ) as key:
            winreg.QueryValueEx(key, RUN_REG_NAME)
            return True
    except OSError:
        return False


def set_auto_launch_enabled(enable: bool) -> bool:
    """Activa o desactiva el inicio automático de NoFlash al abrir League of Legends."""
    if winreg is None:
        return False
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_REG_PATH, 0, winreg.KEY_SET_VALUE) as key:
            if enable:
                args = _build_launch_args(watch_lol=True)
                cmd_str = " ".join(f'"{a}"' if " " in a else a for a in args)
                winreg.SetValueEx(key, RUN_REG_NAME, 0, winreg.REG_SZ, cmd_str)
            else:
                try:
                    winreg.DeleteValue(key, RUN_REG_NAME)
                except FileNotFoundError:
                    pass
    except OSError:
        return False

    if enable:
        # Lanzar el watcher silencioso ahora mismo (el mutex evita duplicados)
        try:
            subprocess.Popen(
                _build_launch_args(watch_lol=True),
                creationflags=CREATE_NO_WINDOW | DETACHED_PROCESS,
                close_fds=True,
            )
        except Exception:
            pass
    return is_auto_launch_enabled()


def _is_lol_client_running(check_tasklist: bool = False) -> bool:
    """Detecta si el cliente de League of Legends está abierto (0% CPU vía lockfile)."""
    for drive in ("C", "D", "E", "F"):
        if os.path.exists(f"{drive}:\\Riot Games\\League of Legends\\lockfile"):
            return True
    if check_tasklist:
        try:
            out = subprocess.check_output(
                ["tasklist", "/FI", "IMAGENAME eq LeagueClientUx.exe", "/NH"],
                creationflags=CREATE_NO_WINDOW,
                timeout=3,
            )
            return b"LeagueClientUx.exe" in out
        except Exception:
            return False
    return False


def run_lol_watcher() -> None:
    """
    Modo silencioso (--watch-lol): espera en segundo plano (~5 MB RAM, 0% CPU)
    y abre NoFlash automáticamente apenas se inicia League of Legends.
    """
    # Mutex de instancia única para no duplicar watchers
    kernel32 = ctypes.windll.kernel32
    _mutex = kernel32.CreateMutexW(None, False, "Local\\NoFlashLolWatcherMutex")
    if kernel32.GetLastError() == 183:  # ERROR_ALREADY_EXISTS
        return

    user32 = ctypes.windll.user32
    was_running = _is_lol_client_running(check_tasklist=True)
    tick = 0

    while True:
        time.sleep(4)
        tick += 1

        # Si el usuario desactivó Auto-LoL desde la app, salir limpiamente
        if tick % 3 == 0 and not is_auto_launch_enabled():
            return

        is_running = _is_lol_client_running(check_tasklist=(tick % 2 == 0))
        if is_running and not was_running:
            # LoL acaba de abrirse -> abrir NoFlash si no está abierto ya
            hwnd = user32.FindWindowW(None, WINDOW_TITLE)
            if not hwnd:
                try:
                    subprocess.Popen(
                        _build_launch_args(watch_lol=False),
                        creationflags=DETACHED_PROCESS,
                        close_fds=True,
                    )
                except Exception:
                    pass
        was_running = is_running


class DesktopAPI:
    """Funciones nativas expuestas al frontend cuando corre como app de escritorio."""

    def __init__(self) -> None:
        self._window = None
        self._on_top = False

    def set_window(self, window) -> None:
        self._window = window

    def get_auto_launch(self) -> bool:
        return is_auto_launch_enabled()

    def toggle_auto_launch(self) -> bool:
        return set_auto_launch_enabled(not is_auto_launch_enabled())

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

    def win_minimize(self) -> None:
        """Minimiza la ventana nativa sin bloquear WebView2."""
        def _do() -> None:
            hwnd = ctypes.windll.user32.FindWindowW(None, WINDOW_TITLE)
            if hwnd:
                ctypes.windll.user32.ShowWindow(hwnd, SW_MINIMIZE)
        threading.Thread(target=_do, daemon=True).start()

    def win_toggle_maximize(self) -> bool:
        """Alterna Maximizar / Restaurar la ventana nativa."""
        self._maximized = not getattr(self, "_maximized", False)
        target_max = self._maximized

        def _do() -> None:
            hwnd = ctypes.windll.user32.FindWindowW(None, WINDOW_TITLE)
            if hwnd:
                ctypes.windll.user32.ShowWindow(hwnd, SW_MAXIMIZE if target_max else SW_RESTORE)
        threading.Thread(target=_do, daemon=True).start()
        return target_max

    def win_close(self) -> None:
        """Cierra la ventana nativa limpiamente."""
        def _do() -> None:
            hwnd = ctypes.windll.user32.FindWindowW(None, WINDOW_TITLE)
            if hwnd:
                ctypes.windll.user32.PostMessageW(hwnd, WM_CLOSE, 0, 0)
        threading.Thread(target=_do, daemon=True).start()


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

    # 2. Crear ventana nativa frameless (barra Hextech gamer propia)
    api = DesktopAPI()
    window = webview.create_window(
        title=WINDOW_TITLE,
        url=url,
        js_api=api,
        width=1220,
        height=820,
        min_size=(840, 600),
        background_color="#010a13",
        resizable=True,
        frameless=True,
        easy_drag=False,
    )
    api.set_window(window)

    # Aplicar barra oscura + ícono Hextech apenas aparezca la ventana
    threading.Thread(target=_apply_native_windows_theme, daemon=True).start()

    # Iniciar loop gráfico nativo (Edge WebView2 en Windows)
    webview.start()


if __name__ == "__main__":
    if "--watch-lol" in sys.argv:
        run_lol_watcher()
    else:
        main()
