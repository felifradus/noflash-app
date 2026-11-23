"""
Caché local en disco (SQLite) para partidas de League of Legends.
Una partida terminada nunca cambia: guardándola localmente evitamos volver a
pedirla a Riot API, logrando cargas casi instantáneas (<1s) y respetando rate limits.
"""

import json
import sqlite3
import zlib
from pathlib import Path
from typing import Any, Optional

DB_PATH = Path(__file__).resolve().parent / "data" / "match_cache.db"


class MatchCache:
    """Almacena y recupera detalles de partidas comprimidos en SQLite."""

    def __init__(self, db_path: Path = DB_PATH) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _init_db(self) -> None:
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA synchronous=NORMAL")
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS matches (
                    match_id TEXT PRIMARY KEY,
                    data BLOB NOT NULL
                )
                """
            )
            conn.commit()

    def get_many(self, match_ids: list[str]) -> dict[str, dict[str, Any]]:
        """Recupera en una sola consulta todas las partidas ya cacheadas."""
        if not match_ids:
            return {}
        placeholders = ",".join("?" for _ in match_ids)
        found: dict[str, dict[str, Any]] = {}
        with sqlite3.connect(self.db_path) as conn:
            rows = conn.execute(
                f"SELECT match_id, data FROM matches WHERE match_id IN ({placeholders})",
                match_ids,
            ).fetchall()
        for match_id, blob in rows:
            try:
                raw = zlib.decompress(blob).decode("utf-8")
                found[match_id] = json.loads(raw)
            except Exception:
                continue
        return found

    def put_many(self, items: dict[str, dict[str, Any]]) -> None:
        """Guarda múltiples partidas comprimidas en una sola transacción."""
        if not items:
            return
        rows = []
        for match_id, payload in items.items():
            try:
                blob = zlib.compress(
                    json.dumps(payload, separators=(",", ":")).encode("utf-8"),
                    level=6,
                )
                rows.append((match_id, blob))
            except Exception:
                continue
        if not rows:
            return
        with sqlite3.connect(self.db_path) as conn:
            conn.executemany(
                "INSERT OR REPLACE INTO matches (match_id, data) VALUES (?, ?)",
                rows,
            )
            conn.commit()

    def count(self) -> int:
        with sqlite3.connect(self.db_path) as conn:
            row = conn.execute("SELECT COUNT(*) FROM matches").fetchone()
            return int(row[0]) if row else 0
