"""
Motor de análisis de rendimiento de jugadores de League of Legends.
Procesa el historial de partidas, maestrías y estadísticas ranked
para generar recomendaciones de draft personalizadas.
"""

from typing import Any
import random

from app.data.counter_data import (
    CHAMPION_ID_TO_NAME,
    CHAMPION_TAGS,
    COUNTER_DATA,
    SYNERGY_DATA,
)


def _safe_get(data: dict[str, Any], *keys: str, default: Any = 0) -> Any:
    """Accede a claves anidadas de forma segura, retornando default si falta alguna."""
    current = data
    for key in keys:
        if isinstance(current, dict):
            current = current.get(key, default)
        else:
            return default
    return current


def _champion_name(champion_id: int) -> str:
    """Convierte un ID numérico de campeón a su nombre."""
    return CHAMPION_ID_TO_NAME.get(champion_id, f"Campeón #{champion_id}")


def _map_role(individual_position: str) -> str:
    """Mapea la posición de la API a nuestros roles simplificados."""
    mapping: dict[str, str] = {
        "TOP": "TOP",
        "JUNGLE": "JG",
        "MIDDLE": "MID",
        "BOTTOM": "ADC",
        "UTILITY": "SUP",
    }
    return mapping.get(individual_position.upper(), individual_position.upper())


