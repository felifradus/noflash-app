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


# Campeones cuya R al nivel 6 es amenaza de largo alcance / ejecución (no all-in cuerpo a cuerpo)
LONG_RANGE_ULT_CHAMPS = {
    "caitlyn", "jinx", "ezreal", "ashe", "draven", "karthus", "senna",
    "lux", "xerath", "ziggs", "jhin", "twistedfate", "shen", "pantheon",
    "galio", "briar", "gangplank", "soraka", "kaisa",
}

# Campeones cuya R al nivel 6 es un spike real de all-in / engage letal
ALL_IN_ULT_CHAMPS = {
    "zed", "malphite", "leona", "nautilus", "rengar", "vi", "fizz", "diana",
    "pyke", "amumu", "kennen", "annie", "yasuo", "yone", "akali", "talon",
    "darius", "mordekaiser", "camille", "hecarim", "nocturne", "jarvaniv",
    "alistar", "rell", "rakan", "skarner", "warwick", "syndra", "veigar",
    "lissandra", "ahri", "leblanc", "katarina", "irelia", "riven", "renekton",
    "garen", "sett", "tristana", "samira", "lucian", "twitch", "kassadin",
    "ekko", "evelynn", "khazix", "leesin", "qiyana", "naafiri", "sylas",
    "vex", "neeko", "fiddlesticks", "zac", "sejuani", "ornn", "wukong",
}


# Conjuntos tácticos para el Plan de Línea inicial (Min 0–2:30)
ENGAGE_BOT_CHAMPS = {
    "nautilus", "thresh", "blitzcrank", "leona", "pyke", "alistar", "rell",
    "rakan", "maokai", "amumu", "pantheon", "sett", "samira", "tristana", "draven",
}
POKE_LANE_CHAMPS = {
    "caitlyn", "lux", "xerath", "karma", "brand", "velkoz", "ezreal", "varus",
    "ashe", "senna", "zyra", "morgana", "hwei", "syndra", "orianna", "viktor",
    "ziggs", "jayce", "teemo", "quinn", "vayne", "kennen", "heimeirdinger", "heimerdinger",
}
MELEE_ALLIN_SOLO_CHAMPS = {
    "zed", "yasuo", "yone", "talon", "fizz", "akali", "katarina", "qiyana",
    "irelia", "darius", "riven", "sett", "renekton", "aatrox", "camille",
    "fiora", "jax", "olaf", "tryndamere", "kled", "pantheon", "sylas", "ekko",
}
EARLY_INVADE_JUNGLE = {
    "leesin", "graves", "kindred", "nidalee", "shaco", "elise", "khazix",
    "rengar", "belveth", "reksai", "xinzhau", "xinzhao", "jarvaniv", "warwick",
}


