import sqlite3
import json
import os

DB_FILE = "rfp_database.db"
DATA_DIR = "data"
INVENTORY_FILE = os.path.join(DATA_DIR, "inventory.json")
PRICING_FILE = os.path.join(DATA_DIR, "pricing_rules.json")

def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def initialize_db():
    """Creates tables and loads initial data if empty."""
    conn = get_db_connection()
    cursor = conn.cursor()

    # Create Tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS inventory (
            sku TEXT PRIMARY KEY,
            name TEXT,
            category TEXT,
            base_cost REAL,
            description TEXT
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pricing_rules (
            key TEXT PRIMARY KEY,
            value REAL
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS rfp_requests (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
            input_text TEXT,
            sales_data TEXT,
            tech_data TEXT,
            pricing_data TEXT,
            final_response TEXT,
            status TEXT DEFAULT 'Pending'
        )
    ''')

    # Migration: Add status column if it doesn't exist (for existing DBs)
    try:
        cursor.execute('ALTER TABLE rfp_requests ADD COLUMN status TEXT DEFAULT "Pending"')
    except sqlite3.OperationalError:
        pass # Column likely already exists

    # Check if inventory is empty
    cursor.execute('SELECT count(*) FROM inventory')
    if cursor.fetchone()[0] == 0:
        print("[Database] Migrating Inventory from JSON...")
        if os.path.exists(INVENTORY_FILE):
            with open(INVENTORY_FILE, 'r', encoding='utf-8') as f:
                items = json.load(f)
                for item in items:
                    cursor.execute('''
                        INSERT INTO inventory (sku, name, category, base_cost, description)
                        VALUES (?, ?, ?, ?, ?)
                    ''', (item['sku'], item['name'], item['category'], item['base_cost'], item.get('description', '')))
        conn.commit()

    # Check if pricing rules are empty
    cursor.execute('SELECT count(*) FROM pricing_rules')
    if cursor.fetchone()[0] == 0:
        print("[Database] Migrating Pricing Rules from JSON...")
        if os.path.exists(PRICING_FILE):
            with open(PRICING_FILE, 'r', encoding='utf-8') as f:
                rules = json.load(f)
                for key, value in rules.items():
                    cursor.execute('INSERT INTO pricing_rules (key, value) VALUES (?, ?)', (key, value))
        conn.commit()

    conn.close()
    print("[Database] Initialization Complete.")

def get_inventory():
    conn = get_db_connection()
    items = conn.execute('SELECT * FROM inventory').fetchall()
    conn.close()
    return [dict(item) for item in items]

def get_pricing_rules():
    conn = get_db_connection()
    rules = conn.execute('SELECT * FROM pricing_rules').fetchall()
    conn.close()
    return {rule['key']: rule['value'] for rule in rules}

def save_rfp_request(input_text, sales, tech, pricing, final):
    conn = get_db_connection()
    conn.execute('''
        INSERT INTO rfp_requests (input_text, sales_data, tech_data, pricing_data, final_response, status)
        VALUES (?, ?, ?, ?, ?, 'Pending')
    ''', (input_text, json.dumps(sales), json.dumps(tech), json.dumps(pricing), json.dumps(final)))
    conn.commit()
    conn.close()

def get_dashboard_stats():
    conn = get_db_connection()
    
    # Status Counts
    stats = conn.execute('SELECT status, COUNT(*) as count FROM rfp_requests GROUP BY status').fetchall()
    status_counts = {row['status']: row['count'] for row in stats}
    
    # Recent Activity
    recent = conn.execute('SELECT id, timestamp, status, sales_data FROM rfp_requests ORDER BY timestamp DESC LIMIT 5').fetchall()
    recent_activity = []
    for row in recent:
        sales = json.loads(row['sales_data'])
        title = sales.get('rfp_metadata', {}).get('title', 'Unknown RFP')
        recent_activity.append({
            "id": row['id'],
            "date": row['timestamp'],
            "status": row['status'],
            "title": title
        })

    conn.close()
    
    return {
        "approved": status_counts.get('Approved', 0),
        "declined": status_counts.get('Declined', 0),
        "pending": status_counts.get('Pending', 0),
        "recent_activity": recent_activity
    }

def add_product(product):
    conn = get_db_connection()
    try:
        conn.execute('''
            INSERT INTO inventory (sku, name, category, base_cost, description)
            VALUES (?, ?, ?, ?, ?)
        ''', (product['sku'], product['name'], product['category'], product['base_cost'], product.get('description', '')))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False # SKU likely exists
    finally:
        conn.close()
