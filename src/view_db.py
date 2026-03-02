import pandas as pd
from sqlalchemy import text
from db_utils import get_db_engine

def view_database_content():
    engine = get_db_engine()
    
    print("-" * 50)
    print("Checking PostgreSQL Database Content...")
    print("-" * 50)

    try:
        with engine.connect() as conn:
            # Check raw_materials table
            print("\nTable: raw_materials (Top 5 rows)")
            try:
                df_raw = pd.read_sql_query(text("SELECT * FROM raw_materials LIMIT 5"), conn)
                if not df_raw.empty:
                    print(df_raw.to_string(index=False))
                else:
                    print("(Table is empty)")
            except Exception as e:
                print(f"Error reading raw_materials: {e}")

            print("-" * 50)

            # Check materials_processed table
            print("\nTable: materials_processed (Top 5 rows)")
            try:
                df_proc = pd.read_sql_query(text("SELECT * FROM materials_processed LIMIT 5"), conn)
                if not df_proc.empty:
                    # Select a subset of columns to fit on screen
                    cols = ['Material_Type', 'Cost_Per_Unit', 'CO2_Emission_Score', 'Strength_MPa', 'Material_Suitability_Score', 'final_score']
                    # Filter columns that exist
                    cols = [c for c in cols if c in df_proc.columns]
                    print(df_proc[cols].to_string(index=False))
                else:
                    print("(Table is empty)")
            except Exception as e:
                print(f"Error reading materials_processed: {e}")
                
    except Exception as e:
        print(f"Failed to connect to database: {e}")
        print("Make sure your .env file is correct and PostgreSQL is running.")

if __name__ == "__main__":
    view_database_content()
