"""
Cliente para la API de Riot Games.
Maneja autenticación, rate limiting y todos los endpoints necesarios
para obtener datos de un jugador de League of Legends.
"""

import asyncio
import logging
from typing import Any, Optional

import httpx

logger = logging.getLogger(__name__)

# Mapeo de plataformas a sus routings regionales
PLATFORM_TO_ROUTING: dict[str, str] = {
    "na1": "americas",
    "br1": "americas",
    "la1": "americas",
    "la2": "americas",
    "oc1": "sea",
    "euw1": "europe",
    "eun1": "europe",
    "tr1": "europe",
    "ru": "europe",
    "kr": "asia",
    "jp1": "asia",
    "ph2": "sea",
    "sg2": "sea",
    "th2": "sea",
    "tw2": "sea",
    "vn2": "sea",
}

# Nombres legibles para las regiones (para el frontend)
REGION_DISPLAY_NAMES: dict[str, str] = {
    "na1": "Norte América (NA)",
    "br1": "Brasil (BR)",
    "la1": "Latinoamérica Norte (LAN)",
    "la2": "Latinoamérica Sur (LAS)",
    "euw1": "Europa Oeste (EUW)",
    "eun1": "Europa Nórdica & Este (EUNE)",
    "tr1": "Turquía (TR)",
    "ru": "Rusia (RU)",
    "kr": "Corea (KR)",
    "jp1": "Japón (JP)",
    "oc1": "Oceanía (OCE)",
    "ph2": "Filipinas (PH)",
    "sg2": "Singapur (SG)",
    "th2": "Tailandia (TH)",
    "tw2": "Taiwán (TW)",
    "vn2": "Vietnam (VN)",
}


class RiotAPIError(Exception):
    """Error personalizado para problemas con la API de Riot."""

    def __init__(self, mensaje: str, status_code: int | None = None) -> None:
        self.mensaje = mensaje
        self.status_code = status_code
        super().__init__(mensaje)


