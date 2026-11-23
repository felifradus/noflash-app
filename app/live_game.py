"""
Monitor In-Game oficial de League of Legends (Live Client Data API).
Se conecta a https://127.0.0.1:2999/liveclientdata/allgamedata (100% permitido por Riot,
no lee memoria del juego ni requiere API key) para dar consejos tácticos en tiempo real.
"""

import logging
from typing import Any

import httpx

logger = logging.getLogger(__name__)

LIVE_CLIENT_URL = "https://127.0.0.1:2999/liveclientdata/allgamedata"

# Cooldowns base oficiales en segundos (para timer manual 100% legal)
SPELL_BASE_COOLDOWNS: dict[str, int] = {
    "flash": 300,
    "destello": 300,
    "teleport": 300,
    "teleportación": 300,
    "heal": 240,
    "curar": 240,
    "exhaust": 210,
    "extenuar": 210,
    "cleanse": 210,
    "limpiar": 210,
    "ghost": 210,
    "fantasmal": 210,
    "barrier": 180,
    "barrera": 180,
    "ignite": 180,
    "prender": 180,
    "smite": 90,
    "aplastar": 90,
}

# IDs de ítems defensivos comunes para detectar si el rival está stackeando armadura o MR
ARMOR_KEYWORDS = ("plate", "mail", "randuin", "frozen", "zhonya", "death's dance", "thornmail", "guardian", "steelcaps", "armadura", "cota", "coraza")
MR_KEYWORDS = ("maw", "wit's end", "force of nature", "spirit visage", "kaenic", "banshee", "mercury", "fauces", "rostro", "velo", "mercurio")


def _spell_cooldown(display_name: str) -> int:
    low = (display_name or "").lower()
    for key, cd in SPELL_BASE_COOLDOWNS.items():
        if key in low:
            return cd
    return 210


def _format_time(seconds: float) -> str:
    sec = max(0, int(seconds))
    return f"{sec // 60:02d}:{sec % 60:02d}"


