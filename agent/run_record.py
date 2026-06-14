import sqlite3
import os
from datetime import datetime
from typing import Optional, List
from agent.models.types import RunRecord

DB_DIR = os.environ.get('DATA_DIR', os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'run_records'))
DB_PATH = os.path.join(DB_DIR, 'pulse_runs.db')

def init_db(db_path: str = DB_PATH):
    """Initialize the SQLite database with the runs table."""
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS runs (
                run_id TEXT PRIMARY KEY,
                product TEXT NOT NULL,
                iso_week TEXT NOT NULL,
                started_at TEXT NOT NULL,
                completed_at TEXT,
                status TEXT NOT NULL,
                reviews_fetched INTEGER,
                clusters_found INTEGER,
                themes_generated INTEGER,
                doc_heading_anchor TEXT,
                doc_id TEXT,
                email_message_id TEXT,
                email_mode TEXT,
                llm_tokens_used INTEGER,
                error_message TEXT
            )
        ''')
        conn.commit()

def _row_to_record(row: tuple) -> RunRecord:
    """Convert a SQLite row to a RunRecord object."""
    return RunRecord(
        run_id=row[0],
        product=row[1],
        iso_week=row[2],
        started_at=datetime.fromisoformat(row[3]),
        completed_at=datetime.fromisoformat(row[4]) if row[4] else None,
        status=row[5],
        reviews_fetched=row[6],
        clusters_found=row[7],
        themes_generated=row[8],
        doc_heading_anchor=row[9],
        doc_id=row[10],
        email_message_id=row[11],
        email_mode=row[12],
        llm_tokens_used=row[13],
        error_message=row[14]
    )

def find_record(product: str, iso_week: str, db_path: str = DB_PATH) -> Optional[RunRecord]:
    """Find a successful run record for a given product and ISO week."""
    if not os.path.exists(db_path):
        return None
    
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM runs
            WHERE product = ? AND iso_week = ? AND status = 'success'
            ORDER BY completed_at DESC
            LIMIT 1
        ''', (product, iso_week))
        row = cursor.fetchone()
        
        if row:
            return _row_to_record(row)
        return None

def insert_record(record: RunRecord, db_path: str = DB_PATH) -> None:
    """Insert a new run record into the database."""
    init_db(db_path)
    
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO runs (
                run_id, product, iso_week, started_at, completed_at, status,
                reviews_fetched, clusters_found, themes_generated,
                doc_heading_anchor, doc_id, email_message_id, email_mode,
                llm_tokens_used, error_message
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(run_id) DO UPDATE SET
                product=excluded.product,
                iso_week=excluded.iso_week,
                started_at=excluded.started_at,
                completed_at=excluded.completed_at,
                status=excluded.status,
                reviews_fetched=excluded.reviews_fetched,
                clusters_found=excluded.clusters_found,
                themes_generated=excluded.themes_generated,
                doc_heading_anchor=excluded.doc_heading_anchor,
                doc_id=excluded.doc_id,
                email_message_id=excluded.email_message_id,
                email_mode=excluded.email_mode,
                llm_tokens_used=excluded.llm_tokens_used,
                error_message=excluded.error_message
        ''', (
            record.run_id,
            record.product,
            record.iso_week,
            record.started_at.isoformat(),
            record.completed_at.isoformat() if record.completed_at else None,
            record.status,
            record.reviews_fetched,
            record.clusters_found,
            record.themes_generated,
            record.doc_heading_anchor,
            record.doc_id,
            record.email_message_id,
            record.email_mode,
            record.llm_tokens_used,
            record.error_message
        ))
        conn.commit()

def list_records(product: str, limit: int = 10, db_path: str = DB_PATH) -> List[RunRecord]:
    """List recent run records for a product."""
    if not os.path.exists(db_path):
        return []
        
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT * FROM runs
            WHERE product = ?
            ORDER BY started_at DESC
            LIMIT ?
        ''', (product, limit))
        rows = cursor.fetchall()
        
        return [_row_to_record(row) for row in rows]
