"""
Reconocimiento y parseo de comandos de voz para el Mini-HUD de NoFlash.
Detecta principalmente:
  - Ulti (R): "Mid sin ulti", "Ahri no R", "Jinx ulteó", "Sin ulti" (rival de línea)
  - Summoners: "Mid no flash", "ADC sin flash", "Top TP", "Supp exhaust", "No flash"
  - Ambos summoners: "ADC sin summs", "Bot sin summoners", "Mid gastó todo"
Ignora conversaciones normales (Discord) si no contienen un trigger válido.
"""

from __future__ import annotations

import io
import logging
import re
import unicodedata
from typing import Any, Optional

logger = logging.getLogger(__name__)

# Cooldowns base aproximados de Ulti (R) por rango [Lv6-10, Lv11-15, Lv16+]
ULT_COOLDOWNS: dict[str, tuple[int, int, int]] = {
    "karthus": (200, 180, 160),
    "shen": (200, 180, 160),
    "galio": (180, 160, 140),
    "twistedfate": (170, 140, 110),
    "pantheon": (180, 165, 150),
    "nocturne": (140, 115, 90),
    "soraka": (150, 135, 120),
    "taric": (180, 150, 120),
    "kayle": (160, 120, 80),
    "kindred": (160, 140, 120),
    "zilean": (120, 90, 60),
    "malphite": (130, 105, 80),
    "amumu": (150, 125, 100),
    "orianna": (110, 95, 80),
    "ahri": (130, 115, 100),
    "syndra": (120, 100, 80),
    "zed": (120, 100, 80),
    "yasuo": (70, 50, 30),
    "yone": (120, 100, 80),
    "darius": (120, 100, 80),
    "garen": (120, 100, 80),
    "mordekaiser": (140, 120, 100),
    "sett": (120, 100, 80),
    "aatrox": (120, 100, 80),
    "camille": (140, 115, 90),
    "jax": (110, 100, 90),
    "fiora": (110, 90, 70),
    "renekton": (120, 100, 80),
    "jinx": (85, 65, 45),
    "caitlyn": (90, 90, 90),
    "ashe": (100, 80, 60),
    "ezreal": (120, 105, 90),
    "kaisa": (130, 100, 70),
    "missfortune": (120, 110, 100),
    "jhin": (120, 105, 90),
    "lucian": (110, 100, 90),
    "vayne": (100, 85, 70),
    "xayah": (140, 120, 100),
    "samira": (5, 5, 5),
    "thresh": (140, 120, 100),
    "nautilus": (120, 100, 80),
    "leona": (90, 75, 60),
    "blitzcrank": (60, 45, 30),
    "lulu": (120, 100, 80),
    "janna": (130, 115, 100),
    "nami": (120, 110, 100),
    "lux": (60, 50, 40),
    "morgana": (120, 110, 100),
    "leesin": (110, 85, 60),
    "viego": (120, 100, 80),
    "vi": (140, 115, 90),
    "jarvaniv": (120, 105, 90),
    "hecarim": (140, 120, 100),
    "amumu": (150, 125, 100),
    "ekko": (110, 80, 50),
    "fizz": (100, 85, 70),
    "katarina": (90, 60, 45),
    "akali": (100, 80, 60),
    "sylas": (80, 55, 30),
    "viktor": (120, 100, 80),
    "veigar": (100, 80, 60),
    "annie": (130, 115, 100),
    "brand": (105, 90, 75),
    "zyra": (110, 100, 90),
    "pyke": (100, 85, 70),
    "rakan": (130, 110, 90),
    "alistar": (120, 100, 80),
    "braum": (130, 110, 90),
    "renata": (150, 130, 110),
    "milio": (160, 145, 130),
}


def get_ult_cooldown(champion: str, level: int = 6) -> int:
    """Devuelve el cooldown base estimado de la R del campeón según su nivel actual."""
    key = re.sub(r"[^a-z0-9]", "", (champion or "").lower())
    cds = ULT_COOLDOWNS.get(key, (110, 95, 80))
    if level >= 16:
        return cds[2]
    if level >= 11:
        return cds[1]
    return cds[0]


