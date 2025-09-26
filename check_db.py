import os
import sqlite3

db = os.environ.get("TERMNET_DB", "test_trajectories.db")
conn = sqlite3.connect(db)
cur = conn.cursor()

tables = ["trajectories", "trajectory_steps", "golden_trajectories"]

for t in tables:
    try:
        n = cur.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        print(f"{t}: {n} rows")
    except Exception as e:
        print(f"ERR {t} -> {e}")

conn.close()
