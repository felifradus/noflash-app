"""
Cliente LCU (League Client Update) para conectar automáticamente
con el cliente de League of Legends abierto en la PC del usuario.
No requiere API Key de Riot: usa el lockfile o proceso local del cliente.
"""

import base64
import logging
import re
import subprocess
import time
from pathlib import Path
from typing import Any, Optional

import httpx

from app.data.counter_data import CHAMPION_ID_TO_NAME

logger = logging.getLogger(__name__)

COMMON_LOCKFILE_PATHS = [
    Path("C:/Riot Games/League of Legends/lockfile"),
    Path("D:/Riot Games/League of Legends/lockfile"),
    Path("E:/Riot Games/League of Legends/lockfile"),
    Path("C:/Program Files/Riot Games/League of Legends/lockfile"),
    Path("C:/Program Files (x86)/Riot Games/League of Legends/lockfile"),
]

LCU_POSITION_MAP = {
    "top": "TOP",
    "jungle": "JG",
    "middle": "MID",
    "bottom": "ADC",
    "utility": "SUP",
}

# IDs oficiales de Hechizos de Invocador de Riot
SPELL_NAME_TO_ID: dict[str, int] = {
    "flash": 4, "destello": 4,
    "barrier": 21, "barrera": 21,
    "cleanse": 1, "limpiar": 1,
    "exhaust": 3, "extenuar": 3,
    "ignite": 14, "prender": 14,
    "teleport": 12, "teleportación": 12,
    "ghost": 6, "fantasmal": 6,
    "heal": 7, "curar": 7,
    "smite": 11, "aplastar": 11,
}

