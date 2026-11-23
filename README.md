# RiftMind — Live LoL Coach

Aplicación de escritorio nativa para Windows (sin Overwolf) que analiza el historial real de un jugador de League of Legends, recomienda bans/picks/runas/hechizos en tiempo real durante el Draft, acompaña In-Game por voz neuronal y ofrece mini-juegos de Warm-Up para la cola.

## Cómo ejecutar
- **Doble click en `iniciar.bat`** (o `python desktop_app.py`).
- Requiere archivo `.env` en la raíz con `RIOT_API_KEY=RGAPI-...` (en modo desarrollo; en producción vivirá en un backend en la nube).

## Arquitectura del Proyecto
```text
lol-draft-analyzer/
├── desktop_app.py         # Ventana nativa Windows (pywebview + barra oscura + app.ico + Always-on-top Win32)
├── iniciar.bat            # Lanzador rápido (pythonw desktop_app.py)
├── run.py                 # Lanzador alternativo en navegador
├── requirements.txt       # fastapi, uvicorn, httpx, python-dotenv, pywebview, edge-tts
├── .env                   # RIOT_API_KEY (no subir a git)
├── app/
│   ├── main.py            # Servidor FastAPI (127.0.0.1:8080) + caché TTS + endpoints
│   ├── riot_api.py        # Cliente async de Riot API (Account v1, Summoner v4, Match v5, Mastery v4, League v4 by-puuid)
│   ├── match_cache.py     # Caché local SQLite (modo WAL, zlib) para analizar hasta 160 partidas en ~1.7s
│   ├── analyzer.py        # Motor de análisis (Bayesiano, Maestría, Coach Draft, Gameplan, Draft Diff, Anti-Tilt, Deep Dive por campeón, Némesis & Fun Facts, localización EN/ES)
│   ├── lcu_client.py      # Conexión local al cliente de LoL (LCU): auto-detección de cuenta, Champ Select en vivo e importación de Runas/Hechizos en 1 click
│   ├── live_game.py       # Monitor oficial In-Game (127.0.0.1:2999): objetivos, nivel 6 enemigo, armadura/MR, ventanas de gank/roam y cooldowns base
│   └── data/
│       └── counter_data.py # Counters, sinergias y tags de 95 campeones
└── static/
    ├── index.html         # SPA con 5 vistas: Búsqueda, Análisis, Draft, En Partida y Warm-Up
    ├── logo.jpg / app.ico # Logo oficial Hextech RM
    ├── css/style.css      # Estética Hextech oficial (Cinzel + Inter + paleta #010a13 / #c89b3c / #0ac8b9)
    └── js/
        ├── app.js         # Lógica principal, LCU live sync, Modo Smurf, Modal visual de campeón, In-Game timers
        ├── i18n.js        # Sistema multi-idioma (9 idiomas: ES, EN, PT, KO, FR, DE, ZH, JA, TR) con auto-detección OS
        ├── voice.js       # Coach por Voz neuronal vía /api/tts (edge-tts)
        └── riftdle.js     # Zona Warm-Up: Riftdle, Calentamiento Micro (20s), Quiz Macro/Builds y pop-up de cola
```

## Funcionalidades Implementadas
1. **Análisis Profundo (160 partidas cacheadas en SQLite + 30 Maestrías):**
   - Perfil con Splash Art del campeón principal e ícono real de invocador.
   - Pulso de Sesión (detector de racha / anti-tilt con mensajes amigables rotativos) + diagnóstico de errores recientes.
   - Análisis por Rol (arriba) + Champion Pool + **Modal visual por campeón** (4 barras Hextech + chips cortos de fortalezas/mejoras).
   - **Némesis, Víctima Favorita, Mejor Aliado y Fun Facts reales** (horas jugadas, millones de daño, Pentas/Quadras/Triples, mejor racha).
2. **Coach de Draft en Vivo (LCU):**
   - Detecta el cliente de LoL y salta automáticamente a Draft al entrar a Champ Select.
   - **Draft Diff + Semáforo de Dodge**, qué banear, cuándo pickear/swap, alertas de comp + mensaje copiable al chat, Plan de Partida (Win Condition, Early, Teamfights, Items).
   - Top 5 picks con Tier (`S+/S/A/B`), íconos oficiales de Hechizos y Runas, y botón **Importar Runas y Hechizos al LoL**.
   - **Modo Smurf:** podés elegir otra cuenta (tu main) sin que el LoL logueado en una smurf la pise.
3. **Coach por Voz Neuronal (`edge-tts`) + Monitor In-Game (`127.0.0.1:2999`):**
   - Voces neuronales reales (`es-AR-ElenaNeural`, `en-US-AriaNeural`, etc.) con caché en memoria.
   - Avisos hablados de Dragón/Grubs/Heraldo/Barón, ventanas de gank/roam, nivel 6 enemigo, armadura/MR y tracker manual legal de hechizos enemigos.
4. **Zona Warm-Up para la Cola:**
   - **Riftdle** (estilo LoLdle), **Calentamiento Micro (20s)**, **Quiz de Macro & Builds** y pop-up discreto tras 45s de inactividad.

## Estrategia de Producto y Próximos Pasos
- **Mercado foco:** Global-first (**NA / EUW** en inglés para suscripciones Pro de $4.99–$6.99/mes vía Lemon Squeezy/Paddle), manteniendo soporte completo para **LATAM / BR**.
- **Siguientes hitos técnicos:**
  1. Empaquetar como instalador `.exe` (PyInstaller / Electron).
  2. Subir el backend de Riot API a la nube con una **Production API Key** de Riot para que los usuarios finales no necesiten API Key.
  3. Crear landing page (`riftmind.gg`) y lanzar beta usando el kit de redes (`@riftmindgg`).
