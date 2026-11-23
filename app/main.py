"""
FastAPI application para LoL Draft Analyzer.
Sirve la interfaz web y expone los endpoints de análisis y draft.
"""

import asyncio
import logging
import os
import sys
from pathlib import Path
from typing import Any, Optional

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from app.analyzer import PlayerAnalyzer
from app.data.counter_data import CHAMPION_TAGS
from app.lcu_client import LCUClient
from app.live_game import LiveGameMonitor
from app.match_cache import MatchCache
from app.riot_api import (
    PLATFORM_TO_ROUTING,
    REGION_DISPLAY_NAMES as REGION_NAMES,
    RiotAPIClient,
    RiotAPIError,
)

logger = logging.getLogger(__name__)

# ── Crear la app FastAPI ────────────────────────────────────────────

app = FastAPI(
    title="LoL Draft Analyzer",
    description="Analiza tu rendimiento y recibí recomendaciones de draft personalizadas",
    version="1.0.0",
)

# CORS para localhost
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8080", "http://127.0.0.1:8080"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Resolver directorio base (compatible con ejecución normal y PyInstaller .exe)
if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
    BASE_DIR = Path(sys._MEIPASS)
else:
    BASE_DIR = Path(__file__).resolve().parent.parent

# Montar archivos estáticos
static_dir = BASE_DIR / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")


# ── Modelos de request / response ──────────────────────────────────

class AnalyzeRequest(BaseModel):
    game_name: str
    tag_line: str
    region: str = "americas"
    platform: str = "la2"
    lang: str = "es"


class DraftRequest(BaseModel):
    player_analysis: dict[str, Any]
    ally_picks: list[str] = []
    enemy_picks: list[str] = []
    bans: list[str] = []
    role: str = "MID"
    lang: str = "es"


class ImportSetupRequest(BaseModel):
    champion: str
    keystone: str
    spells: list[str] = []


# ── Instancias globales ────────────────────────────────────────────

analyzer = PlayerAnalyzer()
lcu_client = LCUClient()
live_game_monitor = LiveGameMonitor()
match_cache = MatchCache()


def _get_api_key() -> str | None:
    """Obtiene la API key de las variables de entorno o del archivo .env."""
    for candidate in (BASE_DIR / ".env", Path.cwd() / ".env"):
        if candidate.exists():
            try:
                from dotenv import load_dotenv
                load_dotenv(candidate, override=True)
            except ImportError:
                pass
    key = os.environ.get("RIOT_API_KEY", "").strip()
    if not key or key == "tu-api-key-aqui":
        return None
    return key


def _get_cloud_url() -> str | None:
    """URL opcional del servidor central de NoFlash en la nube (para usuarios sin API key)."""
    url = os.environ.get("NoFlash_CLOUD_URL", "").strip().rstrip("/")
    return url or None


# ── Endpoints ──────────────────────────────────────────────────────

@app.get("/")
async def serve_index() -> FileResponse:
    """Sirve la página principal."""
    index_path = static_dir / "index.html"
    if not index_path.exists():
        raise HTTPException(
            status_code=404,
            detail="No se encontró index.html. Asegurate de tener la carpeta 'static/' con los archivos del frontend.",
        )
    return FileResponse(str(index_path))


@app.get("/api/regions")
async def get_regions() -> dict[str, Any]:
    """Retorna la lista de regiones/plataformas disponibles."""
    regions = []
    for platform, routing in PLATFORM_TO_ROUTING.items():
        regions.append({
            "platform": platform,
            "routing": routing,
            "display_name": REGION_NAMES.get(platform, platform),
        })
    return {"regions": regions}


@app.get("/api/champions")
async def get_champions() -> dict[str, Any]:
    """Retorna la lista de campeones con sus datos/tags."""
    champions = []
    for name, tags in CHAMPION_TAGS.items():
        if isinstance(tags, dict):
            champions.append({
                "name": name,
                "roles": tags.get("roles", []),
                "damage": tags.get("damage", "mixed"),
                "class": tags.get("class", []),
            })
    champions.sort(key=lambda c: c["name"])
    return {"champions": champions}