# Páginas de runas completas válidas (Riot Perks v1: 1 keystone + 3 primarias + 2 secundarias + 3 shards)
RUNE_PRESETS: dict[str, dict[str, Any]] = {
    "Compás Letal": {"primary": 8000, "sub": 8300, "perks": [8008, 9101, 9104, 8014, 8304, 8345, 5005, 5008, 5001]},
    "Lethal Tempo": {"primary": 8000, "sub": 8300, "perks": [8008, 9101, 9104, 8014, 8304, 8345, 5005, 5008, 5001]},
    "Pies Veloces": {"primary": 8000, "sub": 8200, "perks": [8021, 9101, 9103, 8014, 8234, 8236, 5005, 5008, 5001]},
    "Fleet Footwork": {"primary": 8000, "sub": 8200, "perks": [8021, 9101, 9103, 8014, 8234, 8236, 5005, 5008, 5001]},
    "Ataque Intensificado": {"primary": 8000, "sub": 8300, "perks": [8005, 8009, 9104, 8014, 8304, 8345, 5005, 5008, 5001]},
    "Press the Attack": {"primary": 8000, "sub": 8300, "perks": [8005, 8009, 9104, 8014, 8304, 8345, 5005, 5008, 5001]},
    "Conquistador": {"primary": 8000, "sub": 8400, "perks": [8010, 9111, 9104, 8299, 8473, 8451, 5005, 5008, 5001]},
    "Conqueror": {"primary": 8000, "sub": 8400, "perks": [8010, 9111, 9104, 8299, 8473, 8451, 5005, 5008, 5001]},
    "Electrocutar": {"primary": 8100, "sub": 8200, "perks": [8112, 8139, 8138, 8135, 8226, 8237, 5008, 5008, 5001]},
    "Electrocute": {"primary": 8100, "sub": 8200, "perks": [8112, 8139, 8138, 8135, 8226, 8237, 5008, 5008, 5001]},
    "Cometa Arcano": {"primary": 8200, "sub": 8300, "perks": [8229, 8226, 8210, 8237, 8345, 8347, 5008, 5008, 5001]},
    "Arcane Comet": {"primary": 8200, "sub": 8300, "perks": [8229, 8226, 8210, 8237, 8345, 8347, 5008, 5008, 5001]},
    "Invocar a Aery": {"primary": 8200, "sub": 8300, "perks": [8214, 8226, 8210, 8237, 8345, 8347, 5008, 5008, 5001]},
    "Summon Aery": {"primary": 8200, "sub": 8300, "perks": [8214, 8226, 8210, 8237, 8345, 8347, 5008, 5008, 5001]},
    "Irrupción de Fase": {"primary": 8200, "sub": 8300, "perks": [8230, 8275, 8210, 8236, 8304, 8347, 5007, 5008, 5001]},
    "Phase Rush": {"primary": 8200, "sub": 8300, "perks": [8230, 8275, 8210, 8236, 8304, 8347, 5007, 5008, 5001]},
    "Primer Golpe": {"primary": 8300, "sub": 8200, "perks": [8369, 8304, 8345, 8347, 8226, 8210, 5008, 5008, 5001]},
    "First Strike": {"primary": 8300, "sub": 8200, "perks": [8369, 8304, 8345, 8347, 8226, 8210, 5008, 5008, 5001]},
    "Réplica": {"primary": 8400, "sub": 8300, "perks": [8439, 8463, 8473, 8451, 8306, 8347, 5007, 5001, 5013]},
    "Aftershock": {"primary": 8400, "sub": 8300, "perks": [8439, 8463, 8473, 8451, 8306, 8347, 5007, 5001, 5013]},
    "Agarre del Perpetuo": {"primary": 8400, "sub": 8300, "perks": [8437, 8446, 8444, 8451, 8304, 8345, 5005, 5008, 5001]},
    "Grasp of the Undying": {"primary": 8400, "sub": 8300, "perks": [8437, 8446, 8444, 8451, 8304, 8345, 5005, 5008, 5001]},
    "Guardián": {"primary": 8400, "sub": 8300, "perks": [8465, 8463, 8473, 8451, 8345, 8347, 5007, 5001, 5001]},
    "Guardian": {"primary": 8400, "sub": 8300, "perks": [8465, 8463, 8473, 8451, 8345, 8347, 5007, 5001, 5001]},
    "Dark Harvest": {"primary": 8100, "sub": 8200, "perks": [8128, 8139, 8138, 8135, 8226, 8237, 5008, 5008, 5001]},
    "Cosecha Oscura": {"primary": 8100, "sub": 8200, "perks": [8128, 8139, 8138, 8135, 8226, 8237, 5008, 5008, 5001]},
    "Hail of Blades": {"primary": 8100, "sub": 8000, "perks": [9923, 8143, 8138, 8135, 9111, 8014, 5005, 5008, 5001]},
    "Lluvia de Espadas": {"primary": 8100, "sub": 8000, "perks": [9923, 8143, 8138, 8135, 9111, 8014, 5005, 5008, 5001]},
    "Glacial Augment": {"primary": 8300, "sub": 8400, "perks": [8351, 8306, 8345, 8347, 8473, 8451, 5007, 5001, 5001]},
    "Aumento Glacial": {"primary": 8300, "sub": 8400, "perks": [8351, 8306, 8345, 8347, 8473, 8451, 5007, 5001, 5001]},
}