class RiotAPIClient:
    """
    Cliente asíncrono para interactuar con la API de Riot Games.
    Maneja autenticación, rate limiting (429) con reintentos y backoff.
    """

    MAX_RETRIES: int = 3
    BASE_BACKOFF: float = 1.0  # segundos base para backoff exponencial

    def __init__(self, api_key: str) -> None:
        self._api_key = api_key
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        """Obtiene o crea el cliente HTTP."""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                headers={"X-Riot-Token": self._api_key},
                timeout=httpx.Timeout(30.0),
            )
        return self._client

    async def close(self) -> None:
        """Cierra el cliente HTTP."""
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def _request(self, url: str) -> Any:
        """
        Realiza un request GET con manejo de rate limiting y errores.
        Reintenta automáticamente ante 429 (Rate Limit) con backoff exponencial.
        """
        client = await self._get_client()

        for intento in range(self.MAX_RETRIES):
            try:
                response = await client.get(url)

                if response.status_code == 200:
                    return response.json()

                if response.status_code == 429:
                    # Rate limited — usar Retry-After si lo provee Riot
                    retry_after = response.headers.get("Retry-After")
                    if retry_after:
                        espera = int(retry_after)
                    else:
                        espera = self.BASE_BACKOFF * (2 ** intento)
                    logger.warning(
                        f"Rate limited (429). Reintentando en {espera}s "
                        f"(intento {intento + 1}/{self.MAX_RETRIES})"
                    )
                    await asyncio.sleep(espera)
                    continue

                if response.status_code == 403:
                    raise RiotAPIError(
                        "API Key inválida o expirada. "
                        "Verificá tu clave en https://developer.riotgames.com/",
                        status_code=403,
                    )

                if response.status_code == 404:
                    raise RiotAPIError(
                        "No se encontró el recurso solicitado. "
                        "Verificá el nombre de invocador y la región.",
                        status_code=404,
                    )

                raise RiotAPIError(
                    f"Error de la API de Riot (código {response.status_code}): "
                    f"{response.text}",
                    status_code=response.status_code,
                )

            except httpx.TimeoutException:
                if intento < self.MAX_RETRIES - 1:
                    espera = self.BASE_BACKOFF * (2 ** intento)
                    logger.warning(
                        f"Timeout en request. Reintentando en {espera}s "
                        f"(intento {intento + 1}/{self.MAX_RETRIES})"
                    )
                    await asyncio.sleep(espera)
                    continue
                raise RiotAPIError(
                    "La API de Riot no respondió a tiempo. Intentá de nuevo más tarde."
                )

            except httpx.HTTPError as e:
                if intento < self.MAX_RETRIES - 1:
                    espera = self.BASE_BACKOFF * (2 ** intento)
                    logger.warning(
                        f"Error HTTP: {e}. Reintentando en {espera}s "
                        f"(intento {intento + 1}/{self.MAX_RETRIES})"
                    )
                    await asyncio.sleep(espera)
                    continue
                raise RiotAPIError(
                    f"Error de conexión con la API de Riot: {e}"
                )

        raise RiotAPIError(
            "Se agotaron los reintentos al comunicarse con la API de Riot."
        )

    def _get_routing(self, platform: str) -> str:
        """Obtiene el routing regional para una plataforma."""
        routing = PLATFORM_TO_ROUTING.get(platform.lower())
        if not routing:
            raise RiotAPIError(
                f"Plataforma '{platform}' no reconocida. "
                f"Plataformas válidas: {', '.join(PLATFORM_TO_ROUTING.keys())}"
            )
        return routing

    # ── Account API v1 ──────────────────────────────────────────────

    async def get_account_by_riot_id(
        self, game_name: str, tag_line: str, region: str = "americas"
    ) -> dict[str, Any]:
        """
        Obtiene la cuenta (incluido PUUID) a partir del Riot ID.
        region es el routing regional (americas, europe, asia).
        """
        url = (
            f"https://{region}.api.riotgames.com"
            f"/riot/account/v1/accounts/by-riot-id/{game_name}/{tag_line}"
        )
        return await self._request(url)

    # ── Summoner API v4 ─────────────────────────────────────────────

    async def get_summoner_by_puuid(
        self, puuid: str, platform: str
    ) -> dict[str, Any]:
        """Obtiene datos del summoner a partir del PUUID."""
        url = (
            f"https://{platform}.api.riotgames.com"
            f"/lol/summoner/v4/summoners/by-puuid/{puuid}"
        )
        return await self._request(url)

    # ── Match API v5 ────────────────────────────────────────────────

    async def get_match_ids(
        self,
        puuid: str,
        region: str = "americas",
        count: int = 20,
        start: int = 0,
        queue: Optional[int] = None,
    ) -> list[str]:
        """
        Obtiene los últimos N match IDs de un jugador con paginación (start).
        queue=420 para solo ranked, None para todos.
        """
        url = (
            f"https://{region}.api.riotgames.com"
            f"/lol/match/v5/matches/by-puuid/{puuid}/ids?start={start}&count={count}"
        )
        if queue is not None:
            url += f"&queue={queue}"
        return await self._request(url)

    async def get_match_detail(
        self, match_id: str, region: str = "americas"
    ) -> dict[str, Any]:
        """Obtiene el detalle completo de un match."""
        url = (
            f"https://{region}.api.riotgames.com"
            f"/lol/match/v5/matches/{match_id}"
        )
        return await self._request(url)

    # ── Champion Mastery API v4 ─────────────────────────────────────

    async def get_champion_masteries(
        self, puuid: str, platform: str
    ) -> list[dict[str, Any]]:
        """Obtiene las maestrías de campeón del jugador."""
        url = (
            f"https://{platform}.api.riotgames.com"
            f"/lol/champion-mastery/v4/champion-masteries/by-puuid/{puuid}"
        )
        return await self._request(url)

    # ── League API v4 ──────────────────────────────────────────────

    async def get_ranked_stats_by_puuid(
        self, puuid: str, platform: str
    ) -> list[dict[str, Any]]:
        """Obtiene las estadísticas de ranked del jugador usando su PUUID."""
        url = (
            f"https://{platform}.api.riotgames.com"
            f"/lol/league/v4/entries/by-puuid/{puuid}"
        )
        return await self._request(url)

    async def get_ranked_stats(
        self, summoner_id: str, platform: str
    ) -> list[dict[str, Any]]:
        """Obtiene las estadísticas de ranked del jugador (legacy by-summoner)."""
        url = (
            f"https://{platform}.api.riotgames.com"
            f"/lol/league/v4/entries/by-summoner/{summoner_id}"
        )
        return await self._request(url)