# Sinónimos de roles (ES + EN + fonética común)
ROLE_ALIASES: dict[str, list[str]] = {
    "TOP": ["top", "toplaner", "top laner", "arriba", "el top", "la top"],
    "JUNGLE": ["jg", "jng", "jungla", "jungle", "jungler", "selva", "el jg", "la jungla"],
    "MIDDLE": ["mid", "medio", "midlaner", "mid laner", "el mid", "la mid", "mit"],
    "BOTTOM": ["adc", "ad", "bot", "tirador", "carry", "ad carry", "el adc", "la adc", "a de ce"],
    "UTILITY": ["sup", "supp", "support", "soporte", "apoyo", "suport", "el sup", "la sup"],
}

# Triggers de "ambos summoners" (D + F)
ALL_SUMMS_ALIASES: list[str] = [
    "sin summs", "no summs", "sin sums", "no sums",
    "sin summoners", "no summoners", "sin hechizos", "no hechizos",
    "gasto todo", "tiro todo", "no tiene nada", "sin nada",
]

# Triggers de Ulti (R)
ULTI_ALIASES: list[str] = [
    "no ulti", "sin ulti", "no ult", "sin ult", "no ultimate", "sin ultimate",
    "no r", "sin r", "no erre", "sin erre",
    "tiro ulti", "gasto ulti", "tiro r", "gasto r", "uso ulti", "uso r",
    "ulteo", "ultio", "ulti", "ult", "r",
]

# Sinónimos de Summoner Spells -> dd_key oficial de Data Dragon
SPELL_ALIASES: list[tuple[str, list[str]]] = [
    ("SummonerFlash", [
        "no flash", "sin flash", "flash", "flasheo", "flashe", "flashea",
        "destello", "sin destello", "no destello", "gasto flash", "tiro flash",
        "no f", "sin f", "f",
    ]),
    ("SummonerTeleport", [
        "tp", "tepe", "teleport", "teletransportacion", "teletransporte", "no tp", "sin tp",
    ]),
    ("SummonerDot", [
        "ignite", "ignit", "prender", "no ignite", "sin ignite", "prendio",
    ]),
    ("SummonerExhaust", [
        "exhaust", "exaust", "extenuar", "extenuacion", "no exhaust", "sin exhaust",
    ]),
    ("SummonerBarrier", [
        "barrier", "barrera", "escudo", "no barrier", "sin barrier",
    ]),
    ("SummonerHeal", [
        "heal", "curar", "curacion", "no heal", "sin heal",
    ]),
    ("SummonerBoost", [
        "cleanse", "clens", "limpiar", "purificar", "no cleanse", "sin cleanse",
    ]),
    ("SummonerHaste", [
        "ghost", "fantasmal", "fantasma", "no ghost", "sin ghost",
    ]),
    ("SummonerSmite", [
        "smite", "aplastar", "no smite", "sin smite",
    ]),
]

# Abreviaturas populares de campeones en voz (ES/EN)
CHAMP_NICKNAMES: dict[str, str] = {
    "mf": "missfortune", "tf": "twistedfate", "lee": "leesin", "yi": "masteryi",
    "mundo": "drmundo", "cait": "caitlyn", "ez": "ezreal", "ezre": "ezreal",
    "kaisa": "kaisa", "kai sa": "kaisa", "kha": "khazix", "cho": "chogath",
    "kog": "kogmaw", "vel": "velkoz", "rek": "reksai", "bel": "belveth",
    "j4": "jarvaniv", "jarvan": "jarvaniv", "wu": "monkeyking", "wukong": "monkeyking",
    "mono": "monkeyking", "xin": "xinzhao", "tahm": "tahmkench", "kench": "tahmkench",
    "asol": "aurelionsol", "aurelion": "aurelionsol", "morg": "morgana",
    "kat": "katarina", "kata": "katarina", "cass": "cassiopeia", "cassio": "cassiopeia",
    "malph": "malphite", "malza": "malzahar", "morde": "mordekaiser",
    "naut": "nautilus", "blitz": "blitzcrank", "trist": "tristana", "ori": "orianna",
    "gp": "gangplank", "panth": "pantheon", "vlad": "vladimir", "voli": "volibear",
    "ww": "warwick", "fid": "fiddlesticks", "fiddle": "fiddlesticks",
    "heca": "hecarim", "sej": "sejuani", "rene": "renekton", "renek": "renekton",
    "cam": "camille", "lb": "leblanc", "ali": "alistar", "sera": "seraphine",
}