@app.post("/api/analyze")
async def analyze_player(request: AnalyzeRequest) -> dict[str, Any]:
    """
    Analiza a un jugador: busca su cuenta, descarga historial,
    maestrías y ranked, y retorna el análisis completo.
    """
    api_key = _get_api_key()
    cloud_url = _get_cloud_url()

    # Modo híbrido para usuarios finales: si no hay API key local pero sí servidor cloud, delegamos el análisis
    if not api_key and cloud_url:
        try:
            async with httpx.AsyncClient(timeout=60.0) as proxy:
                resp = await proxy.post(
                    f"{cloud_url}/api/analyze",
                    json=request.model_dump(),
                )
                if resp.status_code == 200:
                    return resp.json()
                detail = resp.json().get("detail", "Error del servidor NoFlash Cloud.")
                raise HTTPException(status_code=resp.status_code, detail=detail)
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(
                status_code=503,
                detail=f"No se pudo conectar con NoFlash Cloud ({cloud_url}): {e}",
            )

    if not api_key:
        raise HTTPException(
            status_code=503,
            detail=(
                "No se configuró la API Key de Riot Games. "
                "Configurá RIOT_API_KEY en .env o NoFlash_CLOUD_URL para usar el servidor en la nube."
            ),
        )

    client = RiotAPIClient(api_key)

    try:
        # 1. Obtener cuenta por Riot ID (derivamos routing siempre desde platform)
        platform = request.platform.lower()
        routing = PLATFORM_TO_ROUTING.get(platform, request.region.lower())
        if routing not in {"americas", "europe", "asia", "sea"}:
            routing = "americas"

        account = await client.get_account_by_riot_id(
            request.game_name, request.tag_line, routing
        )
        puuid = account["puuid"]

        # 2. Obtener datos del summoner
        summoner = await client.get_summoner_by_puuid(puuid, platform)
        summoner_id = summoner.get("id", "")

        # 3. Obtener historial de hasta 160 partidas (2 llamadas de IDs: 100 + 60)
        ids_part1, ids_part2 = await asyncio.gather(
            client.get_match_ids(puuid, routing, count=100, start=0),
            client.get_match_ids(puuid, routing, count=60, start=100),
        )
        match_ids = list(dict.fromkeys((ids_part1 or []) + (ids_part2 or [])))

        # 4. Consultar caché local primero (0ms para partidas ya descargadas)
        cached_matches = match_cache.get_many(match_ids)
        # Descargar máximo 80 partidas nuevas por vez para respetar 100 req / 2 min de Riot
        missing_ids = [mid for mid in match_ids if mid not in cached_matches][:80]

        # Descargar solo las partidas faltantes en tandas paralelas respetando 20 req/seg
        newly_fetched: dict[str, dict[str, Any]] = {}
        batch_size = 15
        for i in range(0, len(missing_ids), batch_size):
            batch = missing_ids[i : i + batch_size]

            async def _fetch_match(m_id: str) -> tuple[str, Optional[dict[str, Any]]]:
                try:
                    return m_id, await client.get_match_detail(m_id, routing)
                except RiotAPIError as e:
                    logger.warning(f"No se pudo obtener el match {m_id}: {e.mensaje}")
                    return m_id, None

            batch_results = await asyncio.gather(*[_fetch_match(mid) for mid in batch])
            for m_id, detail in batch_results:
                if detail is not None:
                    newly_fetched[m_id] = detail

            # Pequeña pausa entre tandas solo si quedan más por bajar (evita 429)
            if i + batch_size < len(missing_ids):
                await asyncio.sleep(1.05)

        if newly_fetched:
            match_cache.put_many(newly_fetched)

        # Reconstruir historial en orden cronológico (más reciente primero)
        match_history: list[dict[str, Any]] = []
        for mid in match_ids:
            detail = cached_matches.get(mid) or newly_fetched.get(mid)
            if detail is not None:
                match_history.append(detail)

        if not match_history:
            raise HTTPException(
                status_code=404,
                detail="No se encontraron partidas recientes para este jugador.",
            )

        # 5. Obtener maestrías
        try:
            masteries = await client.get_champion_masteries(puuid, platform)
        except RiotAPIError:
            masteries = []

        # 6. Obtener stats de ranked (priorizamos by-puuid que es el endpoint actual)
        ranked_stats: list[dict[str, Any]] = []
        try:
            ranked_stats = await client.get_ranked_stats_by_puuid(puuid, platform)
        except RiotAPIError:
            if summoner_id:
                try:
                    ranked_stats = await client.get_ranked_stats(summoner_id, platform)
                except RiotAPIError:
                    ranked_stats = []

        # 7. Analizar
        analysis = analyzer.analyze_player(
            match_history, masteries, ranked_stats, puuid, lang=request.lang
        )

        return {
            "success": True,
            "player": {
                "game_name": request.game_name,
                "tag_line": request.tag_line,
                "puuid": puuid,
                "summoner_level": summoner.get("summonerLevel", 0),
                "profile_icon_id": summoner.get("profileIconId", 0),
            },
            "analysis": analysis,
        }

    except RiotAPIError as e:
        raise HTTPException(
            status_code=e.status_code or 500,
            detail=e.mensaje,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Error inesperado durante el análisis")
        raise HTTPException(
            status_code=500,
            detail=f"Error inesperado: {str(e)}",
        )
    finally:
        await client.close()


@app.get("/api/lcu/status")
async def get_lcu_status() -> dict[str, Any]:
    """Detecta si el cliente de League of Legends está abierto en la PC."""
    return await lcu_client.get_status()


@app.get("/api/lcu/champ-select")
async def get_lcu_champ_select() -> dict[str, Any]:
    """Lee el estado actual de Selección de Campeones en vivo desde el cliente de LoL."""
    return await lcu_client.get_champ_select()


@app.get("/api/live-game")
async def get_live_game() -> dict[str, Any]:
    """Lee el estado oficial In-Game (127.0.0.1:2999) cuando hay una partida en curso."""
    return await live_game_monitor.get_live_state()


@app.post("/api/lcu/import-setup")
async def import_lcu_setup(request: ImportSetupRequest) -> dict[str, Any]:
    """Importa en 1 click las runas y hechizos recomendados directo al cliente de LoL."""
    return await lcu_client.import_setup(
        champion=request.champion,
        keystone=request.keystone,
        spells=request.spells,
    )


NEURAL_VOICES: dict[str, str] = {
    "es": "es-AR-ElenaNeural",
    "en": "en-US-AriaNeural",
    "pt": "pt-BR-FranciscaNeural",
    "ko": "ko-KR-SunHiNeural",
    "fr": "fr-FR-DeniseNeural",
    "de": "de-DE-KatjaNeural",
    "zh": "zh-CN-XiaoxiaoNeural",
    "ja": "ja-JP-NanamiNeural",
    "tr": "tr-TR-EmelNeural",
}


_TTS_CACHE: dict[tuple[str, str], bytes] = {}
_TTS_CACHE_MAX = 64


@app.get("/api/tts")
async def text_to_speech(text: str, lang: str = "es") -> Response:
    """Genera audio MP3 con voz neuronal natural (edge-tts) con caché en memoria."""
    clean_text = (text or "").strip()[:400]
    if not clean_text:
        raise HTTPException(status_code=400, detail="Texto vacío.")
    lang_key = (lang or "es").lower()
    cache_key = (lang_key, clean_text)
    if cache_key in _TTS_CACHE:
        return Response(content=_TTS_CACHE[cache_key], media_type="audio/mpeg")

    voice = NEURAL_VOICES.get(lang_key, "en-US-AriaNeural")
    try:
        import edge_tts

        communicate = edge_tts.Communicate(clean_text, voice=voice, rate="+4%")
        audio_chunks = bytearray()
        async for chunk in communicate.stream():
            if chunk.get("type") == "audio":
                audio_chunks.extend(chunk["data"])
        if not audio_chunks:
            raise HTTPException(status_code=502, detail="No se pudo generar audio.")
        audio_bytes = bytes(audio_chunks)
        if len(_TTS_CACHE) >= _TTS_CACHE_MAX:
            _TTS_CACHE.pop(next(iter(_TTS_CACHE)))
        _TTS_CACHE[cache_key] = audio_bytes
        return Response(content=audio_bytes, media_type="audio/mpeg")
    except HTTPException:
        raise
    except Exception as e:
        logger.warning(f"Error generando TTS: {e}")
        raise HTTPException(status_code=500, detail=f"Error TTS: {e}")


@app.post("/api/draft")
async def get_draft_recommendations(request: DraftRequest) -> dict[str, Any]:
    """
    Genera recomendaciones de draft basadas en el análisis del jugador
    y los picks actuales del draft.
    """
    if not request.player_analysis:
        raise HTTPException(
            status_code=400,
            detail="Se requiere el análisis del jugador. Primero usá /api/analyze.",
        )

    # Soportar tanto el objeto analysis directo como el wrapper completo
    analysis_data = (
        request.player_analysis.get("analysis", request.player_analysis)
        if isinstance(request.player_analysis, dict)
        else request.player_analysis
    )

    role_map = {
        "TOP": "TOP",
        "JUNGLE": "JG",
        "JG": "JG",
        "MIDDLE": "MID",
        "MID": "MID",
        "BOTTOM": "ADC",
        "ADC": "ADC",
        "UTILITY": "SUP",
        "SUP": "SUP",
    }
    normalized_role = role_map.get(request.role.upper(), request.role.upper())

    recommendations = analyzer.get_draft_recommendations(
        player_analysis=analysis_data,
        ally_picks=request.ally_picks,
        enemy_picks=request.enemy_picks,
        role=normalized_role,
        bans=request.bans,
        lang=request.lang,
    )

    coach = analyzer.get_coach_insights(
        player_analysis=analysis_data,
        ally_picks=request.ally_picks,
        enemy_picks=request.enemy_picks,
        role=normalized_role,
        bans=request.bans,
        lang=request.lang,
    )

    return {
        "success": True,
        "role": normalized_role,
        "ally_picks": request.ally_picks,
        "enemy_picks": request.enemy_picks,
        "recommendations": recommendations,
        "coach": coach,
        "message": (
            f"Se encontraron {len(recommendations)} recomendaciones para el rol {normalized_role}"
            if recommendations
            else f"No se encontraron campeones que cumplan los requisitos mínimos para {normalized_role}."
        ),
    }
