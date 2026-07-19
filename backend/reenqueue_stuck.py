"""One-off maintenance script: re-enqueue files stuck in 'processing' or
'failed' status whose thumbnail job never actually completed — e.g. the
batch that hit the psycopg2 sslmode bug before it was fixed.

Run inside a deployed container (backend or worker, either has the same
code and DB access):

    railway ssh
    python reenqueue_stuck.py
"""
from sqlalchemy import text

from app.files.jobs import _get_sync_engine, enqueue_process_file


def main() -> None:
    engine = _get_sync_engine()

    with engine.begin() as conn:
        rows = conn.execute(
            text("SELECT id, storage_key, media_type FROM files WHERE status IN ('processing', 'failed')")
        ).fetchall()

    if not rows:
        print("Nothing stuck — no files in 'processing' or 'failed' state.")
        return

    print(f"Found {len(rows)} stuck file(s). Re-enqueueing...")

    with engine.begin() as conn:
        for file_id, storage_key, media_type in rows:
            conn.execute(
                text("UPDATE files SET status = 'processing', updated_at = now() WHERE id = :id"),
                {"id": file_id},
            )

    for file_id, storage_key, media_type in rows:
        enqueue_process_file(str(file_id), storage_key, media_type)
        print(f"  re-enqueued {file_id} ({media_type})")

    print("Done. Watch the worker logs to confirm each job completes.")


if __name__ == "__main__":
    main()
