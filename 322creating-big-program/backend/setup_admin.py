#!/usr/bin/env python3
import sqlite3, sys

DB = "/root/backend/campus.db"

if len(sys.argv) < 2:
    print("Usage: python3 setup_admin.py <username>")
    sys.exit(1)

username = sys.argv[1]
conn = sqlite3.connect(DB)
cur = conn.execute("UPDATE users SET is_admin = 1 WHERE username = ?", (username,))
if cur.rowcount == 0:
    print(f"User '{username}' not found")
    conn.close()
    sys.exit(1)
conn.commit()
conn.close()
print(f"User '{username}' is now admin")
