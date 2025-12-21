# thn_cli/syncv2/status_db.py

"""
THN Sync V2 – Status Database (Hybrid-Standard)
-----------------------------------------------

Purpose:
    Tracks all Sync operations:
        • raw-zip dry-run
        • raw-zip apply
        • cdc-delta dry-run
        • cdc-delta apply
        • (future) rollback events

IMPORTANT ROLE CLARIFICATION
----------------------------
This module represents **authoritative execution history**, not an execution
controller.

It records what *did* happen, never decides what *should* happen.
All execution semantics remain owned by the Sync V2 engine.

Schema (SQLite):

    applies(
        id            INTEGER PRIMARY KEY AUTOINCREMENT,
        ts            TEXT NOT NULL,            -- ISO8601 UTC
        target        TEXT NOT NULL,
        mode          TEXT NOT NULL,            -- raw-zip | cdc-delta | …
        operation     TEXT NOT NULL,            -- apply | dry-run | rollback | …
        dry_run       INTEGER NOT NULL,
        success       INTEGER NOT NULL,
        manifest_hash TEXT,
        envelope_path TEXT,
        source_root   TEXT,
        file_count    INTEGER,
        total_size    INTEGER,
        backup_zip    TEXT,
        destination   TEXT,
        notes         TEXT                      -- JSON blob
    )

This module guarantees:
    - Auto-creation of DB and schema
    - Safe concurrent reads (SQLite connection per-call)
    - Optional metadata (None → NULL)
    - Forward compatibility: new optional columns can be added without breaking callers
"""

from __future__ import annotations

import datetime as _dt
import json
import os
import sqlite3
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Path Resolution
# ---------------------------------------------------------------------------


def _sync_root() -> str:
    """
    Resolve the Sync root for status DB storage.
    Overridable via THN_SYNC_ROOT.
    """
    return os.environ.get("THN_SYNC_ROOT", r"C:\THN\sync")


def _db_path() -> str:
    """
    Return path to the SQLite DB, ensuring the directory exists.
    """
    root = _sync_root()
    status_dir = os.path.join(root, "status")
    os.makedirs(status_dir, exist_ok=True)
    return os.path.join(status_dir, "sync_status.db")


# ---------------------------------------------------------------------------
# Connection + Schema Init
# ---------------------------------------------------------------------------


def _get_conn() -> sqlite3.Connection:
    """
    Get a connection and ensure schema exists.
    Always returns a fresh connection for safety.
    """
    conn = sqlite3.connect(_db_path())
    conn.row_factory = sqlite3.Row
    _init_schema(conn)
    return conn


def _init_schema(conn: sqlite3.Connection) -> None:
    """
    Create required tables if not present.
    """
    cur = conn.cursor()

    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS applies (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            ts            TEXT NOT NULL,
            target        TEXT NOT NULL,
            mode          TEXT NOT NULL,
            operation     TEXT NOT NULL,
            dry_run       INTEGER NOT NULL,
            success       INTEGER NOT NULL,
            manifest_hash TEXT,
            envelope_path TEXT,
            source_root   TEXT,
            file_count    INTEGER,
            total_size    INTEGER,
            backup_zip    TEXT,
            destination   TEXT,
            notes         TEXT
        )
        """
    )

    conn.commit()


# ---------------------------------------------------------------------------
# Insert Apply Record
# ---------------------------------------------------------------------------


def record_apply(
    *,
    target: str,
    mode: str,
    operation: str,
    dry_run: bool,
    success: bool,
    manifest_hash: Optional[str],
    envelope_path: Optional[str],
    source_root: Optional[str],
    file_count: Optional[int],
    total_size: Optional[int],
    backup_zip: Optional[str],
    destination: Optional[str],
    notes: Optional[Dict[str, Any]] = None,
) -> int:
    """
    Insert a record into the 'applies' table.

    Notes:
        - All timestamps are UTC (ISO8601 with 'Z')
        - Boolean fields converted to 0/1
        - notes (dict) stored as JSON (NULL if absent)

    Returns:
        int: row id of inserted record
    """
    ts = _dt.datetime.utcnow().isoformat(timespec="seconds") + "Z"
    notes_text = json.dumps(notes) if notes else None

    conn = _get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO applies (
            ts, target, mode, operation, dry_run, success,
            manifest_hash, envelope_path, source_root,
            file_count, total_size, backup_zip, destination, notes
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            ts,
            target,
            mode,
            operation,
            1 if dry_run else 0,
            1 if success else 0,
            manifest_hash,
            envelope_path,
            source_root,
            file_count,
            total_size,
            backup_zip,
            destination,
            notes_text,
        ),
    )

    conn.commit()
    row_id = cur.lastrowid
    conn.close()
    return row_id


# ---------------------------------------------------------------------------
# Query Utilities
# ---------------------------------------------------------------------------


def get_history(
    *,
    target: Optional[str] = None,
    limit: int = 50,
) -> List[Dict[str, Any]]:
    """
    Retrieve recent history entries.
    If target=None → return most recent global operations.
    """
    conn = _get_conn()
    cur = conn.cursor()

    if target:
        cur.execute(
            """
            SELECT * FROM applies
            WHERE target = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (target, limit),
        )
    else:
        cur.execute(
            """
            SELECT * FROM applies
            ORDER BY id DESC
            LIMIT ?
            """,
            (limit,),
        )

    rows = cur.fetchall()
    conn.close()
    return [_row_to_dict(r) for r in rows]


def get_last(*, target: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Return the most recent apply record (per target or globally).
    """
    conn = _get_conn()
    cur = conn.cursor()

    if target:
        cur.execute(
            """
            SELECT * FROM applies
            WHERE target = ?
            ORDER BY id DESC
            LIMIT 1
            """,
            (target,),
        )
    else:
        cur.execute(
            """
            SELECT * FROM applies
            ORDER BY id DESC
            LIMIT 1
            """
        )

    row = cur.fetchone()
    conn.close()
    return _row_to_dict(row) if row else None


def get_entry_by_id(entry_id: int) -> Optional[Dict[str, Any]]:
    """
    Fetch a single entry by primary key.
    """
    conn = _get_conn()
    cur = conn.cursor()

    cur.execute(
        "SELECT * FROM applies WHERE id = ?",
        (entry_id,),
    )

    row = cur.fetchone()
    conn.close()
    return _row_to_dict(row) if row else None


# ---------------------------------------------------------------------------
# Transform Row → Dict
# ---------------------------------------------------------------------------


def _row_to_dict(row: sqlite3.Row) -> Dict[str, Any]:
    """
    Convert a SQLite row to a Python dict, decoding notes JSON if present.
    """
    d = dict(row)

    notes = d.get("notes")
    if notes:
        try:
            d["notes"] = json.loads(notes)
        except Exception:
            pass

    return d


# ---------------------------------------------------------------------------
# Compatibility placeholder for diagnostics
# ---------------------------------------------------------------------------


def test_status_db_read() -> dict:
    """
    Placeholder function required by sanity diagnostics.
    """
    return {
        "status": "not_implemented",
        "db_state": None,
        "message": "test_status_db_read placeholder",
    }
