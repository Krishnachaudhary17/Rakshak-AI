import sqlite3
import bcrypt

DB_PATH = "rakshak.db"

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()

    # --- Original tables ---
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
            address TEXT,
            ventilators INTEGER DEFAULT 0,
            oxygen_cylinders INTEGER DEFAULT 0,
            blood_bank_status TEXT DEFAULT 'stocked',
            generator_status TEXT DEFAULT 'on',
            staff_on_duty INTEGER DEFAULT 0,
            incoming_patients INTEGER DEFAULT 0,
            incoming_severity TEXT DEFAULT 'moderate',
            infrastructure_status TEXT DEFAULT 'stable',
            situation_note TEXT DEFAULT '',
            last_updated TEXT DEFAULT (datetime('now'))
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
            address TEXT,
            water_supply_days INTEGER DEFAULT 3,
            food_supply_days INTEGER DEFAULT 3,
            bedding_status TEXT DEFAULT 'ok',
            medical_needs_count INTEGER DEFAULT 0,
            medical_needs_tags TEXT DEFAULT '',
            hazard_note TEXT DEFAULT '',
            next_supply_eta TEXT DEFAULT '',
            skills_medical INTEGER DEFAULT 0,
            skills_engineering INTEGER DEFAULT 0,
            skills_translation INTEGER DEFAULT 0,
            last_updated TEXT DEFAULT (datetime('now'))
        )
    """)

    # --- Admin users table ---
    conn.execute("""
        CREATE TABLE IF NOT EXISTS admin_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('hospital','shelter')),
            facility_name TEXT NOT NULL
        )
    """)

    conn.commit()
    _seed_demo_data(conn)
    conn.close()


def _seed_demo_data(conn):
    """Seed mock data so the demo looks real from the start."""
    hospitals = [
        ("City General Hospital", "hospital", 28.6139, 77.2090, 45, 2, 1, "Connaught Place, New Delhi", 8, 20, "stocked", "on", 32, 0, "moderate", "stable", ""),
        ("Mercy Medical Center", "hospital", 28.6329, 77.2195, 12, 0, 1, "Karol Bagh, New Delhi", 3, 10, "low", "on", 18, 4, "critical", "stable", ""),
        ("AIIMS Trauma Centre", "hospital", 28.5672, 77.2100, 0, 5, 1, "Ansari Nagar, New Delhi", 12, 30, "stocked", "on", 55, 8, "critical", "stable", ""),
        ("Safdarjung Hospital", "hospital", 28.5693, 77.2011, 78, 8, 1, "Ring Road, New Delhi", 10, 25, "stocked", "on", 40, 2, "minor", "stable", ""),
        ("Ram Manohar Lohia Hospital", "hospital", 28.6263, 77.2015, 34, 3, 1, "Baba Kharak Singh Marg, New Delhi", 6, 15, "stocked", "on", 28, 0, "moderate", "stable", ""),
    ]
    for h in hospitals:
        conn.execute(
            """INSERT OR IGNORE INTO facilities 
               (name, type, lat, lng, beds_available, icu_available, is_open, address,
                ventilators, oxygen_cylinders, blood_bank_status, generator_status,
                staff_on_duty, incoming_patients, incoming_severity, infrastructure_status, situation_note)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            h
        )

    shelters = [
        ("Nehru Stadium Shelter", 28.5871, 77.2403, 500, 120, 1, "Pragati Maidan Area", 5, 4, "ok", 3, "dialysis,oxygen", "No active hazards", "", 2, 1, 3),
        ("DDA Sports Complex", 28.6304, 77.2177, 300, 88, 1, "Saket, New Delhi", 3, 2, "low", 7, "insulin,psychiatric", "Flooding risk from south", "2026-08-02T10:00", 5, 0, 1),
        ("Government School Shelter", 28.6503, 77.2343, 200, 200, 0, "Civil Lines, New Delhi", 1, 1, "out", 0, "", "CLOSED — at capacity", "", 0, 0, 0),
    ]
    for s in shelters:
        conn.execute(
            """INSERT OR IGNORE INTO shelters 
               (name, lat, lng, capacity, occupied, is_open, address,
                water_supply_days, food_supply_days, bedding_status,
                medical_needs_count, medical_needs_tags, hazard_note,
                next_supply_eta, skills_medical, skills_engineering, skills_translation)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
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

    # --- Seed demo admin users ---
    demo_admins = [
        ("hospital1", "rakshak123", "hospital", "City General Hospital"),
        ("hospital2", "rakshak123", "hospital", "AIIMS Trauma Centre"),
        ("shelter1",  "rakshak123", "shelter",  "Nehru Stadium Shelter"),
        ("shelter2",  "rakshak123", "shelter",  "DDA Sports Complex"),
    ]
    for username, password, role, facility in demo_admins:
        existing = conn.execute(
            "SELECT id FROM admin_users WHERE username=?", (username,)
        ).fetchone()
        if not existing:
            pw_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
            conn.execute(
                "INSERT INTO admin_users (username, password_hash, role, facility_name) VALUES (?,?,?,?)",
                (username, pw_hash, role, facility)
            )

    conn.commit()
