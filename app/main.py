"""
FastAPI application para LoL Draft Analyzer.
Sirve la interfaz web y expone los endpoints de análisis y draft.
"""

import asyncio
import logging
import os
import re
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
    candidates = [BASE_DIR / ".env", Path.cwd() / ".env"]
    if getattr(sys, "frozen", False):
        candidates.insert(0, Path(sys.executable).resolve().parent / ".env")
    for candidate in candidates:
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
    """Retorna la lista limpia y deduplicada de todos los campeones oficiales (Data Dragon IDs)."""
    alias_to_dd = {"wukong": "MonkeyKing", "nunuwillump": "Nunu", "renataglasc": "Renata"}
    seen: dict[str, dict[str, Any]] = {}

    for name, tags in CHAMPION_TAGS.items():
        if not isinstance(tags, dict):
            continue
        norm = re.sub(r"[^a-z0-9]", "", name.lower())
        norm = alias_to_dd.get(norm, norm).lower()
        is_clean_dd = bool(re.fullmatch(r"[A-Za-z0-9]+", name)) and name.lower() != "wukong"

        entry = {
            "name": name,
            "roles": tags.get("roles", []),
            "damage": tags.get("damage", "mixed"),
            "class": tags.get("class", []),
        }
        # Preferir siempre la clave limpia oficial de Data Dragon (sin espacios ni apóstrofes)
        if norm not in seen or (is_clean_dd and not re.fullmatch(r"[A-Za-z0-9]+", seen[norm]["name"])):
            seen[norm] = entry

    champions = sorted(seen.values(), key=lambda c: c["name"])
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
async def get_live_game(lang: str = "es") -> dict[str, Any]:
    """Lee el estado oficial In-Game (127.0.0.1:2999) cuando hay una partida en curso."""
    return await live_game_monitor.get_live_state(lang=lang)


class LiveScoutPlayer(BaseModel):
    game_name: str = ""
    tag_line: str = ""
    champion: str = ""
    team_side: str = "enemy"  # "ally" | "enemy"
    position: str = ""
    is_me: bool = False


class LiveScoutRequest(BaseModel):
    platform: str = "la2"
    lang: str = "es"
    players: list[LiveScoutPlayer] = Field(default_factory=list)


_SCOUT_CACHE: dict[str, dict[str, Any]] = {}
_TIER_SCORE = {
    "IRON": 1, "BRONZE": 2, "SILVER": 3, "GOLD": 4,
    "PLATINUM": 5, "EMERALD": 6, "DIAMOND": 7,
    "MASTER": 8, "GRANDMASTER": 9, "CHALLENGER": 10,
}


