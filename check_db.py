import os
import django
from django.db import connection

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dict.settings')
django.setup()

def check_tables():
    with connection.cursor() as cursor:
        # Check existing tables
        cursor.execute("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        tables = cursor.fetchall()
        print("=== EXISTING TABLES ===")
        for table in tables:
            print(f"Table: {table[0]}")
        
        # Check django_migrations
        print("\n=== MIGRATIONS ===")
        try:
            cursor.execute("SELECT app, name, applied FROM django_migrations WHERE app = 'myapp'")
            migrations = cursor.fetchall()
            for mig in migrations:
                print(f"App: {mig[0]}, Migration: {mig[1]}, Applied: {mig[2]}")
        except Exception as e:
            print(f"Error reading migrations: {e}")

if __name__ == "__main__":
    check_tables()