class LCUClient:
    """Detecta el cliente de LoL local y lee el estado de la cuenta y del Champ Select."""

    def __init__(self) -> None:
        self._client: Optional[httpx.AsyncClient] = None
        self._cached_creds: Optional[tuple[int, str]] = None
        self._last_ps_check: float = 0.0

    def _get_http_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(verify=False, timeout=2.5)
        return self._client

    def _discover_credentials(self) -> Optional[tuple[int, str]]:
        """Busca el puerto y token del cliente de LoL (lockfile rápido o proceso cada 20s)."""
        # 1. Buscar en rutas comunes del lockfile (instantáneo, <0.1ms)
        for path in COMMON_LOCKFILE_PATHS:
            if path.exists():
                try:
                    content = path.read_text(encoding="utf-8").strip()
                    parts = content.split(":")
                    if len(parts) >= 4:
                        creds = (int(parts[2]), parts[3])
                        self._cached_creds = creds
                        return creds
                except Exception as e:
                    logger.debug(f"No se pudo leer lockfile {path}: {e}")

        # 2. Fallback: consultar LeagueClientUx.exe como máximo cada 20s para ahorrar CPU
        now = time.monotonic()
        if self._cached_creds and (now - self._last_ps_check) < 20.0:
            return self._cached_creds
        if (now - self._last_ps_check) < 20.0:
            return None
        self._last_ps_check = now

        try:
            cmd = [
                "powershell",
                "-NoProfile",
                "-Command",
                "(Get-CimInstance Win32_Process -Filter \"Name='LeagueClientUx.exe'\").CommandLine",
            ]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=3,
                creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
            )
            cmdline = result.stdout or ""
            port_match = re.search(r"--app-port=(\d+)", cmdline)
            token_match = re.search(r"--remoting-auth-token=([\w-]+)", cmdline)
            if port_match and token_match:
                creds = (int(port_match.group(1)), token_match.group(1))
                self._cached_creds = creds
                return creds
        except Exception as e:
            logger.debug(f"No se pudo detectar LeagueClientUx.exe: {e}")

        self._cached_creds = None
        return None

    async def _lcu_get(self, endpoint: str) -> Optional[Any]:
        """Realiza un GET autenticado al LCU local."""
        creds = self._discover_credentials()
        if not creds:
            return None

        port, password = creds
        auth = base64.b64encode(f"riot:{password}".encode("utf-8")).decode("utf-8")
        url = f"https://127.0.0.1:{port}{endpoint}"

        try:
            client = self._get_http_client()
            resp = await client.get(
                url,
                headers={"Authorization": f"Basic {auth}"},
            )
            if resp.status_code == 200:
                return resp.json()
            return None
        except Exception as e:
            self._cached_creds = None
            logger.debug(f"Error consultando LCU {endpoint}: {e}")
            return None

    async def get_status(self) -> dict[str, Any]:
        """Verifica si el cliente de LoL está abierto y obtiene la cuenta logueada."""
        summoner = await self._lcu_get("/lol-summoner/v1/current-summoner")
        if not summoner:
            return {
                "connected": False,
                "in_champ_select": False,
                "message": "Cliente de LoL no detectado. Abrí el juego para sincronizar automáticamente.",
            }

        session = await self._lcu_get("/lol-champ-select/v1/session")
        region_info = await self._lcu_get("/riotclient/region-locale") or {}

        return {
            "connected": True,
            "in_champ_select": session is not None,
            "summoner": {
                "game_name": summoner.get("gameName") or summoner.get("displayName", ""),
                "tag_line": summoner.get("tagLine", ""),
                "puuid": summoner.get("puuid", ""),
                "summoner_level": summoner.get("summonerLevel", 0),
                "region": (region_info.get("region") or "").upper(),
            },
            "message": (
                "¡En Selección de Campeones! Leyendo draft en vivo."
                if session is not None
                else "Cliente de LoL conectado. Esperando partida..."
            ),
        }

    async def get_champ_select(self) -> dict[str, Any]:
        """Lee la sesión actual de Champ Select (rol, picks aliados/enemigos y bans)."""
        session = await self._lcu_get("/lol-champ-select/v1/session")
        if not session:
            return {
                "connected": (await self._lcu_get("/lol-summoner/v1/current-summoner")) is not None,
                "in_champ_select": False,
                "my_role": None,
                "ally_picks": [],
                "enemy_picks": [],
                "bans": [],
                "phase": None,
            }

        local_cell_id = session.get("localPlayerCellId")
        my_role: Optional[str] = None
        ally_picks: list[str] = []
        enemy_picks: list[str] = []

        for member in session.get("myTeam", []):
            if member.get("cellId") == local_cell_id:
                pos = (member.get("assignedPosition") or "").lower()
                my_role = LCU_POSITION_MAP.get(pos)
            champ_id = member.get("championId") or member.get("championPickIntent") or 0
            if champ_id and champ_id in CHAMPION_ID_TO_NAME:
                if member.get("cellId") != local_cell_id:
                    ally_picks.append(CHAMPION_ID_TO_NAME[champ_id])

        for member in session.get("theirTeam", []):
            champ_id = member.get("championId") or 0
            if champ_id and champ_id in CHAMPION_ID_TO_NAME:
                enemy_picks.append(CHAMPION_ID_TO_NAME[champ_id])

        # Extraer bans si existen
        bans: list[str] = []
        bans_obj = session.get("bans", {})
        for ban_id in (bans_obj.get("myTeamBans", []) + bans_obj.get("theirTeamBans", [])):
            if ban_id and ban_id in CHAMPION_ID_TO_NAME:
                bans.append(CHAMPION_ID_TO_NAME[ban_id])

        phase = (session.get("timer") or {}).get("phase", "")

        return {
            "connected": True,
            "in_champ_select": True,
            "my_role": my_role,
            "ally_picks": ally_picks,
            "enemy_picks": enemy_picks,
            "bans": bans,
            "phase": phase,
        }


    async def _lcu_request(
        self, method: str, endpoint: str, json_body: Optional[dict[str, Any]] = None
    ) -> tuple[int, Optional[Any]]:
        creds = self._discover_credentials()
        if not creds:
            return 0, None
        port, password = creds
        auth = base64.b64encode(f"riot:{password}".encode("utf-8")).decode("utf-8")
        url = f"https://127.0.0.1:{port}{endpoint}"
        try:
            async with httpx.AsyncClient(verify=False, timeout=3.0) as client:
                resp = await client.request(
                    method,
                    url,
                    headers={"Authorization": f"Basic {auth}"},
                    json=json_body,
                )
                data = resp.json() if resp.content else None
                return resp.status_code, data
        except Exception as e:
            logger.debug(f"Error LCU {method} {endpoint}: {e}")
            return 0, None

    async def import_setup(
        self, champion: str, keystone: str, spells: list[str]
    ) -> dict[str, Any]:
        """
        Importa en 1 click la página de runas (NoFlash: {champion}) y,
        si el jugador está en Champ Select, también los 2 hechizos de invocador.
        """
        if not self._discover_credentials():
            return {
                "success": False,
                "message": "Cliente de LoL no detectado. Abrí League of Legends para importar.",
            }

        # 1. Crear/reemplazar página de runas editable
        preset = RUNE_PRESETS.get(keystone) or RUNE_PRESETS["Compás Letal"]
        runes_ok = False
        status_pages, pages = await self._lcu_request("GET", "/lol-perks/v1/pages")
        if status_pages == 200 and isinstance(pages, list):
            # Borrar página anterior de NoFlash o la actual si es editable para no llenar el límite
            target_delete = None
            for p in pages:
                if p.get("isEditable") and str(p.get("name", "")).startswith("NoFlash"):
                    target_delete = p.get("id")
                    break
            if target_delete is None:
                for p in pages:
                    if p.get("isEditable") and p.get("current"):
                        target_delete = p.get("id")
                        break
            if target_delete is not None:
                await self._lcu_request("DELETE", f"/lol-perks/v1/pages/{target_delete}")

        new_page = {
            "name": f"NoFlash: {champion}",
            "primaryStyleId": preset["primary"],
            "subStyleId": preset["sub"],
            "selectedPerkIds": preset["perks"],
            "current": True,
        }
        st_post, _ = await self._lcu_request("POST", "/lol-perks/v1/pages", new_page)
        runes_ok = st_post in (200, 201)

        # 2. Importar hechizos de invocador si está en Champ Select
        spells_ok = False
        if len(spells) >= 2:
            def _to_id(label: str) -> int:
                low = (label or "").lower()
                for k, v in SPELL_NAME_TO_ID.items():
                    if k in low:
                        return v
                return 4

            st_sp, _ = await self._lcu_request(
                "PATCH",
                "/lol-champ-select/v1/session/my-selection",
                {"spell1Id": _to_id(spells[0]), "spell2Id": _to_id(spells[1])},
            )
            spells_ok = st_sp in (200, 204)

        if runes_ok and spells_ok:
            msg = f"¡Runas ({keystone}) y Hechizos importados al LoL para {champion}!"
        elif runes_ok:
            msg = f"¡Página de runas 'NoFlash: {champion}' importada al LoL! (Hechizos se aplican en Champ Select)"
        else:
            msg = "No se pudo crear la página de runas (verificá tener una página editable en tu cliente de LoL)."

        return {
            "success": runes_ok or spells_ok,
            "runes_imported": runes_ok,
            "spells_imported": spells_ok,
            "message": msg,
        }
