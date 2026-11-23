"""
Entry point para LoL Draft Analyzer.
Lee la API key, configura el entorno y levanta el servidor.
"""

import os
import sys
import webbrowser
from pathlib import Path

# Cargar variables de entorno desde .env si existe
try:
    from dotenv import load_dotenv

    env_path = Path(__file__).resolve().parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    pass  # python-dotenv no instalado, se usa solo env vars del sistema


def main() -> None:
    """Función principal: valida config e inicia el servidor."""
    # Banner
    print()
    print("=" * 56)
    print("  🎮  LoL Draft Analyzer  🎮")
    print("  Analizá tu rendimiento y mejorá tu draft")
    print("=" * 56)
    print()

    # Verificar API Key
    api_key = os.environ.get("RIOT_API_KEY")
    if not api_key or api_key == "tu-api-key-aqui":
        print("⚠️  No se encontró una API Key de Riot Games válida.")
        print()
        print("Para usar esta aplicación necesitás una API Key:")
        print("  1. Andá a https://developer.riotgames.com/")
        print("  2. Iniciá sesión con tu cuenta de Riot")
        print("  3. En el Dashboard, copiá tu Development API Key")
        print("  4. Creá un archivo .env en esta carpeta con:")
        print("     RIOT_API_KEY=RGAPI-tu-clave-aqui")
        print()
        print("  O configurá la variable de entorno:")
        print('     set RIOT_API_KEY=RGAPI-tu-clave-aqui  (Windows)')
        print('     export RIOT_API_KEY=RGAPI-tu-clave-aqui  (Linux/Mac)')
        print()
        print("⚠️  La app se va a iniciar igual pero no vas a poder")
        print("    analizar jugadores hasta que configures la key.")
        print()
    else:
        print(f"✅ API Key configurada: {api_key[:10]}...{api_key[-4:]}")
        print()

    # Verificar que la carpeta static existe
    static_dir = Path(__file__).resolve().parent / "static"
    if not static_dir.exists():
        print("⚠️  No se encontró la carpeta 'static/'.")
        print("    La interfaz web no va a estar disponible hasta")
        print("    que se creen los archivos del frontend.")
        print()

    host = "127.0.0.1"
    port = 8080
    url = f"http://{host}:{port}"

    print(f"🚀 Iniciando servidor en {url}")
    print(f"   Presioná Ctrl+C para detener")
    print()

    # Abrir el navegador después de un breve delay
    import threading

    def open_browser() -> None:
        import time
        time.sleep(1.5)
        webbrowser.open(url)

    threading.Thread(target=open_browser, daemon=True).start()

    # Iniciar uvicorn
    try:
        import uvicorn

        uvicorn.run(
            "app.main:app",
            host=host,
            port=port,
            reload=False,
            log_level="info",
        )
    except ImportError:
        print("❌ Error: uvicorn no está instalado.")
        print("   Ejecutá: pip install -r requirements.txt")
        sys.exit(1)
    except KeyboardInterrupt:
        print()
        print("👋 ¡Chau! Servidor detenido.")


if __name__ == "__main__":
    main()
