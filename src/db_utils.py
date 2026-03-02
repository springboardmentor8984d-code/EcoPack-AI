import os
from sqlalchemy import create_engine
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def get_db_connection_url(db_name=None):
    user = os.getenv('DB_USER', 'postgres')
    password = os.getenv('DB_PASSWORD', 'postgre') # Default fallback
    host = os.getenv('DB_HOST', 'localhost')
    port = os.getenv('DB_PORT', '5432')
    
    # Use the provided db_name or fallback to env/default
    if db_name is None:
        db_name = os.getenv('DB_NAME', 'ecopack_db')
        
    return f"postgresql://{user}:{password}@{host}:{port}/{db_name}"

def get_db_engine(db_name=None):
    db_url = get_db_connection_url(db_name)
    return create_engine(db_url)
