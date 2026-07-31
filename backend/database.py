import sqlite3

DB_PATH = "rakshak.db"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS facilities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            type TEXT DEFAULT 'hospital',
            lat REAL,
            lng REAL,
            beds_available INTEGER DEFAULT 0,
            icu_available INTEGER DEFAULT 0,
            is_open INTEGER DEFAULT 1,
            address TEXT
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            disaster_type TEXT,
            location TEXT,
            lat REAL,
            lng REAL,
            severity TEXT DEFAULT 'moderate',
            timestamp TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS shelters (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE,
            lat REAL,
            lng REAL,
            capacity INTEGER DEFAULT 0,
            occupied INTEGER DEFAULT 0,
            is_open INTEGER DEFAULT 1,
            address TEXT
        )
    """)
    conn.commit()
    _seed_demo_data(conn)
    conn.close()

def _seed_demo_data(conn):
    """Seed mock data so the demo looks real from the start."""
    hospitals = [
        ("City General Hospital", "hospital", 28.6139, 77.2090, 45, 2, 1, "Connaught Place, New Delhi"),
        ("Mercy Medical Center", "hospital", 28.6329, 77.2195, 12, 0, 1, "Karol Bagh, New Delhi"),
        ("AIIMS Trauma Centre", "hospital", 28.5672, 77.2100, 0, 5, 1, "Ansari Nagar, New Delhi"),
        ("Safdarjung Hospital", "hospital", 28.5693, 77.2011, 78, 8, 1, "Ring Road, New Delhi"),
        ("Ram Manohar Lohia Hospital", "hospital", 28.6263, 77.2015, 34, 3, 1, "Baba Kharak Singh Marg, New Delhi"),
    ]
    for h in hospitals:
        conn.execute(
            "INSERT OR IGNORE INTO facilities (name, type, lat, lng, beds_available, icu_available, is_open, address) VALUES (?,?,?,?,?,?,?,?)",
            h
        )

    shelters = [
        ("Nehru Stadium Shelter", 28.5871, 77.2403, 500, 120, 1, "Pragati Maidan Area"),
        ("DDA Sports Complex", 28.6304, 77.2177, 300, 88, 1, "Saket, New Delhi"),
        ("Government School Shelter", 28.6503, 77.2343, 200, 200, 0, "Civil Lines, New Delhi"),
    ]
    for s in shelters:
        conn.execute(
            "INSERT OR IGNORE INTO shelters (name, lat, lng, capacity, occupied, is_open, address) VALUES (?,?,?,?,?,?,?)",
            s
        )

    events_data = [
        ("Flash Flood Warning", "flood", "Yamuna Floodplain", 28.6619, 77.2300, "high"),
        ("Building Fire Reported", "fire", "Lajpat Nagar", 28.5665, 77.2433, "moderate"),
        ("Earthquake Tremors Felt", "earthquake", "NCR Region", 28.5355, 77.3910, "low"),
    ]
    for e in events_data:
        conn.execute(
            "INSERT OR IGNORE INTO events (title, disaster_type, location, lat, lng, severity) VALUES (?,?,?,?,?,?)",
            e
        )
    conn.commit()
