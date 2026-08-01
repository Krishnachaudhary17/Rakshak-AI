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
    """Seed REAL Indian hospitals and government shelters for demo."""

    hospitals = [
        # (name, type, lat, lng, beds_available, icu_available, is_open, address, ventilators, oxygen_cylinders, blood_bank, generator, staff, incoming_pts, incoming_sev, infra_status, note)
        ("AIIMS New Delhi",            "hospital", 28.5672, 77.2100,   0,  12, 1, "Ansari Nagar, New Delhi",          20, 60, "stocked", "on", 120,  8, "critical", "stable", "Trauma centre fully operational"),
        ("Safdarjung Hospital",         "hospital", 28.5693, 77.2011,  65,   9, 1, "Ring Road, New Delhi",             14, 40, "stocked", "on",  88,  3, "moderate", "stable", ""),
        ("Ram Manohar Lohia Hospital",  "hospital", 28.6263, 77.2015,  38,   4, 1, "Baba Kharak Singh Marg, Delhi",   10, 30, "stocked", "on",  62,  0, "minor",    "stable", ""),
        ("KEM Hospital Mumbai",         "hospital", 19.0017, 72.8422,  42,   6, 1, "Acharya Donde Marg, Parel, Mumbai", 8, 25, "stocked", "on",  74,  5, "moderate", "stable", "Flood overflow ward open"),
        ("AIIMS Bhubaneswar",           "hospital", 20.2673, 85.8138,  55,   7, 1, "Sijua, Bhubaneswar, Odisha",      10, 35, "stocked", "on",  65,  2, "moderate", "stable", "Disaster response unit active"),
        ("NIMHANS Bengaluru",           "hospital", 12.9407, 77.5947,  90,   3, 1, "Hosur Road, Bengaluru",            5, 20, "stocked", "on",  55,  0, "minor",    "stable", ""),
        ("Government Medical College Thiruvananthapuram", "hospital", 8.5241, 76.9366, 30, 5, 1, "Thiruvananthapuram, Kerala", 9, 28, "stocked", "on", 70, 4, "moderate", "stable", "Flood relief admissions ongoing"),
        ("PGIMER Chandigarh",           "hospital", 30.7649, 76.7764,  18,   8, 1, "Sector 12, Chandigarh",           15, 45, "stocked", "on",  95,  6, "critical", "stable", ""),
        ("AIIMS Patna",                 "hospital", 25.6093, 85.0801,  10,   4, 1, "Phulwarisharif, Patna, Bihar",     8, 22, "low",     "on",  48,  9, "critical", "stable", "Flood season surge — high load"),
        ("Gauhati Medical College",     "hospital", 26.1827, 91.7496,   5,   3, 1, "Bhangagarh, Guwahati, Assam",     6, 18, "stocked", "on",  40,  7, "critical", "stable", "Brahmaputra flood victims admitted"),
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
        # (name, lat, lng, capacity, occupied, is_open, address, water_days, food_days, bedding, med_count, med_tags, hazard_note, supply_eta, skills_med, skills_eng, skills_trans)
        ("Jawaharlal Nehru Stadium Relief Camp, Delhi",     28.5871, 77.2403, 2000,  850, 1, "Pragati Maidan Area, New Delhi",        7, 5, "ok",  12, "dialysis,oxygen",      "Yamuna flood zone proximity",       "2026-08-03T08:00", 4, 2, 5),
        ("NDRF Camp Patna Ghat",                            25.6093, 85.0914, 3000, 2400, 1, "Gandhi Ghat, Patna, Bihar",             4, 3, "low",  28, "insulin,cardiac",      "High flood risk — Ganga rising",    "2026-08-02T06:00", 6, 3, 2),
        ("Kalinga Stadium Relief Centre, Bhubaneswar",      20.2960, 85.8188, 2500,  640, 1, "Nayapalli, Bhubaneswar, Odisha",        6, 6, "ok",   8, "psychiatric",          "Cyclone shelter — reinforced",      "",                 3, 4, 1),
        ("Government Arts College Camp, Guwahati",          26.1558, 91.7086, 1500, 1420, 1, "Pan Bazar, Guwahati, Assam",            2, 2, "low",  35, "insulin,oxygen,oxygen", "At near-capacity — Brahmaputra flood","2026-08-02T12:00", 5, 1, 4),
        ("Sardar Patel Stadium Camp, Ahmedabad",            23.0269, 72.5797, 1800,  300, 1, "Navrangpura, Ahmedabad, Gujarat",       8, 7, "ok",   4, "",                     "No active hazard",                  "",                 2, 3, 2),
        ("Indoor Stadium Relief Camp, Thiruvananthapuram",   8.5055, 76.9788, 1200,  890, 0, "Pattom, Thiruvananthapuram, Kerala",   1, 1, "out",   0, "",                     "CLOSED — at full capacity",         "",                 0, 0, 0),
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
        ("Flash Flood Warning — Yamuna Floodplain",   "flood",      "New Delhi",      28.6619, 77.2300, "high"),
        ("Landslide on NH-44 near Ramban",            "landslide",  "Jammu & Kashmir",33.2489, 75.2403, "high"),
        ("Earthquake Tremors Felt in Assam",          "earthquake", "Guwahati, Assam",26.1445, 91.7362, "moderate"),
        ("Cyclone Watch: Bay of Bengal Disturbance",  "cyclone",    "Odisha Coast",   19.8135, 85.8312, "moderate"),
        ("Building Fire Reported",                    "fire",       "Lajpat Nagar",   28.5665, 77.2433, "moderate"),
    ]
    for e in events_data:
        conn.execute(
            "INSERT OR IGNORE INTO events (title, disaster_type, location, lat, lng, severity) VALUES (?,?,?,?,?,?)",
            e
        )

    # --- Admin logins for each real facility ---
    demo_admins = [
        ("aiims_delhi",      "rakshak123", "hospital", "AIIMS New Delhi"),
        ("safdarjung",       "rakshak123", "hospital", "Safdarjung Hospital"),
        ("kem_mumbai",       "rakshak123", "hospital", "KEM Hospital Mumbai"),
        ("aiims_bbsr",       "rakshak123", "hospital", "AIIMS Bhubaneswar"),
        ("aiims_patna",      "rakshak123", "hospital", "AIIMS Patna"),
        ("gauhati_mc",       "rakshak123", "hospital", "Gauhati Medical College"),
        ("shelter_delhi",    "rakshak123", "shelter",  "Jawaharlal Nehru Stadium Relief Camp, Delhi"),
        ("shelter_patna",    "rakshak123", "shelter",  "NDRF Camp Patna Ghat"),
        ("shelter_bbsr",     "rakshak123", "shelter",  "Kalinga Stadium Relief Centre, Bhubaneswar"),
        ("shelter_guwahati", "rakshak123", "shelter",  "Government Arts College Camp, Guwahati"),
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
