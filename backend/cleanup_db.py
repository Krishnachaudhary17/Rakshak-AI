import sqlite3
conn = sqlite3.connect('rakshak.db')

# Remove junk non-disaster articles (unclassified 'disaster' type with low severity = generic news)
deleted = conn.execute("DELETE FROM events WHERE disaster_type = 'disaster' AND severity = 'low'").rowcount
print(f'Removed {deleted} junk news entries')

# Remove duplicate seed events (keep the lowest id for each title)
dupes = conn.execute("DELETE FROM events WHERE id NOT IN (SELECT MIN(id) FROM events GROUP BY title)").rowcount
print(f'Removed {dupes} duplicate seed events')

conn.commit()

# Show what's left
rows = conn.execute('SELECT id, title, disaster_type, severity FROM events ORDER BY id').fetchall()
print(f'\n{len(rows)} events remaining:')
for r in rows:
    print(r)
conn.close()