class LiveGameMonitor:
    """Lee el estado de una partida de LoL en curso y genera avisos de Coach."""

    def __init__(self) -> None:
        self._client: httpx.AsyncClient | None = None

    def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(verify=False, timeout=1.5)
        return self._client

    async def get_live_state(self) -> dict[str, Any]:
        try:
            client = self._get_client()
            resp = await client.get(LIVE_CLIENT_URL)
            if resp.status_code != 200:
                return {"in_game": False}
            data = resp.json()
        except Exception:
            return {"in_game": False}

        game_data = data.get("gameData", {})
        active = data.get("activePlayer", {})
        all_players = data.get("allPlayers", [])

        game_time = float(game_data.get("gameTime", 0.0))
        active_name = active.get("riotIdGameName") or active.get("summonerName", "")

        # Encontrar equipo del jugador activo
        my_entry = None
        for p in all_players:
            if (
                p.get("riotIdGameName") == active_name
                or p.get("summonerName") == active_name
            ):
                my_entry = p
                break
        if not my_entry and all_players:
            my_entry = all_players[0]

        my_team = my_entry.get("team", "ORDER") if my_entry else "ORDER"
        my_scores = (my_entry or {}).get("scores", {})
        my_cs = int(my_scores.get("creepScore", 0))
        minutes = max(game_time / 60.0, 1.0)
        cs_per_min = round(my_cs / minutes, 1)

        enemies: list[dict[str, Any]] = []
        armor_items = 0
        mr_items = 0
        lv6_threats: list[str] = []

        for p in all_players:
            if p.get("team") == my_team:
                continue
            champ = p.get("championName", "Unknown")
            level = int(p.get("level", 1))
            items = [it.get("displayName", "") for it in p.get("items", [])]
            for it_name in items:
                low_it = it_name.lower()
                if any(k in low_it for k in ARMOR_KEYWORDS):
                    armor_items += 1
                if any(k in low_it for k in MR_KEYWORDS):
                    mr_items += 1
            if level == 6 and 240 <= game_time <= 480:
                lv6_threats.append(champ)

            spells_raw = p.get("summonerSpells", {})
            sp1 = (spells_raw.get("summonerSpellOne") or {}).get("displayName", "Flash")
            sp2 = (spells_raw.get("summonerSpellTwo") or {}).get("displayName", "Ignite")

            enemies.append({
                "champion": champ,
                "level": level,
                "position": p.get("position", ""),
                "is_dead": bool(p.get("isDead", False)),
                "items_count": len(items),
                "spells": [
                    {"name": sp1, "cooldown": _spell_cooldown(sp1)},
                    {"name": sp2, "cooldown": _spell_cooldown(sp2)},
                ],
            })

        # ── Generar avisos tácticos en vivo (con ID único para que la voz no repita) ──
        alerts: list[dict[str, str]] = []

        # 1. Timers clave de objetivos y ventanas de gank/roam (100% legal por reloj oficial)
        if 170 <= game_time <= 195:
            alerts.append({
                "id": "jg_first_clear",
                "type": "warning",
                "title": "Ventana de 1er gank (Min 3:00)",
                "message": "Ojo: el jungla enemigo está terminando su primer clear. Revisá el río y poné un ward.",
            })
        if 250 <= game_time <= 295:
            alerts.append({
                "id": "obj_first_drake",
                "type": "objective",
                "title": "Primer Dragón en breve",
                "message": "En menos de un minuto sale el primer Dragón. Empujá oleada y prepará visión en el río.",
            })
        if 310 <= game_time <= 355:
            alerts.append({
                "id": "obj_grubs",
                "type": "objective",
                "title": "Larvas del Vacío (Grubs)",
                "message": "Las Larvas del Vacío salen en breve. Asegurá prioridad en top y mid.",
            })
        if 360 <= game_time <= 390:
            alerts.append({
                "id": "roam_check_6m",
                "type": "warning",
                "title": "Chequeo de Jungla y Mid (Min 6)",
                "message": "Revisá el minimapa: si hace un rato no ves al jungla o al mid enemigo, tené cuidado con un posible gank o roam.",
            })
        if 540 <= game_time <= 575:
            alerts.append({
                "id": "roam_check_9m",
                "type": "warning",
                "title": "Alerta de rotaciones (Min 9)",
                "message": "Chequeá el minimapa: si no viste al jungla, mid o top enemigo hace un rato, no te extiendas sin visión.",
            })
        if 750 <= game_time <= 785:
            alerts.append({
                "id": "roam_check_12m",
                "type": "warning",
                "title": "Cuidado con flancos y roams",
                "message": "Recordatorio de mapa: verificá dónde están el jungla y el mid rival antes de empujar la oleada.",
            })
        if 790 <= game_time <= 835:
            alerts.append({
                "id": "obj_herald",
                "type": "objective",
                "title": "Heraldo de la Grieta",
                "message": "El Heraldo está por salir. Controlá la visión de top side.",
            })
        if 1150 <= game_time <= 1195:
            alerts.append({
                "id": "obj_baron",
                "type": "objective",
                "title": "Barón Nashor por nacer",
                "message": "Falta menos de un minuto para Barón. Comprá Control Wards y no regales picks aislados.",
            })

        # 2. Spikes de Nivel 6 enemigos
        for threat in lv6_threats[:2]:
            alerts.append({
                "id": f"lv6_{threat}",
                "type": "warning",
                "title": f"{threat} llegó a Nivel 6",
                "message": f"Ojo: {threat} acaba de desbloquear su definitiva. Respetá su rango de all-in.",
            })

        # 3. Alertas de itemización enemiga
        if armor_items >= 3:
            alerts.append({
                "id": "enemy_armor_stack",
                "type": "tip",
                "title": "Enemigo armando armadura",
                "message": "El equipo rival ya acumula varios ítems de armadura. Priorizá penetración de armadura.",
            })
        if mr_items >= 3:
            alerts.append({
                "id": "enemy_mr_stack",
                "type": "tip",
                "title": "Enemigo armando Resistencia Mágica",
                "message": "El equipo rival está armando resistencia mágica. Considerá penetración mágica.",
            })

        # 4. Recordatorio de oro en mano
        current_gold = int(active.get("currentGold", 0))
        if current_gold >= 1650 and game_time >= 240:
            alerts.append({
                "id": f"gold_recall_{int(game_time // 180)}",
                "type": "tip",
                "title": f"Tenés {current_gold} de oro sin gastar",
                "message": f"Tenés {current_gold} de oro en mano. Buscá un buen timing de back para convertirlo en stats.",
            })

        return {
            "in_game": True,
            "game_time": round(game_time, 1),
            "game_time_formatted": _format_time(game_time),
            "active_player": {
                "name": active_name,
                "champion": (my_entry or {}).get("championName", ""),
                "level": int(active.get("level", 1)),
                "current_gold": current_gold,
                "cs": my_cs,
                "cs_per_min": cs_per_min,
                "kda": f"{my_scores.get('kills', 0)}/{my_scores.get('deaths', 0)}/{my_scores.get('assists', 0)}",
            },
            "enemies": enemies,
            "alerts": alerts,
        }