def _build_early_lane_plan(
    my_champ: str,
    my_pos: str,
    enemies: list[dict[str, Any]],
    is_en: bool,
) -> tuple[str, str]:
    """Genera recomendación táctica específica para los primeros 3 minutos de línea."""
    pos = (my_pos or "").upper()
    norm = lambda s: "".join(ch for ch in (s or "").lower() if ch.isalnum())

    enemy_by_pos = { (e.get("position") or "").upper(): e.get("champion", "") for e in enemies }

    if pos == "JUNGLE":
        enemy_jg = enemy_by_pos.get("JUNGLE", "")
        if norm(enemy_jg) in EARLY_INVADE_JUNGLE:
            title = f"Early Jungle Plan vs {enemy_jg}" if is_en else f"Plan de Jungla inicial vs {enemy_jg}"
            msg = (
                f"{enemy_jg} loves early invades. Ward your opposite river entrance at 1:15 and track their start."
                if is_en else
                f"Ojo: {enemy_jg} suele invadir temprano. Poné ward defensivo en el río al minuto 1:15 y protegé tu primer clear."
            )
            return title, msg
        title = "Early Jungle Plan (Min 0–3)" if is_en else "Plan de Jungla inicial (Min 0–3)"
        msg = (
            "Focus on a clean first clear into Scuttle at 3:30. Look for a gank on whichever side lane pushes in."
            if is_en else
            "Enfocate en un primer clear limpio hacia el Cangrejo del 3:30 y buscá gank en la línea que quede empujada."
        )
        return title, msg

    if pos in ("BOTTOM", "UTILITY"):
        bot_enemies = [
            e.get("champion", "")
            for e in enemies
            if (e.get("position") or "").upper() in ("BOTTOM", "UTILITY")
        ]
        bot_norms = {norm(c) for c in bot_enemies}
        lane_label = " / ".join(c for c in bot_enemies if c) or ("Bot lane" if is_en else "Bot rival")
        if bot_norms & ENGAGE_BOT_CHAMPS:
            title = f"Lane Plan vs {lane_label}" if is_en else f"Plan de Línea vs {lane_label}"
            msg = (
                "Rush Level 2 first (1st wave + 3 melees) and stay behind minions to deny their engage."
                if is_en else
                "Buscá Nivel 2 primero (primera oleada más 3 melees de la segunda) y jugá detrás de los súbditos contra su engage."
            )
            return title, msg
        if bot_norms & POKE_LANE_CHAMPS:
            title = f"Lane Plan vs {lane_label}" if is_en else f"Plan de Línea vs {lane_label}"
            msg = (
                "Avoid taking free poke at Level 1. Push the wave for prio or wait for a clean Level 2 or 3 all-in."
                if is_en else
                "No regales vida al nivel 1 contra su poke. Empujá rápido para no quedar bajo torre o esperá nivel 2 para tradear."
            )
            return title, msg
        title = f"Lane Plan vs {lane_label}" if is_en else f"Plan de Línea vs {lane_label}"
        msg = (
            "Contest Level 2 first (9 minions) and drop a river ward before 2:45 for the enemy jungler."
            if is_en else
            "Peleá el Nivel 2 primero (9 súbditos) y poné ward en el río antes del minuto 2:45 por el jungla rival."
        )
        return title, msg

    # TOP o MIDDLE (línea sola)
    opp = enemy_by_pos.get(pos, "")
    opp_norm = norm(opp)
    opp_label = opp or ("your lane opponent" if is_en else "tu rival de línea")
    if opp_norm in MELEE_ALLIN_SOLO_CHAMPS:
        title = f"Lane Plan vs {opp_label}" if is_en else f"Plan de Línea vs {opp_label}"
        msg = (
            f"Punish {opp_label} at Level 1 and 2 before their Level 3 combo, and keep the wave near your turret."
            if is_en else
            f"Castigá a {opp_label} en niveles 1 y 2 antes de su combo de nivel 3, y mantené la oleada cerca de tu torre."
        )
        return title, msg
    if opp_norm in POKE_LANE_CHAMPS:
        title = f"Lane Plan vs {opp_label}" if is_en else f"Plan de Línea vs {opp_label}"
        msg = (
            f"Respect {opp_label}'s Level 1 range, keep your HP high, and look for your Level 3 spike or jungle gank."
            if is_en else
            f"Respetá el rango de {opp_label} al nivel 1, cuidá tu vida y buscá tu spike de nivel 3 o gank de tu jungla."
        )
        return title, msg

    title = f"Early Lane Plan ({my_champ})" if is_en else f"Plan de Línea inicial ({my_champ})"
    msg = (
        "Hit Level 2 first (7 minions in solo lane) to win lane prio, and ward river around 2:30."
        if is_en else
        "Buscá el Nivel 2 primero (7 súbditos en línea sola) para ganar prioridad y poné ward en el río al minuto 2:30."
    )
    return title, msg


