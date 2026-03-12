import sqlite3
from datetime import datetime

conn = sqlite3.connect("queue.db")
c = conn.cursor()

# Drop table if exists (fresh start)
c.execute("DROP TABLE IF EXISTS queues")

# Create table
c.execute("""
CREATE TABLE queues (
    place TEXT PRIMARY KEY,
    count INTEGER,
    last_update TEXT
)
""")

# Initialize with some locations
locations = ["Apollo Hospital", "SBI Bank", "Railway Counter", "College Office", "Food Court"]
for loc in locations:
    c.execute("INSERT INTO queues VALUES (?,?,?)", (loc, 0, datetime.now().isoformat()))

conn.commit()
conn.close()
print("Database created and initialized.")