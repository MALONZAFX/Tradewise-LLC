import os
import django
from django.db import connection

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dict.settings')
django.setup()

def fix_database():
    print("🔧 Starting database repair...")
    
    with connection.cursor() as cursor:
        try:
            # 1. Check current tables
            print("📊 Checking current tables...")
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public' AND table_name LIKE 'myapp_%'
                ORDER BY table_name
            """)
            tables = cursor.fetchall()
            print("Existing myapp tables:")
            for table in tables:
                print(f"  - {table[0]}")
            
            # 2. Drop problematic tables
            print("🗑️ Removing problematic tables...")
            cursor.execute("DROP TABLE IF EXISTS myapp_review CASCADE")
            cursor.execute("DROP TABLE IF EXISTS myapp_adminlog CASCADE")
            print("  - Dropped myapp_review and myapp_adminlog")
            
            # 3. Fix tradewisecard table
            print("🔧 Fixing tradewisecard table...")
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'myapp_tradewisecard' AND column_name = 'user_id'
            """)
            if not cursor.fetchone():
                cursor.execute("""
                    ALTER TABLE myapp_tradewisecard 
                    ADD COLUMN user_id INTEGER REFERENCES auth_user(id)
                """)
                print("  - Added user_id to tradewisecard")
            else:
                print("  - user_id already exists in tradewisecard")
            
            # 4. Fix tradewisecoin table
            print("🔧 Fixing tradewisecoin table...")
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'myapp_tradewisecoin' AND column_name = 'user_id'
            """)
            if not cursor.fetchone():
                cursor.execute("""
                    ALTER TABLE myapp_tradewisecoin 
                    ADD COLUMN user_id INTEGER REFERENCES auth_user(id)
                """)
                print("  - Added user_id to tradewisecoin")
            else:
                print("  - user_id already exists in tradewisecoin")
            
            # 5. Fix blogpost table
            print("🔧 Fixing blogpost table...")
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'myapp_blogpost' AND column_name = 'slug'
            """)
            if not cursor.fetchone():
                cursor.execute("""
                    ALTER TABLE myapp_blogpost ADD COLUMN slug VARCHAR(255)
                """)
                print("  - Added slug to blogpost")
            else:
                print("  - slug already exists in blogpost")
            
            # 6. Fix testimonial table
            print("🔧 Fixing testimonial table...")
            cursor.execute("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'myapp_testimonial' AND column_name = 'is_approved'
            """)
            if not cursor.fetchone():
                cursor.execute("""
                    ALTER TABLE myapp_testimonial 
                    ADD COLUMN is_approved BOOLEAN DEFAULT FALSE
                """)
                print("  - Added is_approved to testimonial")
            else:
                print("  - is_approved already exists in testimonial")
            
            # 7. Reset migration history
            print("🔄 Resetting migration history...")
            cursor.execute("DELETE FROM django_migrations WHERE app = 'myapp'")
            print("  - Reset myapp migrations")
            
            print("✅ Database repair completed successfully!")
            
        except Exception as e:
            print(f"❌ Error during database repair: {e}")
            raise

if __name__ == "__main__":
    fix_database()