@app.post("/api/live-scout")
async def live_scout_match(request: LiveScoutRequest) -> dict[str, Any]:
    """
    Scouting en vivo de los 10 jugadores (aliados y rivales) una vez iniciada la partida.
    Usa solo APIs oficiales de Riot (Account v1, League v4 by-puuid, Mastery v4).
    """
    if not request.players:
        return {"success": False, "allies": [], "enemies": [], "summary": {}}

    platform = (request.platform or "la2").lower()
    if platform not in PLATFORM_TO_ROUTING:
        platform = "la2"
    routing = PLATFORM_TO_ROUTING[platform]
    is_en = (request.lang or "es").lower() != "es"

    sig = f"{platform}:{request.lang}:" + "|".join(
        sorted(f"{p.team_side}:{p.game_name}#{p.tag_line}:{p.champion}" for p in request.players)
    )
    if sig in _SCOUT_CACHE:
        return _SCOUT_CACHE[sig]

    api_key = _get_api_key()
    if not api_key:
        raise HTTPException(status_code=503, detail="RIOT_API_KEY no configurada.")

    # Mapa normalizado nombre campeón -> championId para buscar maestría exacta
    from app.data.counter_data import CHAMPION_ID_TO_NAME
    norm_name_to_id: dict[str, int] = {}
    for cid, cname in CHAMPION_ID_TO_NAME.items():
        clean = "".join(ch for ch in cname.lower() if ch.isalnum())
        norm_name_to_id[clean] = cid

    sem = asyncio.Semaphore(5)

    async def _scout_one(client: RiotAPIClient, p: LiveScoutPlayer) -> dict[str, Any]:
        base = {
            "game_name": p.game_name,
            "tag_line": p.tag_line,
            "champion": p.champion,
            "team_side": p.team_side,
            "position": p.position,
            "is_me": p.is_me,
            "tier": "UNRANKED",
            "rank": "",
            "lp": 0,
            "wins": 0,
            "losses": 0,
            "games": 0,
            "win_rate": None,
            "hot_streak": False,
            "mastery_level": 0,
            "mastery_points": 0,
            "tags": [],
            "threat_score": 0.0,
        }
        if not p.game_name or not p.tag_line:
            return base

        async with sem:
            try:
                acc = await client.get_account_by_riot_id(p.game_name, p.tag_line, routing)
                puuid = acc.get("puuid", "")
                if not puuid:
                    return base

                ranked_task = client.get_ranked_stats_by_puuid(puuid, platform)
                mastery_task = client.get_champion_masteries(puuid, platform)
                ranked_res, mastery_res = await asyncio.gather(
                    ranked_task, mastery_task, return_exceptions=True
                )

                # SoloQ stats
                if isinstance(ranked_res, list):
                    solo = next(
                        (e for e in ranked_res if e.get("queueType") == "RANKED_SOLO_5x5"),
                        ranked_res[0] if ranked_res else None,
                    )
                    if solo:
                        wins = int(solo.get("wins", 0))
                        losses = int(solo.get("losses", 0))
                        games = wins + losses
                        wr = round((wins / games) * 100, 1) if games > 0 else None
                        base.update({
                            "tier": solo.get("tier", "UNRANKED"),
                            "rank": solo.get("rank", ""),
                            "lp": int(solo.get("leaguePoints", 0)),
                            "wins": wins,
                            "losses": losses,
                            "games": games,
                            "win_rate": wr,
                            "hot_streak": bool(solo.get("hotStreak", False)),
                        })

                # Maestría en el campeón actual
                champ_norm = "".join(ch for ch in (p.champion or "").lower() if ch.isalnum())
                champ_id = norm_name_to_id.get(champ_norm)
                if isinstance(mastery_res, list) and champ_id is not None:
                    m_entry = next(
                        (m for m in mastery_res if m.get("championId") == champ_id),
                        None,
                    )
                    if m_entry:
                        base["mastery_level"] = int(m_entry.get("championLevel", 0))
                        base["mastery_points"] = int(m_entry.get("championPoints", 0))

                # Generar tags tácticos inteligentes
                tags: list[dict[str, str]] = []
                pts = base["mastery_points"]
                wr = base["win_rate"]
                games = base["games"]
                tier_val = _TIER_SCORE.get(base["tier"], 0)

                if pts >= 150000 or base["mastery_level"] >= 10:
                    tags.append({"cls": "gold", "text": "🔥 OTP / Main"})
                elif pts < 5000 and base["mastery_level"] <= 3:
                    tags.append({"cls": "warn", "text": "🆕 First Time" if is_en else "🆕 Poca práctica"})

                if base["hot_streak"]:
                    tags.append({"cls": "good", "text": "🔥 Hot Streak" if is_en else "🔥 En racha"})

                if wr is not None and games >= 15:
                    if wr >= 55.0:
                        tags.append({"cls": "good", "text": f"📈 {wr}% WR"})
                    elif wr <= 46.0:
                        tags.append({"cls": "bad", "text": f"❄️ {'Tilt Target' if is_en else 'Campable'} ({wr}%)"})

                base["tags"] = tags[:3]
                # Score de peligro para identificar amenaza #1 y target #1
                wr_factor = ((wr or 50.0) - 50.0) * 0.8
                mastery_factor = min(20.0, pts / 15000.0)
                base["threat_score"] = round(
                    tier_val * 10.0 + wr_factor + mastery_factor + (6.0 if base["hot_streak"] else 0.0),
                    1,
                )
            except Exception as exc:
                logger.debug(f"Live scout skip {p.game_name}#{p.tag_line}: {exc}")
        return base

    async with RiotAPIClient(api_key) as client:
        scouted = await asyncio.gather(*[_scout_one(client, p) for p in request.players])

    allies = [p for p in scouted if p["team_side"] == "ally"]
    enemies = [p for p in scouted if p["team_side"] == "enemy"]

    def _avg_wr(group: list[dict[str, Any]]) -> float | None:
        vals = [x["win_rate"] for x in group if x["win_rate"] is not None]
        return round(sum(vals) / len(vals), 1) if vals else None

    key_threat = max(enemies, key=lambda x: x["threat_score"]) if enemies else None
    camp_target = min(enemies, key=lambda x: x["threat_score"]) if len(enemies) > 1 else None

    voice_summary = ""
    if key_threat and camp_target and key_threat["champion"] != camp_target["champion"]:
        if is_en:
            voice_summary = (
                f"Match scout ready. Watch out for enemy {key_threat['champion']} "
                f"and look to punish {camp_target['champion']}."
            )
        else:
            voice_summary = (
                f"Análisis de partida listo. Ojo con {key_threat['champion']} rival, "
                f"y buscá castigar a {camp_target['champion']}."
            )

    result = {
        "success": True,
        "allies": allies,
        "enemies": enemies,
        "summary": {
            "ally_avg_wr": _avg_wr(allies),
            "enemy_avg_wr": _avg_wr(enemies),
            "key_threat": key_threat,
            "camp_target": camp_target,
            "voice_summary": voice_summary,
        },
    }
    if len(_SCOUT_CACHE) >= 12:
        _SCOUT_CACHE.pop(next(iter(_SCOUT_CACHE)))
    _SCOUT_CACHE[sig] = result
    return result