def _normalize(text: str) -> str:
    s = unicodedata.normalize("NFKD", (text or "").lower())
    s = "".join(c for c in s if not unicodedata.combining(c))
    s = re.sub(r"[^a-z0-9\s]", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def _norm_pos(pos: str, idx: int) -> str:
    p = (pos or "").upper()
    if p in ("TOP", "JUNGLE", "MIDDLE", "BOTTOM", "UTILITY"):
        return p
    if p == "JG":
        return "JUNGLE"
    if p == "MID":
        return "MIDDLE"
    if p == "ADC":
        return "BOTTOM"
    if p in ("SUP", "SUPPORT"):
        return "UTILITY"
    order = ["TOP", "JUNGLE", "MIDDLE", "BOTTOM", "UTILITY"]
    return order[idx] if 0 <= idx < 5 else "UNKNOWN"


def _has_word(norm_text: str, phrase: str) -> bool:
    return bool(re.search(rf"(?:^|\s){re.escape(phrase)}(?:\s|$)", norm_text))


def _detect_triggers(norm_text: str) -> list[str]:
    """Devuelve lista de triggers detectados: 'ALL_SUMMS', 'ULTI', o dd_keys de Summoner Spells."""
    found: list[str] = []
    words = norm_text.split()

    if any(_has_word(norm_text, a) for a in ALL_SUMMS_ALIASES):
        found.append("ALL_SUMMS")

    for alias in ULTI_ALIASES:
        if alias == "r":
            if len(words) <= 3 and _has_word(norm_text, "r"):
                found.append("ULTI")
                break
            continue
        if _has_word(norm_text, alias):
            found.append("ULTI")
            break

    for dd_key, aliases in SPELL_ALIASES:
        for alias in aliases:
            if alias == "f":
                if len(words) <= 3 and _has_word(norm_text, "f"):
                    found.append(dd_key)
                    break
                continue
            if _has_word(norm_text, alias):
                found.append(dd_key)
                break

    return found


def _match_enemy_index(
    norm_text: str,
    enemies: list[dict[str, Any]],
    my_position: str = "",
) -> Optional[int]:
    if not enemies:
        return None

    # 1. Buscar por nombre o apodo de campeón enemigo presente en la partida
    compact_text = norm_text.replace(" ", "")
    for idx, en in enumerate(enemies[:5]):
        champ_norm = _normalize(en.get("champion", "")).replace(" ", "")
        if not champ_norm:
            continue
        if len(champ_norm) >= 3 and champ_norm in compact_text:
            return idx
        for nick, target_champ in CHAMP_NICKNAMES.items():
            if target_champ == champ_norm and _has_word(norm_text, nick):
                return idx

    # 2. Buscar por rol (Top / Jungla / Mid / ADC / Supp)
    for role_key, aliases in ROLE_ALIASES.items():
        if any(_has_word(norm_text, a) for a in aliases):
            for idx, en in enumerate(enemies[:5]):
                if _norm_pos(en.get("position", ""), idx) == role_key:
                    return idx

    # 3. Atajo inteligente: si dijo solo "no flash", "sin ulti", "sin summs", etc.
    #    sin nombrar rol ni campeón, apuntar a su rival directo de línea (my_position).
    bare_triggers = (
        "no flash", "sin flash", "no destello", "sin destello", "flasheo", "gasto flash",
        "no ulti", "sin ulti", "no ult", "sin ult", "no r", "sin r", "ulteo", "tiro ulti",
        "sin summs", "no summs", "sin summoners", "no summoners", "gasto todo",
    )
    if any(_has_word(norm_text, p) for p in bare_triggers) and my_position:
        my_norm = _norm_pos(my_position, -1)
        for idx, en in enumerate(enemies[:5]):
            if _norm_pos(en.get("position", ""), idx) == my_norm:
                return idx

    return None


def parse_voice_command(
    transcript: str,
    enemies: list[dict[str, Any]],
    my_position: str = "",
) -> dict[str, Any]:
    """
    Analiza una transcripción de voz y devuelve uno o más targets (Ulti R y/o Summoners)
    a iniciar en el Mini-HUD, o {matched: False} si era charla normal.
    """
    norm = _normalize(transcript)
    if not norm:
        return {"matched": False, "transcript": transcript}

    triggers = _detect_triggers(norm)
    if not triggers:
        return {"matched": False, "transcript": transcript}

    enemy_idx = _match_enemy_index(norm, enemies, my_position=my_position)
    if enemy_idx is None:
        return {"matched": False, "transcript": transcript}

    en = enemies[enemy_idx]
    spells = en.get("spells") or []
    role = _norm_pos(en.get("position", ""), enemy_idx)
    champ = en.get("champion", "")

    targets: list[dict[str, Any]] = []
    seen_keys: set[str] = set()

    for trig in triggers:
        if trig == "ULTI":
            k = f"{enemy_idx}_R"
            if k not in seen_keys:
                seen_keys.add(k)
                targets.append({
                    "key": k,
                    "enemy_idx": enemy_idx,
                    "spell_idx": "R",
                    "spell_name": "Ulti (R)",
                    "spell_dd_key": "ULTI",
                })
        elif trig == "ALL_SUMMS":
            for s_idx, sp in enumerate(spells[:2]):
                k = f"{enemy_idx}_{s_idx}"
                if k not in seen_keys:
                    seen_keys.add(k)
                    targets.append({
                        "key": k,
                        "enemy_idx": enemy_idx,
                        "spell_idx": s_idx,
                        "spell_name": sp.get("name", "Spell"),
                        "spell_dd_key": sp.get("dd_key", "SummonerFlash"),
                    })
        else:
            for s_idx, sp in enumerate(spells[:2]):
                if (sp.get("dd_key") or "").lower() == trig.lower():
                    k = f"{enemy_idx}_{s_idx}"
                    if k not in seen_keys:
                        seen_keys.add(k)
                        targets.append({
                            "key": k,
                            "enemy_idx": enemy_idx,
                            "spell_idx": s_idx,
                            "spell_name": sp.get("name", trig),
                            "spell_dd_key": sp.get("dd_key", trig),
                        })
                    break

    if not targets:
        return {"matched": False, "transcript": transcript, "reason": "spell_not_equipped"}

    first = targets[0]
    return {
        "matched": True,
        "transcript": transcript,
        "enemy_idx": enemy_idx,
        "spell_idx": first["spell_idx"],
        "champion": champ,
        "role": role,
        "spell_name": first["spell_name"],
        "spell_dd_key": first["spell_dd_key"],
        "targets": targets,
    }


def transcribe_wav_bytes(wav_bytes: bytes, lang: str = "es-AR") -> str:
    """Transcribe un clip corto WAV (16kHz mono) usando SpeechRecognition (sin API key)."""
    if not wav_bytes or len(wav_bytes) < 1000:
        return ""
    try:
        import speech_recognition as sr
    except ImportError:
        logger.warning("SpeechRecognition no está instalado.")
        return ""

    recognizer = sr.Recognizer()
    try:
        with sr.AudioFile(io.BytesIO(wav_bytes)) as source:
            audio = recognizer.record(source)
        try:
            return recognizer.recognize_google(audio, language=lang)
        except sr.UnknownValueError:
            fallback = "en-US" if not lang.lower().startswith("en") else "es-AR"
            try:
                return recognizer.recognize_google(audio, language=fallback)
            except Exception:
                return ""
    except Exception as e:
        logger.debug(f"Error transcribiendo audio de voz: {e}")
        return ""
