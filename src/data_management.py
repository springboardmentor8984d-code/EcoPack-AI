import pandas as pd
import sqlite3
import os

def initialize_database(csv_path, db_path):
    """
    Load CSV data into a SQLite database.
    """
    if not os.path.exists(csv_path):
        print(f"Error: {csv_path} not found.")
        return

    # Read CSV
    df = pd.read_csv(csv_path)
    
    # Connect to SQLite
    conn = sqlite3.connect(db_path)
    
    # Save to database
    df.to_sql('materials', conn, if_exists='replace', index=False)
    
    print(f"Database initialized at {db_path} with {len(df)} records.")
    conn.close()

if __name__ == "__main__":
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    CSV_FILE = os.path.join(BASE_DIR, 'data', 'raw_materials.csv')
    DB_FILE = os.path.join(BASE_DIR, 'data', 'ecopack.db')
    initialize_database(CSV_FILE, DB_FILE)
