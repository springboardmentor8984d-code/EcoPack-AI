import pandas as pd
import os
from sqlalchemy import create_engine, text
from db_utils import get_db_engine, get_db_connection_url

def create_database_if_not_exists():
    """
    Connect to default 'postgres' db to create 'ecopack_db' if it doesn't exist.
    """
    try:
        # Use simple string replacement for the connection URL to connect to 'postgres'
        # This assumes get_db_connection_url returns a valid URL string
        default_db_url = get_db_connection_url(db_name='postgres')
        engine = create_engine(default_db_url, isolation_level="AUTOCOMMIT")
        
        target_db = os.getenv('DB_NAME', 'ecopack_db')
        
        with engine.connect() as conn:
            # Check if database exists
            result = conn.execute(text(f"SELECT 1 FROM pg_database WHERE datname='{target_db}'"))
            if not result.fetchone():
                print(f"Database '{target_db}' does not exist. Creating...")
                conn.execute(text(f"CREATE DATABASE {target_db}"))
                print(f"Database '{target_db}' created successfully.")
            else:
                print(f"Database '{target_db}' already exists.")
                
    except Exception as e:
        print(f"Warning: Could not check/create database automatically. Error: {e}")
        print("Please ensure the database exists manually if the next steps fail.")

def initialize_database(csv_path):
    """
    Load CSV data into the PostgreSQL database.
    """
    create_database_if_not_exists()
    
    if not os.path.exists(csv_path):
        print(f"Error: {csv_path} not found.")
        return

    try:
        engine = get_db_engine()
        df = pd.read_csv(csv_path)
        with engine.begin() as conn:
            df.to_sql('raw_materials', conn, if_exists='replace', index=False)
        print(f"Successfully loaded {len(df)} rows into database")
    except Exception as e:
        print(f"Failed to initialize database: {e}")

if __name__ == "__main__":
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    CSV_FILE = os.path.join(BASE_DIR, 'data', 'raw_materials.csv')
    initialize_database(CSV_FILE)