def _resolve_spell(spell_obj: dict[str, Any], default_name: str = "Flash") -> dict[str, Any]:
    """Resuelve nombre, clave exacta de Data Dragon (dd_key) y cooldown en cualquier idioma."""
    disp = (spell_obj or {}).get("displayName") or default_name
    raw = (spell_obj or {}).get("rawDisplayName") or ""
    combo = f"{raw} {disp}".lower()

    if "summonerflash" in combo or "flash" in combo or "destello" in combo:
        return {"name": disp, "dd_key": "SummonerFlash", "cooldown": 300}
    if "summonerteleport" in combo or "teletransport" in combo or "teleport" in combo:
        return {"name": disp, "dd_key": "SummonerTeleport", "cooldown": 300}
    if "summonerdot" in combo or "ignite" in combo or "prender" in combo or "incendi" in combo:
        return {"name": disp, "dd_key": "SummonerDot", "cooldown": 180}
    if "summonerheal" in combo or "heal" in combo or "curaci" in combo or "curar" in combo:
        return {"name": disp, "dd_key": "SummonerHeal", "cooldown": 240}
    if "summonerexhaust" in combo or "exhaust" in combo or "extenua" in combo or "exaust" in combo:
        return {"name": disp, "dd_key": "SummonerExhaust", "cooldown": 210}
    if "summonerbarrier" in combo or "barrier" in combo or "barrera" in combo or "barreira" in combo:
        return {"name": disp, "dd_key": "SummonerBarrier", "cooldown": 180}
    if "summonerhaste" in combo or "ghost" in combo or "fantasmal" in combo:
        return {"name": disp, "dd_key": "SummonerHaste", "cooldown": 210}
    if "summonerboost" in combo or "cleanse" in combo or "limpiar" in combo or "purificar" in combo:
        return {"name": disp, "dd_key": "SummonerBoost", "cooldown": 210}
    if "summonersmite" in combo or "smite" in combo or "aplastar" in combo or "golpear" in combo:
        return {"name": disp, "dd_key": "SummonerSmite", "cooldown": 90}
    if "summonersnowball" in combo or "mark" in combo or "marca" in combo:
        return {"name": disp, "dd_key": "SummonerSnowball", "cooldown": 80}
    return {"name": disp, "dd_key": "SummonerFlash", "cooldown": _spell_cooldown(disp)}


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

    async def get_live_state(self, lang: str = "es") -> dict[str, Any]:
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

        allies: list[dict[str, Any]] = []
        enemies: list[dict[str, Any]] = []
        armor_items = 0
        mr_items = 0
        lv6_threats: list[str] = []

        def _extract_riot_id(player: dict[str, Any]) -> tuple[str, str]:
            g = (player.get("riotIdGameName") or "").strip()
            t = (player.get("riotIdTagLine") or "").strip()
            if not g:
                raw_id = (player.get("riotId") or player.get("summonerName") or "").strip()
                if "#" in raw_id:
                    g, t = raw_id.split("#", 1)
                else:
                    g = raw_id
            return g.strip(), t.strip()

        for p in all_players:
            champ = p.get("championName", "Unknown")
            level = int(p.get("level", 1))
            g_name, t_line = _extract_riot_id(p)
            is_me = (p is my_entry)

            if p.get("team") == my_team:
                allies.append({
                    "champion": champ,
                    "level": level,
                    "position": p.get("position", ""),
                    "game_name": g_name,
                    "tag_line": t_line,
                    "is_me": is_me,
                })
                continue

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
            sp1_info = _resolve_spell(spells_raw.get("summonerSpellOne") or {}, "Flash")
            sp2_info = _resolve_spell(spells_raw.get("summonerSpellTwo") or {}, "Ignite")

            from app.voice_commands import apply_haste, calc_item_haste, get_ult_cooldown
            item_ids = [it.get("itemID", 0) for it in p.get("items", []) if it.get("itemID")]
            _, _, summ_haste = calc_item_haste(item_ids)
            if summ_haste > 0:
                sp1_info["cooldown"] = apply_haste(sp1_info["cooldown"], summ_haste)
                sp2_info["cooldown"] = apply_haste(sp2_info["cooldown"], summ_haste)

            enemies.append({
                "champion": champ,
                "level": level,
                "position": p.get("position", ""),
                "game_name": g_name,
                "tag_line": t_line,
                "is_dead": bool(p.get("isDead", False)),
                "items_count": len(items),
                "spells": [sp1_info, sp2_info],
                "ult_cooldown": get_ult_cooldown(champ, level, item_ids=item_ids),
            })

        # ── Generar avisos tácticos en vivo (con ID único para que la voz no repita) ──
        alerts: list[dict[str, str]] = []
        is_en = (lang or "es").lower() != "es"
        my_champ_name = (my_entry or {}).get("championName", "")
        my_pos_name = ((my_entry or {}).get("position") or "").upper()

        # 0. Plan táctico de inicio de línea (0:15 – 2:35) según tu campeón, rol y matchup
        if 15 <= game_time <= 155:
            lp_title, lp_msg = _build_early_lane_plan(my_champ_name, my_pos_name, enemies, is_en)
            alerts.append({
                "id": "early_lane_plan",
                "type": "tip",
                "title": lp_title,
                "message": lp_msg,
            })

        # 1. Timers clave de objetivos adaptados a tu ROL (timers oficiales actuales)
        if 170 <= game_time <= 195 and my_pos_name != "JUNGLE":
            alerts.append({
                "id": "jg_first_clear",
                "type": "warning",
                "title": "1st Gank Window (3:00)" if is_en else "Ventana de 1er gank (Min 3:00)",
                "message": "Enemy jungler finishing first clear — drop a river ward." if is_en else "Jungla enemigo terminando primer clear — poné ward en el río.",
            })
        if 255 <= game_time <= 290:
            if my_pos_name == "TOP":
                drake_msg = (
                    "First Drake at 5:00 — enemy jungler is likely botside; pressure top or watch TP."
                    if is_en else
                    "Primer Dragón al 5:00 — el jungla rival puede estar en bot; presioná top o revisá TP."
                )
            else:
                drake_msg = (
                    "First Drake at 5:00 — push wave and prep bot river vision."
                    if is_en else
                    "Primer Dragón al 5:00 — empujá oleada y prepará visión en el río de bot."
                )
            alerts.append({
                "id": "obj_first_drake",
                "type": "objective",
                "title": "First Drake (5:00)" if is_en else "Primer Dragón (5:00)",
                "message": drake_msg,
            })
        if 435 <= game_time <= 470:
            if my_pos_name == "BOTTOM":
                grubs_msg = (
                    "Voidgrubs spawn at 8:00 — play safe if your support roams, or pressure bot plates."
                    if is_en else
                    "Grubs al 8:00 — jugá seguro si tu support rota, o presioná placas en bot."
                )
            elif my_pos_name == "UTILITY":
                grubs_msg = (
                    "Voidgrubs at 8:00 — look for a roam timer if your ADC is safe."
                    if is_en else
                    "Grubs al 8:00 — buscá ventana de roam a top si tu ADC queda seguro."
                )
            else:
                grubs_msg = (
                    "Voidgrubs spawn at 8:00 — push your wave and prep top river."
                    if is_en else
                    "Grubs al 8:00 — empujá tu oleada y prepará el río de top."
                )
            alerts.append({
                "id": "obj_grubs",
                "type": "objective",
                "title": "Voidgrubs (8:00)" if is_en else "Larvas del Vacío (8:00)",
                "message": grubs_msg,
            })
        if 855 <= game_time <= 890:
            if my_pos_name == "BOTTOM":
                herald_msg = (
                    "Rift Herald at 15:00 — rotate mid if bot tower is down, or play safe weakside."
                    if is_en else
                    "Heraldo al 15:00 — rotá a mid si ya cayó torre de bot, o jugá seguro en weakside."
                )
            else:
                herald_msg = (
                    "Rift Herald spawns at 15:00 — control top river vision."
                    if is_en else
                    "Heraldo al 15:00 — controlá la visión del río de top."
                )
            alerts.append({
                "id": "obj_herald",
                "type": "objective",
                "title": "Rift Herald (15:00)" if is_en else "Heraldo de la Grieta (15:00)",
                "message": herald_msg,
            })
        if 1150 <= game_time <= 1195:
            alerts.append({
                "id": "obj_baron",
                "type": "objective",
                "title": "Baron Nashor spawning soon" if is_en else "Barón Nashor por nacer",
                "message": "Baron spawns in under a minute. Buy Control Wards and avoid getting picked off." if is_en else "Falta menos de un minuto para Barón. Comprá Control Wards y no regales picks aislados.",
            })

        # 2. Spikes de Nivel 6 enemigos (solo amenazas reales y con mensaje acorde al campeón)
        for threat in lv6_threats[:1]:
            norm_t = "".join(ch for ch in threat.lower() if ch.isalnum())
            if norm_t in LONG_RANGE_ULT_CHAMPS:
                alerts.append({
                    "id": f"lv6_{norm_t}",
                    "type": "warning",
                    "title": f"{threat} hit Level 6 (Long-range R)" if is_en else f"{threat} llegó a Nivel 6 (R de largo alcance)",
                    "message": f"Watch out: {threat} has their long-range ultimate. Don't stay low HP." if is_en else f"Ojo: {threat} ya tiene su R de largo alcance. Cuidado si te quedás con poca vida.",
                })
            elif norm_t in ALL_IN_ULT_CHAMPS:
                alerts.append({
                    "id": f"lv6_{norm_t}",
                    "type": "warning",
                    "title": f"{threat} hit Level 6 (All-in)" if is_en else f"{threat} llegó a Nivel 6 (All-in)",
                    "message": f"Watch out: {threat} just unlocked their ultimate. Respect their engage." if is_en else f"Ojo: {threat} acaba de subir a nivel 6. Respetá su engage.",
                })

        # 3. Alertas de itemización enemiga
        if armor_items >= 3:
            alerts.append({
                "id": "enemy_armor_stack",
                "type": "tip",
                "title": "Enemies stacking Armor" if is_en else "Enemigo armando armadura",
                "message": "Enemy team has multiple armor items. Prioritize armor penetration." if is_en else "El equipo rival ya acumula varios ítems de armadura. Priorizá penetración de armadura.",
            })
        if mr_items >= 3:
            alerts.append({
                "id": "enemy_mr_stack",
                "type": "tip",
                "title": "Enemies stacking Magic Resist" if is_en else "Enemigo armando Resistencia Mágica",
                "message": "Enemy team is stacking magic resist. Consider magic penetration." if is_en else "El equipo rival está armando resistencia mágica. Considerá penetración mágica.",
            })

        # 4. Recordatorio de oro en mano
        current_gold = int(active.get("currentGold", 0))
        if current_gold >= 1650 and game_time >= 240:
            alerts.append({
                "id": f"gold_recall_{int(game_time // 180)}",
                "type": "tip",
                "title": f"You have {current_gold} unspent gold" if is_en else f"Tenés {current_gold} de oro sin gastar",
                "message": f"You are sitting on {current_gold} gold. Look for a clean recall timing to spend it." if is_en else f"Tenés {current_gold} de oro en mano. Buscá un buen timing de back para convertirlo en stats.",
            })

        # 5. Refuerzo positivo en partida (cuando venís carreando o farmeando increíble)
        my_kills = int(my_scores.get("kills", 0))
        my_deaths = int(my_scores.get("deaths", 0))
        if my_kills >= 3 and my_deaths <= 1 and game_time >= 240:
            alerts.append({
                "id": "pos_snowball",
                "type": "tip",
                "title": "Clean Snowball" if is_en else "Buen Snowball",
                "message": "Clean start — great tempo, keep snowballing." if is_en else "Gran arranque — excelente ritmo, seguí así.",
            })
        elif cs_per_min >= 8.0 and game_time >= 600:
            alerts.append({
                "id": "pos_farm",
                "type": "tip",
                "title": f"Elite Farm ({cs_per_min} CS/m)" if is_en else f"Farm Elite ({cs_per_min} CS/m)",
                "message": "Great farm pace — you are ahead of the curve." if is_en else "Excelente ritmo de farm — venís por delante.",
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
            "allies": allies,
            "enemies": enemies,
            "alerts": alerts,
        }
