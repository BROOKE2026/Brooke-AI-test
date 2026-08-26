"""
Durable state for the Brooke API: sessions, meeting requests, transcripts.

One SQLite file. Sessions survive a server restart (a redeploy no longer logs
every client out), meeting requests persist, and every conversation turn is
recorded append-only: who asked what, what route answered it, and how long it
took. The transcript table is the raw material for the compliance archive a
real deployment needs (SEC 17a-4 style retention lives on top of this, not
instead of it).
"""

import json
import sqlite3
import threading
import time
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "brooke.db"
_lock = threading.Lock()
_conn = None


def _db():
    global _conn
    if _conn is None:
        _conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        _conn.execute("PRAGMA journal_mode=WAL")
        _conn.executescript("""
        CREATE TABLE IF NOT EXISTS sessions (
            token      TEXT PRIMARY KEY,
            client_id  TEXT NOT NULL,
            created    REAL NOT NULL
        );
        CREATE TABLE IF NOT EXISTS meeting_requests (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            client_id  TEXT NOT NULL,
            created    REAL NOT NULL,
            kind       TEXT, date TEXT, time TEXT, topic TEXT,
            status     TEXT DEFAULT 'requested'
        );
        CREATE TABLE IF NOT EXISTS transcript (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            ts         REAL NOT NULL,
            client_id  TEXT NOT NULL,
            role       TEXT NOT NULL,          -- 'client' | 'brooke'
            content    TEXT NOT NULL,
            route      TEXT,                   -- instant/advice/tax/howto/nav/model/...
            ms         INTEGER
        );
        CREATE INDEX IF NOT EXISTS transcript_client ON transcript(client_id, ts);
        """)
    return _conn


# ---------------------------------------------------------------- sessions --

def save_session(token, client_id, created):
    with _lock:
        _db().execute("INSERT OR REPLACE INTO sessions VALUES (?,?,?)",
                      (token, client_id, created))
        _db().commit()


def load_sessions():
    with _lock:
        rows = _db().execute("SELECT token, client_id, created FROM sessions").fetchall()
    return {t: {"client_id": c, "created": cr} for t, c, cr in rows}


def drop_session(token):
    with _lock:
        _db().execute("DELETE FROM sessions WHERE token=?", (token,))
        _db().commit()


def sweep_sessions(ttl):
    cutoff = time.time() - ttl
    with _lock:
        _db().execute("DELETE FROM sessions WHERE created < ?", (cutoff,))
        _db().commit()


# ---------------------------------------------------------------- meetings --

def save_meeting(client_id, meeting):
    with _lock:
        _db().execute(
            "INSERT INTO meeting_requests (client_id, created, kind, date, time, topic) "
            "VALUES (?,?,?,?,?,?)",
            (client_id, time.time(), meeting.get("type"), meeting.get("date"),
             meeting.get("time"), meeting.get("topic")))
        _db().commit()


def load_meetings(client_id):
    with _lock:
        rows = _db().execute(
            "SELECT kind, date, time, topic, status FROM meeting_requests "
            "WHERE client_id=? ORDER BY created DESC", (client_id,)).fetchall()
    return [{"type": k, "date": d, "time": t, "topic": tp, "status": st}
            for k, d, t, tp, st in rows]


def count_open_meetings(client_id):
    with _lock:
        (n,) = _db().execute(
            "SELECT COUNT(*) FROM meeting_requests WHERE client_id=? AND status='requested'",
            (client_id,)).fetchone()
    return n


# -------------------------------------------------------------- transcript --

def log_turn(client_id, role, content, route=None, ms=None):
    try:
        with _lock:
            _db().execute(
                "INSERT INTO transcript (ts, client_id, role, content, route, ms) "
                "VALUES (?,?,?,?,?,?)",
                (time.time(), client_id, role, (content or "")[:8000], route, ms))
            _db().commit()
    except Exception:
        pass          # the conversation must never fail because logging did