@app.post("/api/lcu/import-setup")
async def import_lcu_setup(request: ImportSetupRequest) -> dict[str, Any]:
    """Importa en 1 click las runas y hechizos recomendados directo al cliente de LoL."""
    return await lcu_client.import_setup(
        champion=request.champion,
        keystone=request.keystone,
        spells=request.spells,
    )


import re as _re

NEURAL_VOICES: dict[str, str] = {
    "es": "en-US-AvaMultilingualNeural",
    "en": "en-US-AvaMultilingualNeural",
    "pt": "pt-BR-FranciscaNeural",
    "ko": "ko-KR-SunHiNeural",
    "fr": "fr-FR-DeniseNeural",
    "de": "de-DE-KatjaNeural",
    "zh": "zh-CN-XiaoxiaoNeural",
    "ja": "ja-JP-NanamiNeural",
    "tr": "tr-TR-EmelNeural",
}

# Perfiles de voz humana HD (Multilingual Neural, sin distorsión de pitch)
VOICE_PERSONAS: dict[str, dict[str, Any]] = {
    "pro_f": {
        "es": "en-US-AvaMultilingualNeural",
        "en": "en-US-AvaMultilingualNeural",
        "rate": "+0%",
        "pitch": "+0Hz",
    },
    "pro_m": {
        "es": "en-US-AndrewMultilingualNeural",
        "en": "en-US-AndrewMultilingualNeural",
        "rate": "+0%",
        "pitch": "+0Hz",
    },
}

_TTS_CHAMP_FIXES: dict[str, str] = {
    "NoFlash": "No Flash",
    "noflash": "No Flash",
    "LeeSin": "Lee Sin",
    "TwistedFate": "Twisted Fate",
    "AurelionSol": "Aurelion Sol",
    "MasterYi": "Master Yi",
    "MissFortune": "Miss Fortune",
    "JarvanIV": "Jarvan Four",
    "KhaZix": "Kha'Zix",
    "TahmKench": "Tahm Kench",
    "XinZhao": "Xin Zhao",
    "DrMundo": "Doctor Mundo",
    "Chogath": "Cho'Gath",
    "Belveth": "Bel'Veth",
    "KogMaw": "Kog'Maw",
    "RekSai": "Rek'Sai",
    "Velkoz": "Vel'Koz",
    "Kaisa": "Kai'Sa",
    "KSante": "K'Sante",
    "Renata": "Renata Glasc",
    "MonkeyKing": "Wukong",
}


def _polish_tts_text(text: str, lang_key: str) -> str:
    """Pule pronunciación de marca, campeones y siglas de LoL para que suene 100% natural."""
    out = (text or "").strip()[:400]
    for src, dst in _TTS_CHAMP_FIXES.items():
        out = _re.sub(rf"\b{_re.escape(src)}\b", dst, out, flags=_re.IGNORECASE)
    if lang_key == "es":
        out = _re.sub(r"\bsu R\b", "su ulti", out)
        out = _re.sub(r"\bWR\b", "win rate", out)
        out = _re.sub(r"\bHP\b", "vida", out)
    else:
        out = _re.sub(r"\bWR\b", "win rate", out)
    # Quitar emojis/símbolos que cortan el ritmo natural
    out = _re.sub(r"[^\w\s.,!?¡¿áéíóúÁÉÍÓÚñÑüÜ'%-]", " ", out)
    out = _re.sub(r"\s+", " ", out).strip()
    return out


_TTS_CACHE: dict[tuple[str, str, str], bytes] = {}
_TTS_CACHE_MAX = 96


@app.get("/api/tts")
async def text_to_speech(text: str, lang: str = "es", persona: str = "pro_f") -> Response:
    """Genera audio MP3 con voz neuronal ultra-humana (edge-tts) + selector de personaje."""
    lang_key = (lang or "es").lower()
    clean_text = _polish_tts_text(text, lang_key)
    if not clean_text:
        raise HTTPException(status_code=400, detail="Texto vacío.")
    persona_key = (persona or "pro_f").lower()
    if persona_key not in VOICE_PERSONAS:
        persona_key = "pro_f"

    cache_key = (lang_key, persona_key, clean_text)
    if cache_key in _TTS_CACHE:
        return Response(content=_TTS_CACHE[cache_key], media_type="audio/mpeg")

    cfg = VOICE_PERSONAS[persona_key]
    voice = cfg.get(lang_key) or (cfg["en"] if lang_key != "es" and persona_key != "pro_f" else NEURAL_VOICES.get(lang_key, "en-US-AvaMultilingualNeural"))
    rate = cfg.get("rate", "+0%")
    pitch = cfg.get("pitch", "+0Hz")
    try:
        import edge_tts

        communicate = edge_tts.Communicate(clean_text, voice=voice, rate=rate, pitch=pitch)
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