class PlayerAnalyzer:
    """
    Analiza el rendimiento de un jugador basándose en su historial
    de partidas, maestrías de campeón y estadísticas de ranked.
    """

    def analyze_player(
        self,
        match_history: list[dict[str, Any]],
        masteries: list[dict[str, Any]],
        ranked_stats: list[dict[str, Any]],
        puuid: str,
        lang: str = "es",
    ) -> dict[str, Any]:
        """
        Analiza al jugador y retorna estadísticas completas.

        Args:
            match_history: Lista de detalles de partidas (de la Match API v5)
            masteries: Lista de maestrías de campeón
            ranked_stats: Estadísticas de ranked del jugador
            puuid: PUUID del jugador para identificarlo en las partidas

        Returns:
            Dict con champion_stats, best_champions, role_analysis y player_summary
        """
        champion_stats = self._calculate_champion_stats(match_history, puuid)
        best_champions = self._rank_best_champions(champion_stats)
        role_analysis = self._analyze_roles(champion_stats)
        player_summary = self._build_player_summary(
            champion_stats, ranked_stats, match_history, puuid
        )

        # Agregar datos de maestría al resumen y exponer top maestrías para el Coach
        mastery_map = self._build_mastery_map(masteries)
        for champ_name, stats in champion_stats.items():
            if champ_name in mastery_map:
                stats["mastery_level"] = mastery_map[champ_name].get("championLevel", 0)
                stats["mastery_points"] = mastery_map[champ_name].get("championPoints", 0)

        mastery_top: dict[str, dict[str, int]] = {}
        for m in (masteries or [])[:30]:
            c_name = _champion_name(m.get("championId", 0))
            if not c_name.startswith("Campeón #"):
                mastery_top[c_name] = {
                    "level": int(m.get("championLevel", 0)),
                    "points": int(m.get("championPoints", 0)),
                }

        mental_check = self._analyze_mental_and_mistakes(match_history, puuid)
        fun_facts = self._build_fun_facts(match_history, puuid, lang=lang)

        result = {
            "champion_stats": champion_stats,
            "best_champions": best_champions,
            "role_analysis": role_analysis,
            "player_summary": player_summary,
            "mastery_top": mastery_top,
            "mental_check": mental_check,
            "fun_facts": fun_facts,
        }
        if (lang or "es").lower() != "es":
            self._localize_analysis_to_en(result)
        return result

    def _calculate_champion_stats(
        self, match_history: list[dict[str, Any]], puuid: str
    ) -> dict[str, dict[str, Any]]:
        """Calcula estadísticas por campeón a partir del historial."""
        stats: dict[str, dict[str, Any]] = {}

        for match in match_history:
            try:
                info = match.get("info", {})
                participants = info.get("participants", [])

                # Buscar al jugador en los participantes
                player_data: dict[str, Any] | None = None
                for p in participants:
                    if p.get("puuid") == puuid:
                        player_data = p
                        break

                if player_data is None:
                    continue

                champ_name = player_data.get("championName", "Desconocido")
                won = player_data.get("win", False)
                kills = _safe_get(player_data, "kills")
                deaths = _safe_get(player_data, "deaths")
                assists = _safe_get(player_data, "assists")
                cs = _safe_get(player_data, "totalMinionsKilled") + _safe_get(
                    player_data, "neutralMinionsKilled"
                )
                vision_score = _safe_get(player_data, "visionScore")
                total_damage = _safe_get(player_data, "totalDamageDealtToChampions")
                game_duration = _safe_get(info, "gameDuration", default=1)
                role = _map_role(
                    player_data.get("individualPosition", player_data.get("teamPosition", "UNKNOWN"))
                )

                # Calcular damage share del equipo
                team_id = player_data.get("teamId", 100)
                team_damage = sum(
                    _safe_get(p2, "totalDamageDealtToChampions")
                    for p2 in participants
                    if p2.get("teamId") == team_id
                )
                damage_share = (total_damage / team_damage * 100) if team_damage > 0 else 0

                # KDA
                kda = (kills + assists) / max(deaths, 1)

                # CS por minuto
                minutes = game_duration / 60.0 if game_duration > 0 else 1
                cs_per_min = cs / minutes

                # Métricas avanzadas del bloque challenges de Riot Match v5
                challenges = player_data.get("challenges") or {}
                cs_at_10 = challenges.get("laneMinionsFirst10Minutes")
                dpm = challenges.get("damagePerMinute") or (total_damage / minutes)
                kp = challenges.get("killParticipation")
                solo_kills = int(challenges.get("soloKills", 0) or 0)
                turret_takedowns = int(player_data.get("turretTakedowns", 0) or 0)
                control_wards = int(player_data.get("visionWardsBoughtInGame", 0) or 0)

                # Inicializar si es la primera vez que vemos este campeón
                if champ_name not in stats:
                    stats[champ_name] = {
                        "games": 0,
                        "wins": 0,
                        "losses": 0,
                        "total_kills": 0,
                        "total_deaths": 0,
                        "total_assists": 0,
                        "total_cs_per_min": 0.0,
                        "total_vision_score": 0,
                        "total_damage_share": 0.0,
                        "total_dpm": 0.0,
                        "total_control_wards": 0,
                        "total_turrets": 0,
                        "total_solo_kills": 0,
                        "cs10_values": [],
                        "kp_values": [],
                        "deaths_wins": [],
                        "deaths_losses": [],
                        "roles_played": [],
                        "recent_results": [],  # últimos resultados (True/False)
                        "kda_values": [],
                    }

                s = stats[champ_name]
                s["games"] += 1
                if won:
                    s["wins"] += 1
                    s["deaths_wins"].append(deaths)
                else:
                    s["losses"] += 1
                    s["deaths_losses"].append(deaths)
                s["total_kills"] += kills
                s["total_deaths"] += deaths
                s["total_assists"] += assists
                s["total_cs_per_min"] += cs_per_min
                s["total_vision_score"] += vision_score
                s["total_damage_share"] += damage_share
                s["total_dpm"] += float(dpm)
                s["total_control_wards"] += control_wards
                s["total_turrets"] += turret_takedowns
                s["total_solo_kills"] += solo_kills
                if cs_at_10 is not None:
                    s["cs10_values"].append(float(cs_at_10))
                if kp is not None:
                    s["kp_values"].append(float(kp) * 100.0)
                s["kda_values"].append(kda)
                s["recent_results"].append(won)
                if role and role not in s["roles_played"]:
                    s["roles_played"].append(role)

            except Exception:
                # Si un match tiene datos incompletos, lo salteamos
                continue

        # Calcular promedios + análisis profundo por campeón
        for champ_name, s in stats.items():
            games = s["games"]
            s["win_rate"] = round((s["wins"] / games) * 100, 1) if games > 0 else 0
            s["avg_kda"] = round(sum(s["kda_values"]) / len(s["kda_values"]), 2) if s["kda_values"] else 0
            s["avg_cs_per_min"] = round(s["total_cs_per_min"] / games, 1) if games > 0 else 0
            s["avg_vision_score"] = round(s["total_vision_score"] / games, 1) if games > 0 else 0
            s["avg_damage_share"] = round(s["total_damage_share"] / games, 1) if games > 0 else 0

            avg_deaths = round(s["total_deaths"] / games, 1) if games > 0 else 0
            avg_dpm = round(s["total_dpm"] / games) if games > 0 else 0
            avg_pinks = round(s["total_control_wards"] / games, 1) if games > 0 else 0
            avg_turrets = round(s["total_turrets"] / games, 1) if games > 0 else 0
            avg_cs10 = round(sum(s["cs10_values"]) / len(s["cs10_values"]), 1) if s["cs10_values"] else None
            avg_kp = round(sum(s["kp_values"]) / len(s["kp_values"]), 1) if s["kp_values"] else None
            d_win = round(sum(s["deaths_wins"]) / len(s["deaths_wins"]), 1) if s["deaths_wins"] else None
            d_loss = round(sum(s["deaths_losses"]) / len(s["deaths_losses"]), 1) if s["deaths_losses"] else None
            is_support = "SUP" in s["roles_played"] and len(s["roles_played"]) == 1

            strengths: list[str] = []
            improvements: list[str] = []

            # 1. CS / Early CS
            if not is_support:
                if s["avg_cs_per_min"] >= 7.5:
                    strengths.append(f"🌾 Excelente farmeo ({s['avg_cs_per_min']} CS/min) — generás mucha ventaja de oro.")
                elif s["avg_cs_per_min"] < 6.0:
                    improvements.append(f"🌾 Farmeo bajo ({s['avg_cs_per_min']} CS/min): perdés oro clave en oleadas laterales en mid game.")
                if avg_cs10 is not None:
                    if avg_cs10 >= 72:
                        strengths.append(f"⏱️ Dominio de early farm ({avg_cs10} CS al minuto 10).")
                    elif avg_cs10 < 58:
                        improvements.append(f"⏱️ Early CS mejorable ({avg_cs10} CS al min 10): practicá los primeros 10 minutos de last-hit y timings de back.")

            # 2. Daño e impacto
            if s["avg_damage_share"] >= 26 or avg_dpm >= 750:
                strengths.append(f"💥 Alto impacto de daño ({s['avg_damage_share']}% del equipo · {avg_dpm} DPM).")
            elif not is_support and s["avg_damage_share"] < 18:
                improvements.append(f"💥 Bajo aporte de daño ({s['avg_damage_share']}% del equipo): buscá posicionarte mejor para pegar más en teamfights.")

            # 3. Participación en peleas (KP) y Torres
            if avg_kp is not None:
                if avg_kp >= 58:
                    strengths.append(f"⚔️ Gran participación en peleas ({avg_kp}% KP) — estás presente cuando importa.")
                elif avg_kp < 42:
                    improvements.append(f"⚔️ Baja participación en peleas ({avg_kp}% KP): conectá mejor con tu equipo en objetivos.")
            if avg_turrets >= 2.2:
                strengths.append(f"🏰 Alta presión de torres ({avg_turrets} torres/partida) — convertís ventaja en mapa.")

            # 4. Supervivencia / Muertes en derrotas vs victorias
            if avg_deaths <= 4.2:
                strengths.append(f"🛡️ Muy buena supervivencia ({avg_deaths} muertes/partida).")
            elif avg_deaths >= 6.2:
                improvements.append(f"💀 Muchas muertes promedio ({avg_deaths}/partida): revisá tu posicionamiento en línea y flancos sin visión.")

            if d_win is not None and d_loss is not None and (d_loss - d_win) >= 2.2:
                improvements.append(
                    f"📉 Te cuesta frenar la sangría al ir atrás ({d_loss} muertes en derrotas vs {d_win} en victorias)."
                )

            # 5. Visión / Control Wards (vulnerabilidad a ganks)
            if avg_pinks < 1.0:
                improvements.append(
                    f"👁️ Pocas Control Wards ({avg_pinks}/partida): más vulnerable a ganks tempranos y emboscadas en río."
                )
            elif avg_pinks >= 2.5:
                strengths.append(f"👁️ Excelente control de visión ({avg_pinks} Control Wards/partida).")

            if not strengths:
                strengths.append(f"✅ Rendimiento parejo con {s['avg_kda']} KDA en {games} partidas.")
            if not improvements:
                improvements.append("🌟 Sin debilidades marcadas con este campeón — ¡seguí explotándolo!")

            s["deep_analysis"] = {
                "metrics": {
                    "avg_deaths": avg_deaths,
                    "avg_dpm": avg_dpm,
                    "avg_cs10": avg_cs10,
                    "avg_kp": avg_kp,
                    "avg_pinks": avg_pinks,
                    "avg_turrets": avg_turrets,
                    "solo_kills": s["total_solo_kills"],
                    "deaths_in_wins": d_win,
                    "deaths_in_losses": d_loss,
                },
                "strengths": strengths[:4],
                "improvements": improvements[:4],
            }

            # Recent form: win rate de las últimas 5 partidas (más recientes primero)
            last_5 = s["recent_results"][:5]
            s["recent_form"] = round(
                (sum(1 for r in last_5 if r) / len(last_5)) * 100, 1
            ) if last_5 else 0

            # Limpiar campos internos que no necesitamos exponer
            for internal_key in (
                "total_kills", "total_deaths", "total_assists",
                "total_cs_per_min", "total_vision_score", "total_damage_share",
                "total_dpm", "total_control_wards", "total_turrets", "total_solo_kills",
                "cs10_values", "kp_values", "deaths_wins", "deaths_losses",
                "kda_values", "recent_results",
            ):
                s.pop(internal_key, None)

        return stats

    def _rank_best_champions(
        self, champion_stats: dict[str, dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """
        Calcula el top 10 de mejores campeones usando un score compuesto:
        win_rate * 0.4 + games_normalized * 0.3 + kda_normalized * 0.2 + recent_form * 0.1
        """
        if not champion_stats:
            return []

        # Encontrar máximos para normalización
        max_games = max(s["games"] for s in champion_stats.values()) or 1
        max_kda = max(s["avg_kda"] for s in champion_stats.values()) or 1

        scored: list[dict[str, Any]] = []
        for champ_name, s in champion_stats.items():
            # Win rate suavizado (Bayesiano): evita que 1/1 (100%) le gane a 10/14 (71%)
            smoothed_wr = (s["wins"] + 2.5) / (s["games"] + 5.0)
            games_norm = s["games"] / max_games
            kda_norm = min(s["avg_kda"] / max_kda, 1.0)
            recent_form_norm = s["recent_form"] / 100.0

            score = (
                smoothed_wr * 0.45
                + games_norm * 0.30
                + kda_norm * 0.15
                + recent_form_norm * 0.10
            )

            scored.append({
                "champion": champ_name,
                "score": round(score, 3),
                "win_rate": s["win_rate"],
                "games": s["games"],
                "avg_kda": s["avg_kda"],
                "recent_form": s["recent_form"],
            })

        scored.sort(key=lambda x: x["score"], reverse=True)
        return scored[:10]

    def _analyze_roles(
        self, champion_stats: dict[str, dict[str, Any]]
    ) -> dict[str, list[dict[str, Any]]]:
        """Encuentra los mejores campeones del jugador por cada rol."""
        roles: dict[str, list[dict[str, Any]]] = {
            "TOP": [], "JG": [], "MID": [], "ADC": [], "SUP": []
        }

        for champ_name, s in champion_stats.items():
            for role in s.get("roles_played", []):
                if role in roles:
                    roles[role].append({
                        "champion": champ_name,
                        "games": s["games"],
                        "win_rate": s["win_rate"],
                        "avg_kda": s["avg_kda"],
                    })

        # Ordenar cada rol por win_rate (con mínimo 2 games)
        for role in roles:
            roles[role].sort(
                key=lambda x: (x["games"] >= 2, x["win_rate"], x["games"]),
                reverse=True,
            )
            roles[role] = roles[role][:5]  # top 5 por rol

        return roles

    def _build_player_summary(
        self,
        champion_stats: dict[str, dict[str, Any]],
        ranked_stats: list[dict[str, Any]],
        match_history: list[dict[str, Any]],
        puuid: str,
    ) -> dict[str, Any]:
        """Construye un resumen general del jugador."""
        summary: dict[str, Any] = {}

        # Tier de ranked
        solo_queue = None
        for entry in ranked_stats:
            if entry.get("queueType") == "RANKED_SOLO_5x5":
                solo_queue = entry
                break

        if solo_queue:
            summary["tier"] = f"{solo_queue.get('tier', '?')} {solo_queue.get('rank', '?')}"
            summary["lp"] = solo_queue.get("leaguePoints", 0)
            total_ranked = solo_queue.get("wins", 0) + solo_queue.get("losses", 0)
            summary["ranked_win_rate"] = (
                round(solo_queue.get("wins", 0) / total_ranked * 100, 1)
                if total_ranked > 0
                else 0
            )
            summary["ranked_games"] = total_ranked
        else:
            summary["tier"] = "Sin clasificar"
            summary["lp"] = 0
            summary["ranked_win_rate"] = 0
            summary["ranked_games"] = 0

        # Estilo de juego basado en KDA y damage share promedio
        all_kdas = [s["avg_kda"] for s in champion_stats.values()]
        all_dmg_shares = [s["avg_damage_share"] for s in champion_stats.values()]

        avg_kda_global = sum(all_kdas) / len(all_kdas) if all_kdas else 0
        avg_dmg_share_global = sum(all_dmg_shares) / len(all_dmg_shares) if all_dmg_shares else 0

        if avg_kda_global < 2.0 and avg_dmg_share_global > 25:
            summary["play_style"] = "Agresivo / Alto riesgo"
        elif avg_kda_global > 4.0 and avg_dmg_share_global < 20:
            summary["play_style"] = "Pasivo / Seguro"
        elif avg_kda_global > 3.0 and avg_dmg_share_global > 25:
            summary["play_style"] = "Carry agresivo"
        elif avg_kda_global > 3.0:
            summary["play_style"] = "Equilibrado"
        else:
            summary["play_style"] = "Variable"

        # Profundidad real del champion pool (basada en concentración, no en 3 partidas sueltas)
        total_games = sum(s["games"] for s in champion_stats.values()) or 1
        sorted_by_games = sorted(
            champion_stats.items(), key=lambda kv: kv[1]["games"], reverse=True
        )
        top1_share = (sorted_by_games[0][1]["games"] / total_games) if sorted_by_games else 0
        min_real_games = max(3, int(total_games * 0.05))  # al menos 5% del total de partidas
        effective_champs = sum(
            1 for s in champion_stats.values() if s["games"] >= min_real_games
        )

        if top1_share >= 0.45:
            summary["pool_depth"] = f"Especialista ({sorted_by_games[0][0]})"
        elif effective_champs <= 3:
            summary["pool_depth"] = "Enfocado (2-3 mains)"
        elif effective_champs <= 6:
            summary["pool_depth"] = "Moderado"
        else:
            summary["pool_depth"] = "Amplio (versátil)"

        summary["unique_champions"] = len(champion_stats)
        summary["total_games_analyzed"] = len(match_history)
        summary["avg_kda"] = round(avg_kda_global, 2)
        summary["avg_damage_share"] = round(avg_dmg_share_global, 1)

        return summary

    def _analyze_mental_and_mistakes(
        self, match_history: list[dict[str, Any]], puuid: str
    ) -> dict[str, Any]:
        """
        Analiza las partidas más recientes para detectar señales de tilt/fatiga
        (racha de derrotas, pico de muertes, maratón) y patrones concretos de error.
        """
        recent_games: list[dict[str, Any]] = []
        for match in match_history[:25]:
            info = match.get("info", {})
            duration_min = max(info.get("gameDuration", 0) / 60.0, 1.0)
            for p in info.get("participants", []):
                if p.get("puuid") == puuid:
                    cs = p.get("totalMinionsKilled", 0) + p.get("neutralMinionsKilled", 0)
                    recent_games.append({
                        "win": bool(p.get("win", False)),
                        "kills": int(p.get("kills", 0)),
                        "deaths": int(p.get("deaths", 0)),
                        "assists": int(p.get("assists", 0)),
                        "cs_per_min": cs / duration_min,
                        "control_wards": int(p.get("visionWardsBoughtInGame", 0)),
                        "vision_score": int(p.get("visionScore", 0)),
                        "champion": p.get("championName", ""),
                        "role": _map_role(p.get("teamPosition") or p.get("individualPosition") or ""),
                    })
                    break

        if not recent_games:
            return {
                "status": "ok",
                "title": "Listo para jugar",
                "message": "No hay suficientes partidas recientes para evaluar tu racha.",
                "streak_label": "—",
                "mistakes": [],
            }

        # Calcular racha actual (victorias o derrotas consecutivas desde la más reciente)
        first_win = recent_games[0]["win"]
        streak = 0
        for g in recent_games:
            if g["win"] == first_win:
                streak += 1
            else:
                break

        # Comparar muertes en últimas 3 partidas vs promedio general
        avg_deaths_all = sum(g["deaths"] for g in recent_games) / len(recent_games)
        last3 = recent_games[:3]
        avg_deaths_last3 = sum(g["deaths"] for g in last3) / len(last3)
        death_spike = avg_deaths_last3 >= avg_deaths_all + 2.0 and avg_deaths_last3 >= 6.0

        # Determinar estado mental y elegir mensaje amigable rotativo
        if (not first_win and streak >= 3) or (not first_win and streak >= 2 and death_spike):
            status = "break"
            title = "⏸️ Pausa recomendada (Alerta de Tilt)"
            messages = [
                f"Venís de {streak} derrotas seguidas. Andá a tocar pasto 15 minutitos, tomate algo frío y volvés fresco a carrear.",
                f"Che, van {streak} derrotas al hilo y el LP pide un respiro. Estirá las piernas, despejá la cabeza 20 min y después volvés con todo.",
                f"Se nota un poco de cansancio en las últimas {streak} partidas. Un descanso corto ahora vale mucho más que forzar otra cola.",
                f"Frená un toque: {streak} derrotas seguidas suelen arrastrar al tilt silencioso. Tomate un café o un mate y retomás limpio.",
            ]
            message = random.choice(messages)
        elif (not first_win and streak == 2) or death_spike:
            status = "caution"
            title = "🟡 Ojo con la racha — Jugá seguro"
            messages = [
                "Venís de un par de partidas duras. Si mandás otra, asegurate tu pick más cómodo y evitá peleas innecesarias en early.",
                "Cuidado con jugar en piloto automático: respirá hondo, silenciá el chat si hace falta y confiá en tu main.",
                "Tus muertes subieron un poco en las últimas partidas. Priorizá posicionamiento seguro y visión antes de forzar jugadas.",
            ]
            message = random.choice(messages)
        elif first_win and streak >= 3:
            status = "hot"
            title = f"🔥 En racha ({streak} victorias seguidas)"
            messages = [
                f"Estás volando con {streak} victorias al hilo. ¡Aprovechá el momento y seguí sumando LP!",
                f"Modo imparable: {streak}W seguidas. Seguí respetando tus fundamentos y no te confíes.",
                f"Venís jugando súper limpio ({streak} victorias seguidas). Excelente momento para seguir rankeando.",
            ]
            message = random.choice(messages)
        else:
            status = "ok"
            title = "🟢 Buen estado para jugar"
            messages = [
                "Tu rendimiento reciente viene estable y sin señales de tilt. ¡Mandale cola tranquilo!",
                "Ritmo sólido en tus últimas partidas. Mantené el foco en tu pool principal.",
                "Todo en orden para rankear: venís consistente en tus métricas recientes.",
            ]
            message = random.choice(messages)

        streak_label = f"{streak}V seguidas" if first_win else f"{streak}D seguidas"

        # ── Diagnóstico de errores / oportunidades de mejora en partidas pasadas ──
        mistakes: list[dict[str, str]] = []
        wins_list = [g for g in recent_games if g["win"]]
        losses_list = [g for g in recent_games if not g["win"]]

        if wins_list and losses_list:
            d_win = sum(g["deaths"] for g in wins_list) / len(wins_list)
            d_loss = sum(g["deaths"] for g in losses_list) / len(losses_list)
            if d_loss - d_win >= 2.2:
                mistakes.append({
                    "icon": "💀",
                    "title": "Muchas muertes cuando la partida se complica",
                    "detail": f"En victorias promediás {d_win:.1f} muertes, pero en derrotas subís a {d_loss:.1f}. Cuando vas atrás, evitá forzar peleas sin visión y dejá que el rival cometa errores.",
                })

        avg_pinks = sum(g["control_wards"] for g in recent_games) / len(recent_games)
        if avg_pinks < 1.2:
            mistakes.append({
                "icon": "👁️",
                "title": "Pocas Control Wards compradas",
                "detail": f"Promediás {avg_pinks:.1f} Control Wards por partida. Comprar 1 o 2 por juego antes de Dragón/Barón reduce muchísimo las muertes por flancos.",
            })

        carry_games = [g for g in recent_games if g["role"] in ("TOP", "MID", "ADC")]
        if len(carry_games) >= 5:
            avg_cs = sum(g["cs_per_min"] for g in carry_games) / len(carry_games)
            if avg_cs < 6.8:
                mistakes.append({
                    "icon": "🌾",
                    "title": "Margen de mejora en farmeo (CS/min)",
                    "detail": f"Tu promedio reciente en línea es {avg_cs:.1f} CS/min. Recoger oleadas laterales en mid game te da 1 ítem de ventaja gratis.",
                })

        # Detectar si perdió partidas probando campeones fuera de su main
        champ_counts: dict[str, list[bool]] = {}
        for g in recent_games:
            champ_counts.setdefault(g["champion"], []).append(g["win"])
        off_meta_losses = sum(
            res.count(False) for res in champ_counts.values() if len(res) <= 2
        )
        if off_meta_losses >= 4:
            mistakes.append({
                "icon": "🎯",
                "title": "LP perdidos fuera de tu pool principal",
                "detail": f"Tuviste {off_meta_losses} derrotas recientes probando campeones con 1–2 partidas. Quedarte en tus mains te da mucho mejor win rate.",
            })

        if not mistakes:
            mistakes.append({
                "icon": "✅",
                "title": "Fundamentos muy sólidos",
                "detail": "Tus muertes, visión y farmeo vienen súper consistentes en tus últimas partidas. ¡Seguí así!",
            })

        return {
            "status": status,
            "title": title,
            "message": message,
            "streak_label": streak_label,
            "mistakes": mistakes[:3],
        }

    def _build_mastery_map(
        self, masteries: list[dict[str, Any]]
    ) -> dict[str, dict[str, Any]]:
        """Construye un mapa nombre_campeon → datos de maestría."""
        mastery_map: dict[str, dict[str, Any]] = {}
        for m in masteries:
            champ_id = m.get("championId", 0)
            champ_name = _champion_name(champ_id)
            mastery_map[champ_name] = m
        return mastery_map

    @staticmethod
    def _score_to_tier(score: float) -> str:
        """Convierte un draft_score (0..1) a un Tier legible por jugadores."""
        if score >= 0.72:
            return "S+"
        if score >= 0.60:
            return "S"
        if score >= 0.48:
            return "A"
        return "B"

    def get_draft_recommendations(
        self,
        player_analysis: dict[str, Any],
        ally_picks: list[str],
        enemy_picks: list[str],
        role: str,
        bans: list[str] | None = None,
        lang: str = "es",
    ) -> list[dict[str, Any]]:
        """
        Genera recomendaciones de draft personalizadas en tiempo real con criterio de Coach.

        Combina:
        - Historial reciente suavizado (Bayesiano) + puntos de maestría
        - Matchups y counters directos contra picks enemigos
        - Sinergias con picks aliados
        - Balance de composición (AP/AD, frontline, engage)
        """
        champion_stats = player_analysis.get("champion_stats", {})
        mastery_top = player_analysis.get("mastery_top", {})
        ban_list = bans or []
        already_taken = set(ally_picks + enemy_picks + ban_list)
        role_normalized = role.lower()
        max_games = max((s.get("games", 1) for s in champion_stats.values()), default=1) or 1

        candidates: list[dict[str, Any]] = []
        included_names: set[str] = set()

        # 1. Evaluar campeones del historial reciente del jugador
        for champ_name, stats in champion_stats.items():
            if champ_name in already_taken:
                continue

            games = stats.get("games", 0)
            wins = stats.get("wins", round(games * stats.get("win_rate", 50.0) / 100.0))
            wr = stats.get("win_rate", 50.0)
            if games >= 4 and wr < 38:
                continue

            champ_tags = CHAMPION_TAGS.get(champ_name, {})
            champ_roles = champ_tags.get("roles", []) if isinstance(champ_tags, dict) else []
            played_roles = stats.get("roles_played", [])
            if isinstance(played_roles, dict):
                played_roles = list(played_roles.keys())
            plays_role = (
                role_normalized in [r.lower() for r in champ_roles]
                or role_normalized in [r.lower() for r in played_roles]
            )
            if not plays_role and champ_roles:
                continue

            # Win rate suavizado (Bayesiano) + volumen de partidas + bonus de maestría
            smoothed_wr = (wins + 2.5) / (games + 5.0)
            volume_score = min(1.0, (games / max_games) ** 0.7)
            mastery_pts = stats.get("mastery_points") or mastery_top.get(champ_name, {}).get("points", 0)
            mastery_bonus = min(0.15, (mastery_pts / 150_000) * 0.15) if mastery_pts else 0.0

            comfort = min(1.0, smoothed_wr * 0.60 + volume_score * 0.30 + mastery_bonus)
            counter_value = self._calc_counter_value(champ_name, enemy_picks)
            synergy_value = self._calc_synergy_value(champ_name, ally_picks)
            meta_value = self._calc_meta_value(champ_name, ally_picks, enemy_picks)

            draft_score = min(
                0.98,
                comfort * 0.45
                + counter_value * 0.25
                + synergy_value * 0.20
                + meta_value * 0.10,
            )

            explanation = self._generate_explanation(
                champ_name, stats, comfort, counter_value,
                synergy_value, meta_value, ally_picks, enemy_picks,
            )
            tag = "Tu Main" if games >= 5 or mastery_pts >= 80_000 else "Pool Reciente"

            included_names.add(champ_name)
            candidates.append({
                "champion": champ_name,
                "tier": self._score_to_tier(draft_score),
                "tag": tag,
                "draft_score": round(draft_score, 3),
                "scores_breakdown": {
                    "player_comfort": round(comfort, 3),
                    "counter_value": round(counter_value, 3),
                    "team_synergy": round(synergy_value, 3),
                    "meta_strength": round(meta_value, 3),
                },
                "player_stats": {
                    "games": games,
                    "win_rate": wr,
                    "avg_kda": stats.get("avg_kda", 1.0),
                    "recent_form": stats.get("recent_form", 50.0),
                    "mastery_points": mastery_pts,
                },
                "setup": self._get_runes_and_spells(champ_name, role, enemy_picks),
                "explanation": explanation,
            })

        # 2. Completar con campeones de alta MAESTRÍA del jugador en este rol (aunque no jugó esta semana)
        if len(candidates) < 5 and mastery_top:
            for champ_name, mdata in mastery_top.items():
                if champ_name in already_taken or champ_name in included_names:
                    continue
                tags = CHAMPION_TAGS.get(champ_name)
                if not isinstance(tags, dict):
                    continue
                if role_normalized not in [r.lower() for r in tags.get("roles", [])]:
                    continue
                pts = mdata.get("points", 0)
                if pts < 20_000:
                    continue

                comfort = min(0.75, 0.42 + (pts / 200_000) * 0.30)
                counter_value = self._calc_counter_value(champ_name, enemy_picks)
                synergy_value = self._calc_synergy_value(champ_name, ally_picks)
                meta_value = self._calc_meta_value(champ_name, ally_picks, enemy_picks)
                draft_score = (
                    comfort * 0.40
                    + counter_value * 0.30
                    + synergy_value * 0.20
                    + meta_value * 0.10
                )

                pts_k = f"{pts // 1000}k"
                reasons = [f"Lo dominás ({pts_k} pts de maestría) aunque no lo jugaste en tus últimas partidas"]
                champ_counters = COUNTER_DATA.get(champ_name, {}).get("counters", [])
                countered = [e for e in enemy_picks if e in champ_counters]
                if countered:
                    reasons.append(f"countea a {', '.join(countered)}")
                champ_syn = [s["champion"] for s in SYNERGY_DATA.get(champ_name, [])]
                syns = [a for a in ally_picks if a in champ_syn]
                if syns:
                    reasons.append(f"gran sinergia con {', '.join(syns)}")

                included_names.add(champ_name)
                candidates.append({
                    "champion": champ_name,
                    "tier": self._score_to_tier(draft_score),
                    "tag": f"Maestría {pts_k}",
                    "draft_score": round(draft_score, 3),
                    "scores_breakdown": {
                        "player_comfort": round(comfort, 3),
                        "counter_value": round(counter_value, 3),
                        "team_synergy": round(synergy_value, 3),
                        "meta_strength": round(meta_value, 3),
                    },
                    "player_stats": {
                        "games": 0,
                        "win_rate": 0.0,
                        "avg_kda": 0.0,
                        "recent_form": 50.0,
                        "mastery_points": pts,
                    },
                    "setup": self._get_runes_and_spells(champ_name, role, enemy_picks),
                    "explanation": ". ".join(reasons) + ".",
                })

        # 3. Si todavía faltan opciones para llegar a 5, sugerir mejores counters/sinergias del rol
        if len(candidates) < 5:
            fallback_candidates: list[dict[str, Any]] = []
            for champ_name, tags in CHAMPION_TAGS.items():
                if champ_name in already_taken or champ_name in included_names:
                    continue
                if not isinstance(tags, dict):
                    continue
                champ_roles = [r.lower() for r in tags.get("roles", [])]
                if role_normalized not in champ_roles:
                    continue

                counter_value = self._calc_counter_value(champ_name, enemy_picks)
                synergy_value = self._calc_synergy_value(champ_name, ally_picks)
                meta_value = self._calc_meta_value(champ_name, ally_picks, enemy_picks)
                comfort = 0.25

                draft_score = (
                    comfort * 0.20
                    + counter_value * 0.40
                    + synergy_value * 0.25
                    + meta_value * 0.15
                )

                reasons = ["Pick estratégico del rol"]
                champ_counters = COUNTER_DATA.get(champ_name, {}).get("counters", [])
                countered = [e for e in enemy_picks if e in champ_counters]
                if countered:
                    reasons.append(f"countea directamente a {', '.join(countered)}")
                champ_syn = [s["champion"] for s in SYNERGY_DATA.get(champ_name, [])]
                syns = [a for a in ally_picks if a in champ_syn]
                if syns:
                    reasons.append(f"excelente sinergia con {', '.join(syns)}")
                if len(reasons) == 1:
                    dmg = tags.get("damage", "mixed")
                    reasons.append(f"aporta daño {dmg} y balance sólido a tu composición")

                fallback_candidates.append({
                    "champion": champ_name,
                    "tier": self._score_to_tier(draft_score),
                    "tag": "Counter / Meta",
                    "draft_score": round(draft_score, 3),
                    "scores_breakdown": {
                        "player_comfort": round(comfort, 3),
                        "counter_value": round(counter_value, 3),
                        "team_synergy": round(synergy_value, 3),
                        "meta_strength": round(meta_value, 3),
                    },
                    "player_stats": {
                        "games": 0,
                        "win_rate": 0.0,
                        "avg_kda": 0.0,
                        "recent_form": 50.0,
                        "mastery_points": 0,
                    },
                    "setup": self._get_runes_and_spells(champ_name, role, enemy_picks),
                    "explanation": ". ".join(reasons) + ".",
                })

            fallback_candidates.sort(key=lambda x: x["draft_score"], reverse=True)
            needed = 5 - len(candidates)
            candidates.extend(fallback_candidates[:needed])

        candidates.sort(key=lambda x: x["draft_score"], reverse=True)
        top5 = candidates[:5]
        if (lang or "es").lower() != "es":
            for rec in top5:
                self._localize_rec_to_en(rec)
        return top5

    def get_coach_insights(
        self,
        player_analysis: dict[str, Any],
        ally_picks: list[str],
        enemy_picks: list[str],
        role: str,
        bans: list[str] | None = None,
        lang: str = "es",
    ) -> dict[str, Any]:
        """
        Genera consejos de Coach en tiempo real para el draft:
        - Qué banear (counters directos de tus mains en tu rol)
        - Cuándo pickear / si conviene pedir swap de turno
        - Alertas de composición (AP/AD, frontline, engage)
        - Mensaje listo para copiar y decirle a tus compañeros en el chat
        """
        champion_stats = player_analysis.get("champion_stats", {})
        already_taken = set(ally_picks + enemy_picks + (bans or []))
        role_lower = role.lower()

        # ── 1. Qué BANEAR: buscar los peores counters de tus mejores campeones del rol ──
        player_role_mains: list[str] = []
        for champ_name, stats in sorted(
            champion_stats.items(),
            key=lambda kv: (kv[1].get("games", 0), kv[1].get("win_rate", 0)),
            reverse=True,
        ):
            tags = CHAMPION_TAGS.get(champ_name, {})
            roles = [r.lower() for r in (tags.get("roles", []) if isinstance(tags, dict) else [])]
            played = stats.get("roles_played", [])
            if isinstance(played, dict):
                played = list(played.keys())
            if role_lower in roles or role_lower in [r.lower() for r in played]:
                player_role_mains.append(champ_name)

        ban_scores: dict[str, list[str]] = {}
        for main in player_role_mains[:3]:
            for threat in COUNTER_DATA.get(main, {}).get("countered_by", []):
                if threat not in already_taken:
                    ban_scores.setdefault(threat, []).append(main)

        recommended_bans: list[dict[str, str]] = []
        for threat, countered_mains in sorted(
            ban_scores.items(), key=lambda kv: len(kv[1]), reverse=True
        )[:3]:
            recommended_bans.append({
                "champion": threat,
                "reason": f"Countea duro a tu {', '.join(countered_mains)}",
            })

        # Fallback de bans por rol si el jugador no tiene mains cargados en ese rol
        if not recommended_bans:
            default_role_bans = {
                "top": [("Darius", "Muy opresivo en fase de líneas"), ("Jax", "Escala y domina 1v1")],
                "jg": [("LeeSin", "Presión temprana muy alta"), ("Viego", "Resets peligrosos en teamfight")],
                "mid": [("Zed", "Alta presión de asesinato en SoloQ"), ("Syndra", "Control de línea dominante")],
                "adc": [("Draven", "Snowball muy fuerte en early"), ("Caitlyn", "Abusa de rango en fase de líneas")],
                "sup": [("Nautilus", "Engage confiable y fácil de ejecutar"), ("Thresh", "Pick potencial y peel")],
            }
            for ch, why in default_role_bans.get(role_lower, []):
                if ch not in already_taken:
                    recommended_bans.append({"champion": ch, "reason": why})

        # ── 2. Análisis de composición del equipo aliado ──
        ad_count = 0
        ap_count = 0
        has_tank = False
        has_engage = False

        for ally in ally_picks:
            tags = CHAMPION_TAGS.get(ally, {})
            if not isinstance(tags, dict):
                continue
            dmg = tags.get("damage", "")
            if dmg == "AD":
                ad_count += 1
            elif dmg == "AP":
                ap_count += 1
            classes = [c.lower() for c in tags.get("class", [])]
            if "tank" in classes:
                has_tank = True
            if "tank" in classes or "fighter" in classes:
                has_engage = True

        team_alerts: list[dict[str, str]] = []
        chat_suggestions: list[str] = []

        if ad_count >= 3 and ap_count == 0:
            team_alerts.append({
                "type": "warning",
                "title": "Exceso de daño físico (Full AD)",
                "detail": f"Ya tienen {ad_count} campeones AD y 0 AP. El enemigo puede stackear armadura gratis.",
            })
            chat_suggestions.append("Gente estamos full AD, alguno puede pickear AP para balancear el daño?")
        elif ap_count >= 3 and ad_count == 0:
            team_alerts.append({
                "type": "warning",
                "title": "Exceso de daño mágico (Full AP)",
                "detail": f"Ya tienen {ap_count} campeones AP. Si arman Resistencia Mágica les va a costar bajar tanques.",
            })
            chat_suggestions.append("Estamos muy AP, nos vendría bien algo de daño AD sostenido.")
        elif len(ally_picks) >= 2:
            team_alerts.append({
                "type": "ok",
                "title": "Daño bien balanceado",
                "detail": f"Composición mixta ({ad_count} AD / {ap_count} AP). Difícil de itemizar para el rival.",
            })

        if len(ally_picks) >= 2 and not has_tank:
            team_alerts.append({
                "type": "warning",
                "title": "Falta Frontline / Tanque",
                "detail": "No hay un tanque claro en tu equipo. Las teamfights van a ser difíciles sin alguien que absorba daño.",
            })
            if not chat_suggestions:
                chat_suggestions.append("Nos falta un poco de frontline/engage para las TF, alguien juega tanque?")
        elif has_tank:
            team_alerts.append({
                "type": "ok",
                "title": "Buena Frontline",
                "detail": "Tienen presencia frontal para pelear objetivos y proteger a los carries.",
            })

        # ── 3. Consejo de Orden de Pick / Swap ──
        total_enemy = len(enemy_picks)
        if total_enemy == 0:
            if role_lower in ("top", "mid"):
                pick_order_advice = (
                    "Si te toca First Pick en Top/Mid, pedí swap de orden con ADC o Jungla para evitar "
                    "que te counterpickeen la línea. Si no te cambian, elegí un blind pick seguro."
                )
                if not chat_suggestions:
                    chat_suggestions.append("Alguien me cambia turno de pick así no me counterean línea?")
            else:
                pick_order_advice = (
                    "Estás en fase temprana del draft. Podés ofrecer swap a tu Top o Mid si quieren "
                    "pickear último, o asegurar tu main de confort antes de que te lo saquen."
                )
        elif total_enemy <= 2:
            pick_order_advice = (
                f"El rival ya mostró {total_enemy} pick(s) ({', '.join(enemy_picks)}). "
                "Evaluá si ya sabés tu matchup directo; si todavía falta tu rival de línea, priorizá seguridad o sinergia."
            )
        else:
            pick_order_advice = (
                f"Draft avanzado ({total_enemy} picks enemigos visibles). "
                "Es el momento ideal para cerrar con un counter directo o completar lo que le falta a tu composición."
            )

        if not chat_suggestions:
            chat_suggestions.append("Buena comp equipo, juguemos tranquilos por objetivos y teamfights!")

        # ── 4. Plan de Partida (Gameplan) + Evaluación Draft Diff / Dodge ──
        gameplan = self._build_gameplan(ally_picks, enemy_picks, role)
        draft_eval = self._evaluate_draft_diff(
            ally_picks, enemy_picks, bans or [], player_role_mains, ad_count, ap_count, has_tank, lang
        )

        payload = {
            "recommended_bans": recommended_bans[:3],
            "pick_order_advice": pick_order_advice,
            "team_alerts": team_alerts,
            "teammate_chat_tip": chat_suggestions[0],
            "gameplan": gameplan,
            "draft_eval": draft_eval,
        }
        if (lang or "es").lower() != "es":
            self._localize_coach_to_en(payload, ally_picks, enemy_picks)
        return payload

    def _evaluate_draft_diff(
        self,
        ally_picks: list[str],
        enemy_picks: list[str],
        bans: list[str],
        player_role_mains: list[str],
        ad_count: int,
        ap_count: int,
        has_tank: bool,
        lang: str = "es",
    ) -> dict[str, Any]:
        """Calcula ventaja de draft (Draft Diff %) y semáforo de Dodge."""
        is_en = (lang or "es").lower() != "es"
        score = 50  # Base 50/50

        # Penalizaciones / bonos de composición aliada
        if len(ally_picks) >= 2:
            if has_tank:
                score += 4
            else:
                score -= 5
            if (ad_count >= 3 and ap_count == 0) or (ap_count >= 3 and ad_count == 0):
                score -= 7
            elif ad_count >= 1 and ap_count >= 1:
                score += 4

        # Sinergias y counters entre equipos
        for a in ally_picks:
            syns = [s["champion"] for s in SYNERGY_DATA.get(a, [])]
            for a2 in ally_picks:
                if a2 in syns:
                    score += 3
            counters = COUNTER_DATA.get(a, {}).get("counters", [])
            countered_by = COUNTER_DATA.get(a, {}).get("countered_by", [])
            for e in enemy_picks:
                if e in counters:
                    score += 4
                if e in countered_by:
                    score -= 4

        # Penalización si te banearon o pickearon tu main #1
        main_taken = bool(player_role_mains and player_role_mains[0] in set(bans + enemy_picks))
        if main_taken:
            score -= 5

        ally_pct = max(32, min(68, score))
        enemy_pct = 100 - ally_pct

        if ally_pct >= 54:
            verdict = "play"
            label = "🟢 Favorable Draft" if is_en else "🟢 Draft Favorable"
        elif ally_pct <= 44:
            verdict = "dodge"
            label = "🔴 Tough Draft — Consider Dodge" if is_en else "🔴 Draft Cuesta Arriba — Evaluar Dodge"
        else:
            verdict = "even"
            label = "🟡 Even Draft" if is_en else "🟡 Draft Parejo"

        return {
            "ally_pct": ally_pct,
            "enemy_pct": enemy_pct,
            "verdict": verdict,
            "label": label,
        }

    def _build_gameplan(
        self,
        ally_picks: list[str],
        enemy_picks: list[str],
        role: str,
    ) -> dict[str, Any]:
        """
        Genera un plan táctico para jugar la partida (Win Condition, Early, Teamfights
        y Amenazas/Itemización) según las composiciones completas o avanzadas.
        """
        total_picks = len(ally_picks) + len(enemy_picks)
        is_complete = len(ally_picks) >= 4 and len(enemy_picks) >= 4

        if total_picks < 4:
            return {
                "ready": False,
                "is_complete": False,
                "status_label": f"Esperando picks ({total_picks}/10)",
                "win_condition": "Cuando se completen más picks del draft, el Coach va a armar tu plan de partida completo (Early, Teamfights y Amenazas).",
                "early_game": "",
                "teamfights": "",
                "itemization": "",
            }

        # Clasificar composiciones
        enemy_assassins: list[str] = []
        enemy_tanks: list[str] = []
        enemy_ap = 0
        enemy_ad = 0

        for e in enemy_picks:
            tags = CHAMPION_TAGS.get(e, {})
            if not isinstance(tags, dict):
                continue
            classes = [c.lower() for c in tags.get("class", [])]
            if "assassin" in classes:
                enemy_assassins.append(e)
            if "tank" in classes:
                enemy_tanks.append(e)
            dmg = tags.get("damage", "")
            if dmg == "AP":
                enemy_ap += 1
            elif dmg == "AD":
                enemy_ad += 1

        ally_tanks: list[str] = []
        ally_carries: list[str] = []
        for a in ally_picks:
            tags = CHAMPION_TAGS.get(a, {})
            if not isinstance(tags, dict):
                continue
            classes = [c.lower() for c in tags.get("class", [])]
            if "tank" in classes:
                ally_tanks.append(a)
            if "marksman" in classes or "mage" in classes:
                ally_carries.append(a)

        # Win condition
        if ally_tanks and ally_carries:
            win_condition = (
                f"Jugar alrededor de peleas 5v5 por objetivos (Dragón/Barón). "
                f"Tienen buena estructura con {', '.join(ally_tanks[:2])} adelante para dar espacio a sus carries."
            )
        elif enemy_assassins:
            win_condition = (
                f"Sobrevivir al burst/snowball de {', '.join(enemy_assassins[:2])} en mid game "
                "sin regalar ventajas aisladas; en 5v5 agrupados su comp pierde valor."
            )
        else:
            win_condition = (
                "Controlar la visión en el río antes de cada objetivo y forzar peleas con ventaja numérica "
                "o de cooldowns clave."
            )

        # Early Game
        if role.upper() == "ADC":
            if enemy_assassins:
                early_game = (
                    "Priorizá farm limpio y control de oleada cerca de tu torre. "
                    "Trackeá al jungla/mid rival para no quedar expuesto a ganks antes de tu primer ítem."
                )
            else:
                early_game = (
                    "Buscá ventaja de CS y prio en bot para rotar primero a Dragón. "
                    "Castigá el posicionamiento rival cuando gasten habilidades clave de línea."
                )
        elif role.upper() in ("TOP", "MID"):
            early_game = (
                "Manejá los timers de oleada para tener prio en Grubs/Dragón o castigar con placas si el rival roamea. "
                "Evitá peleas 1v1 sin información del jungla enemigo."
            )
        else:
            early_game = (
                "Identificá tu línea ganadora desde minuto 1 y jugá hacia ese lado del mapa para asegurar "
                "los primeros objetivos neutrales y visión profunda."
            )

        # Teamfights
        tf_parts: list[str] = []
        if enemy_assassins:
            tf_parts.append(
                f"Cuidado con los flancos de {', '.join(enemy_assassins[:2])}: no te regales sin visión y guardá tu herramienta defensiva/Flash hasta que entren."
            )
        if enemy_tanks:
            tf_parts.append(
                f"Peleá front-to-back golpeando primero a {', '.join(enemy_tanks[:2])} sin sobre-extenderte."
            )
        if ally_tanks:
            tf_parts.append(
                f"Esperá el engage o peel de {', '.join(ally_tanks[:2])} antes de comprometer tu posición."
            )
        if not tf_parts:
            tf_parts.append(
                "Mantené el espaciado (spacing) al límite de tu rango y focuseá al objetivo más cercano que puedas castigar de forma segura."
            )
        teamfights = " ".join(tf_parts)

        # Itemización / Amenazas
        item_parts: list[str] = []
        if len(enemy_tanks) >= 2:
            item_parts.append(
                f"Tienen {len(enemy_tanks)} tanques ({', '.join(enemy_tanks[:2])}): priorizá penetración (% armadura/MR) en 3er ítem."
            )
        if enemy_ap >= 3:
            item_parts.append(
                "Alto daño mágico enemigo (3+ AP): un ítem defensivo de MR (Fauces, Botas Mercurio o Velo) te va a dar muchísimo valor."
            )
        elif enemy_ad >= 3:
            item_parts.append(
                "Composición enemiga muy física (3+ AD): armadura temprana o Ángel Guardián rinde excelente."
            )
        if enemy_assassins and not item_parts:
            item_parts.append(
                f"Contra el burst de {', '.join(enemy_assassins[:2])}, considerá ítem defensivo (Zhonya / Ángel Guardián / Barredor de visión)."
            )
        if not item_parts:
            item_parts.append(
                "Armá tu core estándar priorizando tu spike de 2 ítems y comprá Control Wards antes de cada Barón/Dragón."
            )

        return {
            "ready": True,
            "is_complete": is_complete,
            "status_label": "Draft completo — Plan listo" if is_complete else f"Plan preliminar ({total_picks}/10 picks)",
            "win_condition": win_condition,
            "early_game": early_game,
            "teamfights": teamfights,
            "itemization": " ".join(item_parts),
        }

    def _get_runes_and_spells(
        self, champion: str, role: str, enemy_picks: list[str]
    ) -> dict[str, Any]:
        """
        Recomienda Hechizos de Invocador y Runas (Keystone + Ramas + consejo situacional)
        adaptados al campeón, rol y composición enemiga.
        """
        role_up = role.upper()
        tags = CHAMPION_TAGS.get(champion, {})
        classes = [c.lower() for c in (tags.get("class", []) if isinstance(tags, dict) else [])]

        heavy_cc_champs = {
            "Leona", "Nautilus", "Amumu", "Lissandra", "TwistedFate", "Ashe",
            "Lux", "Morgana", "Annie", "Sejuani", "Varus", "Thresh", "Rammus", "Maokai",
        }
        assassin_dive_champs = {
            "Zed", "Talon", "Khazix", "Rengar", "Akali", "Fizz", "Katarina",
            "Diana", "Evelynn", "Draven", "Samira", "Tristana", "Yone", "Yasuo",
        }

        enemy_cc = [e for e in enemy_picks if e in heavy_cc_champs]
        enemy_dive = [e for e in enemy_picks if e in assassin_dive_champs]

        # ── 1. Hechizos de Invocador ──
        if role_up == "JG":
            if champion in {"Hecarim", "Udyr", "Mordekaiser"}:
                spells = ["Fantasmal (Ghost)", "Aplastar (Smite)"]
                spell_reason = "Movilidad sostenida para ganks y teamfights."
            else:
                spells = ["Destello (Flash)", "Aplastar (Smite)"]
                spell_reason = "Estándar de jungla para asegurar objetivos y jugadas."
        elif role_up == "ADC":
            if len(enemy_cc) >= 2 or any(e in {"Leona", "Ashe", "Lissandra", "TwistedFate"} for e in enemy_cc):
                spells = ["Destello (Flash)", "Limpiar (Cleanse)"]
                spell_reason = f"Clave para salir del CC de {', '.join(enemy_cc[:2])}."
            elif len(enemy_dive) >= 2:
                spells = ["Destello (Flash)", "Extenuar (Exhaust)"]
                spell_reason = f"Frena el burst de {', '.join(enemy_dive[:2])} cuando te salten."
            else:
                spells = ["Destello (Flash)", "Barrera (Barrier)"]
                spell_reason = "Mejor supervivencia en intercambios 2v2 y teamfights."
        elif role_up == "TOP":
            if champion in {"Darius", "Garen", "Mordekaiser", "Tryndamere"}:
                spells = ["Destello (Flash)", "Fantasmal (Ghost)"]
                spell_reason = "Te permite correr y kitear/perseguir en línea larga."
            else:
                spells = ["Destello (Flash)", "Teleportación (TP)"]
                spell_reason = "Control de oleadas, presión en splitpush y presencia en objetivos."
        elif role_up == "MID":
            if any(e in {"Lissandra", "TwistedFate", "Annie", "Lux", "Ahri"} for e in enemy_cc):
                spells = ["Destello (Flash)", "Limpiar (Cleanse)"]
                spell_reason = f"Neutraliza el pick/CC de {', '.join(enemy_cc[:2])}."
            elif "assassin" in classes:
                spells = ["Destello (Flash)", "Prender (Ignite)"]
                spell_reason = "Presión de kill en línea y snowball temprano."
            else:
                spells = ["Destello (Flash)", "Teleportación (TP)"]
                spell_reason = "Tempo de línea y rotaciones rápidas al mapa."
        else:  # SUP
            if len(enemy_dive) >= 1:
                spells = ["Destello (Flash)", "Extenuar (Exhaust)"]
                spell_reason = f"Protege a tu carry del burst de {', '.join(enemy_dive[:2])}."
            else:
                spells = ["Destello (Flash)", "Prender (Ignite)"]
                spell_reason = "Presión de kill en 2v2 y corta curaciones."

        # ── 2. Runas por campeón específico o por clase ──
        specific_runes: dict[str, tuple[str, str, str]] = {
            "Jinx": ("Compás Letal", "Precisión", "Inspiración"),
            "Jhin": ("Pies Veloces", "Precisión", "Brujería"),
            "Ezreal": ("Ataque Intensificado", "Precisión", "Inspiración"),
            "Caitlyn": ("Pies Veloces", "Precisión", "Inspiración"),
            "Kaisa": ("Compás Letal", "Precisión", "Inspiración"),
            "Lucian": ("Ataque Intensificado", "Precisión", "Inspiración"),
            "Vayne": ("Compás Letal", "Precisión", "Valor"),
            "Draven": ("Ataque Intensificado", "Precisión", "Dominación"),
            "MissFortune": ("Ataque Intensificado", "Precisión", "Brujería"),
            "Sivir": ("Compás Letal", "Precisión", "Brujería"),
            "Tristana": ("Ataque Intensificado", "Precisión", "Inspiración"),
            "Twitch": ("Compás Letal", "Precisión", "Dominación"),
            "Ashe": ("Compás Letal", "Precisión", "Inspiración"),
            "Ahri": ("Electrocutar", "Dominación", "Brujería"),
            "Syndra": ("Primer Golpe", "Inspiración", "Brujería"),
            "Orianna": ("Invocar a Aery", "Brujería", "Inspiración"),
            "Lux": ("Cometa Arcano", "Brujería", "Inspiración"),
            "Zed": ("Electrocutar", "Dominación", "Brujería"),
            "Yasuo": ("Compás Letal", "Precisión", "Valor"),
            "Yone": ("Compás Letal", "Precisión", "Valor"),
            "Aatrox": ("Conquistador", "Precisión", "Valor"),
            "Darius": ("Conquistador", "Precisión", "Valor"),
            "Malphite": ("Cometa Arcano", "Brujería", "Valor"),
            "Vladimir": ("Irrupción de Fase", "Brujería", "Inspiración"),
            "Thresh": ("Réplica", "Valor", "Inspiración"),
            "Nautilus": ("Réplica", "Valor", "Inspiración"),
            "Leona": ("Réplica", "Valor", "Inspiración"),
            "Braum": ("Guardián", "Valor", "Inspiración"),
            "Lulu": ("Invocar a Aery", "Brujería", "Inspiración"),
        }

        if champion in specific_runes:
            keystone, primary, secondary = specific_runes[champion]
        elif "marksman" in classes:
            keystone, primary, secondary = ("Compás Letal", "Precisión", "Inspiración")
        elif "assassin" in classes:
            keystone, primary, secondary = ("Electrocutar", "Dominación", "Brujería")
        elif "tank" in classes:
            keystone, primary, secondary = (
                ("Réplica", "Valor", "Inspiración")
                if role_up in ("SUP", "JG")
                else ("Agarre del Perpetuo", "Valor", "Inspiración")
            )
        elif "fighter" in classes:
            keystone, primary, secondary = ("Conquistador", "Precisión", "Valor")
        elif "mage" in classes:
            keystone, primary, secondary = ("Cometa Arcano", "Brujería", "Inspiración")
        else:
            keystone, primary, secondary = ("Invocar a Aery", "Brujería", "Inspiración")

        # Consejo situacional de runas menores
        if enemy_dive:
            rune_tip = "Considerá Huesos Revestidos (Valor) o fragmento de Vida escalable contra el burst enemigo."
        elif enemy_cc:
            rune_tip = "Llevá Inquebrantable o fragmento de Tenacidad para reducir el CC enemigo."
        else:
            rune_tip = "Llevá fragmentos ofensivos estándar (Velocidad de Ataque / Fuerza Adaptable + Vida)."

        return {
            "spells": spells,
            "spell_reason": spell_reason,
            "keystone": keystone,
            "primary_tree": primary,
            "secondary_tree": secondary,
            "rune_tip": rune_tip,
        }

    def _calc_counter_value(
        self, champion: str, enemy_picks: list[str]
    ) -> float:
        """Calcula qué tan bien countea este campeón a los picks enemigos."""
        if not enemy_picks:
            return 0.5  # neutral si no hay enemigos

        counter_score = 0.0
        relevant = 0

        champ_counters = COUNTER_DATA.get(champion, {})
        counters_list = champ_counters.get("counters", [])
        countered_by_list = champ_counters.get("countered_by", [])

        for enemy in enemy_picks:
            if enemy in counters_list:
                counter_score += 1.0
                relevant += 1
            elif enemy in countered_by_list:
                counter_score -= 0.5
                relevant += 1

            # También revisar si el enemigo tiene datos de counter
            enemy_data = COUNTER_DATA.get(enemy, {})
            if champion in enemy_data.get("countered_by", []):
                counter_score += 0.5
                relevant += 1

        if relevant == 0:
            return 0.5

        # Normalizar entre 0 y 1
        normalized = (counter_score / relevant + 1) / 2
        return max(0.0, min(1.0, normalized))

    def _calc_synergy_value(
        self, champion: str, ally_picks: list[str]
    ) -> float:
        """Calcula la sinergia con los aliados ya pickeados."""
        if not ally_picks:
            return 0.5

        synergy_count = 0
        champ_synergies = SYNERGY_DATA.get(champion, [])
        synergy_names = [s["champion"] for s in champ_synergies]

        for ally in ally_picks:
            if ally in synergy_names:
                synergy_count += 1
            # Revisar sinergia bidireccional
            ally_synergies = SYNERGY_DATA.get(ally, [])
            if champion in [s["champion"] for s in ally_synergies]:
                synergy_count += 1

        # Normalizar: 0 sinergias → 0.3, 1+ → escala hasta 1.0
        return min(0.3 + synergy_count * 0.35, 1.0)

    def _calc_meta_value(
        self, champion: str, ally_picks: list[str], enemy_picks: list[str]
    ) -> float:
        """
        Evalúa la fortaleza meta del campeón en el contexto del draft.
        Considera balance de tipos de daño y composición del equipo.
        """
        champ_tags = CHAMPION_TAGS.get(champion, {})
        if not isinstance(champ_tags, dict):
            return 0.5

        champ_damage = champ_tags.get("damage", "mixed")
        champ_classes = champ_tags.get("class", [])

        # Analizar daño del equipo aliado
        team_ad = 0
        team_ap = 0
        for ally in ally_picks:
            ally_tags = CHAMPION_TAGS.get(ally, {})
            if isinstance(ally_tags, dict):
                dmg = ally_tags.get("damage", "mixed")
                if dmg == "AD":
                    team_ad += 1
                elif dmg == "AP":
                    team_ap += 1
                else:
                    team_ad += 0.5
                    team_ap += 0.5

        # Bonificar si balancea el tipo de daño del equipo
        balance_bonus = 0.0
        if team_ad > team_ap and champ_damage == "AP":
            balance_bonus = 0.3
        elif team_ap > team_ad and champ_damage == "AD":
            balance_bonus = 0.3
        elif team_ad == team_ap:
            balance_bonus = 0.1

        # Bonificar roles importantes que faltan (tank, engage)
        team_has_tank = any(
            "tank" in CHAMPION_TAGS.get(a, {}).get("class", [])
            for a in ally_picks
            if isinstance(CHAMPION_TAGS.get(a, {}), dict)
        )
        tank_bonus = 0.2 if not team_has_tank and "tank" in champ_classes else 0.0

        return min(0.3 + balance_bonus + tank_bonus, 1.0)

    def _generate_explanation(
        self,
        champion: str,
        stats: dict[str, Any],
        comfort: float,
        counter_value: float,
        synergy_value: float,
        meta_value: float,
        ally_picks: list[str],
        enemy_picks: list[str],
    ) -> str:
        """Genera una explicación en español de por qué se recomienda el campeón."""
        parts: list[str] = []

        # Comodidad del jugador
        wr = stats.get("win_rate", 50.0)
        games = stats.get("games", 0)
        if wr >= 55:
            parts.append(
                f"Tenés un gran rendimiento con {champion} "
                f"({wr}% WR en {games} partidas)"
            )
        else:
            parts.append(
                f"Jugás {champion} con {wr}% WR "
                f"en {games} partidas"
            )

        # Recent form
        recent_form = stats.get("recent_form", 50.0)
        if recent_form >= 60:
            parts.append("y estás en buena racha reciente")

        # Counters
        if counter_value > 0.65 and enemy_picks:
            countered_enemies: list[str] = []
            champ_counters = COUNTER_DATA.get(champion, {}).get("counters", [])
            for enemy in enemy_picks:
                if enemy in champ_counters:
                    countered_enemies.append(enemy)
            if countered_enemies:
                parts.append(f"Countea a {', '.join(countered_enemies)}")

        # Sinergias
        if synergy_value > 0.5 and ally_picks:
            synergy_allies: list[str] = []
            champ_syn = SYNERGY_DATA.get(champion, [])
            syn_names = [s["champion"] for s in champ_syn]
            for ally in ally_picks:
                if ally in syn_names:
                    synergy_allies.append(ally)
            if synergy_allies:
                parts.append(f"Tiene sinergia con {', '.join(synergy_allies)}")

        # Balance de equipo
        if meta_value > 0.6:
            parts.append("Ayuda a balancear la composición del equipo")

        return ". ".join(parts) + "."


    # ── Localización al Inglés (Audiencia Global NA / EUW) ───────────

    def _localize_analysis_to_en(self, result: dict[str, Any]) -> None:
        summary = result.get("player_summary", {})
        if summary.get("tier") == "Sin clasificar":
            summary["tier"] = "Unranked"
        pd = summary.get("pool_depth", "")
        if pd.startswith("Especialista ("):
            summary["pool_depth"] = pd.replace("Especialista (", "Specialist (")
        elif "Enfocado" in pd:
            summary["pool_depth"] = "Focused (2-3 mains)"
        elif pd == "Moderado":
            summary["pool_depth"] = "Balanced"
        elif "Amplio" in pd:
            summary["pool_depth"] = "Wide (versatile)"

        mc = result.get("mental_check")
        if not isinstance(mc, dict):
            return
        status = mc.get("status", "ok")
        sl = mc.get("streak_label", "")
        mc["streak_label"] = sl.replace("V seguidas", "W streak").replace("D seguidas", "L streak")
        if status == "break":
            mc["title"] = "⏸️ Take a short break (Tilt Alert)"
            mc["message"] = random.choice([
                "Rough loss streak. Step away for 15 minutes, grab some water, touch grass, and come back fresh to carry.",
                "Your LP is asking for a breather. Take a 20-minute reset before queueing again.",
                "Fatigue shows up fast after consecutive losses. A short break now saves LP later.",
            ])
        elif status == "caution":
            mc["title"] = "🟡 Watch the streak — Play your comfort"
            mc["message"] = "A couple of tough games recently. Lock in your highest-comfort pick and play calm early."
        elif status == "hot":
            mc["title"] = f"🔥 On fire ({mc['streak_label']})"
            mc["message"] = f"You're playing super clean ({mc['streak_label']}). Great momentum to keep climbing!"
        else:
            mc["title"] = "🟢 Ready to queue"
            mc["message"] = "Recent performance looks steady with zero signs of tilt. Good luck on the Rift!"

        en_mistakes = []
        for m in mc.get("mistakes", []):
            title = m.get("title", "")
            if "Control Wards" in title:
                en_mistakes.append({
                    "icon": "👁️",
                    "title": "Low Control Ward purchases",
                    "detail": "Buying 1–2 Control Wards before Drake/Baron drastically cuts down flank and gank deaths.",
                })
            elif "muertes" in title.lower():
                en_mistakes.append({
                    "icon": "💀",
                    "title": "High deaths when playing from behind",
                    "detail": "Your deaths spike in losses. Avoid forcing fights without vision when behind.",
                })
            elif "farmeo" in title.lower():
                en_mistakes.append({
                    "icon": "🌾",
                    "title": "Room to improve CS/min",
                    "detail": "Catching side waves cleanly in mid game gives you an extra item spike.",
                })
            elif "pool" in title.lower():
                en_mistakes.append({
                    "icon": "🎯",
                    "title": "LP lost outside your main pool",
                    "detail": "Sticking to your highest-mastery champions yields a much stronger win rate.",
                })
            else:
                en_mistakes.append({
                    "icon": "✅",
                    "title": "Very solid fundamentals",
                    "detail": "Deaths, vision, and farming have been super consistent in recent games!",
                })
        mc["mistakes"] = en_mistakes

    def _localize_rec_to_en(self, rec: dict[str, Any]) -> None:
        tag = rec.get("tag", "")
        if tag == "Tu Main":
            rec["tag"] = "Your Main"
        elif tag == "Pool Reciente":
            rec["tag"] = "Recent Pool"
        elif tag.startswith("Maestría "):
            rec["tag"] = tag.replace("Maestría ", "Mastery ")

        # Traducir explicación
        ps = rec.get("player_stats", {})
        champ = rec.get("champion", "")
        games = ps.get("games", 0)
        wr = ps.get("win_rate", 0)
        parts = []
        if games > 0:
            parts.append(f"Strong personal record on {champ} ({wr}% WR in {games} games)")
        elif ps.get("mastery_points", 0) >= 20000:
            parts.append(f"High mastery comfort pick ({ps['mastery_points'] // 1000}k pts)")
        else:
            parts.append("Strategic role pick for this draft")

        bd = rec.get("scores_breakdown", {})
        if bd.get("counter_value", 0) > 0.6:
            parts.append("favorable matchup into enemy picks")
        if bd.get("team_synergy", 0) > 0.55:
            parts.append("great synergy with your allies")
        if bd.get("meta_strength", 0) > 0.6:
            parts.append("balances team composition well")
        rec["explanation"] = ". ".join(parts) + "."

        # Traducir hechizos y runas
        setup = rec.get("setup")
        if not isinstance(setup, dict):
            return
        spell_en = {
            "Destello (Flash)": "Flash", "Barrera (Barrier)": "Barrier",
            "Limpiar (Cleanse)": "Cleanse", "Extenuar (Exhaust)": "Exhaust",
            "Prender (Ignite)": "Ignite", "Teleportación (TP)": "Teleport",
            "Fantasmal (Ghost)": "Ghost", "Aplastar (Smite)": "Smite",
        }
        setup["spells"] = [spell_en.get(s, s) for s in setup.get("spells", [])]
        if "Limpiar" in setup.get("spell_reason", "") or "CC" in setup.get("spell_reason", ""):
            setup["spell_reason"] = "Key for cleansing heavy enemy CC."
        elif "burst" in setup.get("spell_reason", "").lower():
            setup["spell_reason"] = "Shuts down enemy dive and burst threats."
        else:
            setup["spell_reason"] = "Optimal standard summoner setup for this role."

        ks_en = {
            "Compás Letal": "Lethal Tempo", "Pies Veloces": "Fleet Footwork",
            "Ataque Intensificado": "Press the Attack", "Conquistador": "Conqueror",
            "Electrocutar": "Electrocute", "Cometa Arcano": "Arcane Comet",
            "Invocar a Aery": "Summon Aery", "Irrupción de Fase": "Phase Rush",
            "Primer Golpe": "First Strike", "Réplica": "Aftershock",
            "Agarre del Perpetuo": "Grasp of the Undying", "Guardián": "Guardian",
        }
        tree_en = {
            "Precisión": "Precision", "Dominación": "Domination",
            "Brujería": "Sorcery", "Valor": "Resolve", "Inspiración": "Inspiration",
        }
        setup["keystone"] = ks_en.get(setup.get("keystone", ""), setup.get("keystone", ""))
        setup["primary_tree"] = tree_en.get(setup.get("primary_tree", ""), setup.get("primary_tree", ""))
        setup["secondary_tree"] = tree_en.get(setup.get("secondary_tree", ""), setup.get("secondary_tree", ""))
        if "CC" in setup.get("rune_tip", ""):
            setup["rune_tip"] = "Take Unflinching / Tenacity shard against enemy CC."
        elif "burst" in setup.get("rune_tip", "").lower():
            setup["rune_tip"] = "Consider Bone Plating or scaling HP against enemy burst."
        else:
            setup["rune_tip"] = "Standard offensive shards (Attack Speed / Adaptive + HP)."

    def _localize_coach_to_en(
        self, payload: dict[str, Any], ally_picks: list[str], enemy_picks: list[str]
    ) -> None:
        for b in payload.get("recommended_bans", []):
            r = b.get("reason", "")
            if "Countea duro a tu " in r:
                b["reason"] = r.replace("Countea duro a tu ", "Hard counters your ")
            else:
                b["reason"] = "High solo-queue threat in your lane"

        n_enemy = len(enemy_picks)
        if n_enemy == 0:
            payload["pick_order_advice"] = (
                "Early draft phase. Offer a pick-order swap if your Top/Mid wants last pick, "
                "or lock in your safest blind-pick main."
            )
        elif n_enemy <= 2:
            payload["pick_order_advice"] = (
                f"Enemy showed {n_enemy} pick(s) ({', '.join(enemy_picks)}). "
                "Check if your lane matchup is revealed; otherwise prioritize comfort or synergy."
            )
        else:
            payload["pick_order_advice"] = (
                f"Late draft ({n_enemy} enemy picks revealed). Great spot to lock a direct counter "
                "or fill what your team composition needs."
            )

        en_alerts = []
        for a in payload.get("team_alerts", []):
            t_str = a.get("title", "")
            if "Full AD" in t_str:
                en_alerts.append({"type": "warning", "title": "Heavy Physical Damage (Full AD)", "detail": "Your team lacks magic damage — enemies can stack armor easily."})
            elif "Full AP" in t_str:
                en_alerts.append({"type": "warning", "title": "Heavy Magic Damage (Full AP)", "detail": "Your team lacks sustained AD — enemies can stack Magic Resist."})
            elif "Frontline" in t_str and a.get("type") == "warning":
                en_alerts.append({"type": "warning", "title": "Missing Frontline / Tank", "detail": "No dedicated tank on your team. Teamfights will require careful spacing."})
            elif "Frontline" in t_str:
                en_alerts.append({"type": "ok", "title": "Solid Frontline", "detail": "Good frontline presence to contest objectives and peel for carries."})
            else:
                en_alerts.append({"type": "ok", "title": "Balanced Damage Profile", "detail": "Mixed AD/AP damage makes itemizing tough for the enemy team."})
        payload["team_alerts"] = en_alerts

        chat = payload.get("teammate_chat_tip", "")
        if "full AD" in chat:
            payload["teammate_chat_tip"] = "Hey team, we're full AD — can anyone go AP?"
        elif "muy AP" in chat:
            payload["teammate_chat_tip"] = "We're heavy AP, some sustained AD would help a lot!"
        elif "frontline" in chat:
            payload["teammate_chat_tip"] = "We could use some frontline/engage for teamfights, anyone play tank?"
        elif "cambia turno" in chat:
            payload["teammate_chat_tip"] = "Can anyone swap pick order so I don't get counterpicked?"
        else:
            payload["teammate_chat_tip"] = "Great comp team, let's play around objectives and teamfights!"

        gp = payload.get("gameplan", {})
        if gp:
            if not gp.get("ready"):
                gp["status_label"] = f"Waiting for picks ({len(ally_picks) + len(enemy_picks)}/10)"
                gp["win_condition"] = "Once more draft picks lock in, RiftMind will build your full in-game plan (Early, Teamfights & Itemization)."
            else:
                gp["status_label"] = "Draft complete — Gameplan ready" if gp.get("is_complete") else f"Early plan ({len(ally_picks) + len(enemy_picks)}/10 picks)"
                gp["win_condition"] = "Play around 5v5 objective fights (Drake/Baron) and leverage your team's core scaling and engage."
                gp["early_game"] = "Focus on clean wave management, early CS lead, and tracking the enemy jungler before your first item spike."
                gp["teamfights"] = "Play front-to-back, respect enemy flanks/assassins, and hold your defensive cooldowns until key enemy threats commit."
                gp["itemization"] = "Build your core 2-item spike, adapt with % penetration vs tanks or defensive MR/Armor vs heavy single-damage comps."


    # ── Némesis, Víctima Favorita, Mejor Aliado y Fun Facts Reales ────

    def _build_fun_facts(
        self, match_history: list[dict[str, Any]], puuid: str, lang: str = "es"
    ) -> dict[str, Any]:
        """Extrae Némesis, Víctima Favorita, Mejor Aliado y datos curiosos de las partidas."""
        is_en = (lang or "es").lower() != "es"
        vs_enemy: dict[str, list[bool]] = {}
        with_ally: dict[str, list[bool]] = {}

        total_seconds = 0
        total_damage = 0
        total_cs = 0
        pentas = 0
        quadras = 0
        triples = 0
        max_spree = 0
        max_spree_champ = ""
        longest_sec = 0
        shortest_win_sec = 999999

        for match in match_history:
            info = match.get("info", {})
            participants = info.get("participants", [])
            duration = int(info.get("gameDuration", 0) or 0)
            if duration < 300:
                continue  # Ignorar remakes

            me = None
            for p in participants:
                if p.get("puuid") == puuid:
                    me = p
                    break
            if not me:
                continue

            won = bool(me.get("win", False))
            my_team = me.get("teamId", 100)
            total_seconds += duration
            if duration > longest_sec:
                longest_sec = duration
            if won and duration < shortest_win_sec:
                shortest_win_sec = duration

            total_damage += int(me.get("totalDamageDealtToChampions", 0) or 0)
            total_cs += int(me.get("totalMinionsKilled", 0) or 0) + int(
                me.get("neutralMinionsKilled", 0) or 0
            )
            pentas += int(me.get("pentaKills", 0) or 0)
            quadras += int(me.get("quadraKills", 0) or 0)
            triples += int(me.get("tripleKills", 0) or 0)

            spree = int(me.get("largestKillingSpree", 0) or 0)
            if spree > max_spree:
                max_spree = spree
                max_spree_champ = me.get("championName", "")

            for p in participants:
                if p.get("puuid") == puuid:
                    continue
                cname = p.get("championName", "")
                if not cname:
                    continue
                if p.get("teamId") == my_team:
                    with_ally.setdefault(cname, []).append(won)
                else:
                    vs_enemy.setdefault(cname, []).append(won)

        def _pick_extreme(table: dict[str, list[bool]], highest: bool, min_games: int = 4) -> dict[str, Any] | None:
            eligible = [
                (ch, res, sum(1 for r in res if r) / len(res) * 100.0)
                for ch, res in table.items()
                if len(res) >= min_games
            ]
            if not eligible:
                eligible = [
                    (ch, res, sum(1 for r in res if r) / len(res) * 100.0)
                    for ch, res in table.items()
                    if len(res) >= 2
                ]
            if not eligible:
                return None
            eligible.sort(key=lambda x: (x[2], len(x[1])) if highest else (-x[2], len(x[1])), reverse=True)
            ch, res, wr = eligible[0]
            wins = sum(1 for r in res if r)
            return {
                "champion": ch,
                "games": len(res),
                "wins": wins,
                "losses": len(res) - wins,
                "win_rate": round(wr, 1),
            }

        nemesis = _pick_extreme(vs_enemy, highest=False)
        victim = _pick_extreme(vs_enemy, highest=True)
        best_ally = _pick_extreme(with_ally, highest=True)

        hours = round(total_seconds / 3600.0, 1)
        dmg_m = round(total_damage / 1_000_000.0, 2)
        cs_k = round(total_cs / 1000.0, 1)
        longest_str = f"{longest_sec // 60}:{longest_sec % 60:02d}"
        fastest_str = f"{shortest_win_sec // 60}:{shortest_win_sec % 60:02d}" if shortest_win_sec < 999999 else "—"

        records: list[dict[str, str]] = [
            {
                "icon": "⏱️",
                "value": f"{hours}h",
                "label": "Time on the Rift" if is_en else "Horas en la Grieta",
                "sub": f"{'Longest' if is_en else 'Más larga'}: {longest_str} · {'Fastest W' if is_en else 'Victoria rápida'}: {fastest_str}",
            },
            {
                "icon": "💥",
                "value": f"{dmg_m}M",
                "label": "Total Champion Damage" if is_en else "Daño Total a Campeones",
                "sub": f"{cs_k}k {'minions farmed' if is_en else 'súbditos farmeados'}",
            },
            {
                "icon": "🔥",
                "value": f"{max_spree} kills",
                "label": "Best Killing Spree" if is_en else "Mejor Racha sin Morir",
                "sub": f"{'with' if is_en else 'con'} {max_spree_champ}" if max_spree_champ else "—",
            },
            {
                "icon": "🏆",
                "value": f"{pentas}P · {quadras}Q · {triples}T",
                "label": "Multikills",
                "sub": "Penta · Quadra · Triple",
            },
        ]

        return {
            "nemesis": nemesis,
            "victim": victim,
            "best_ally": best_ally,
            "records": records,
        }
