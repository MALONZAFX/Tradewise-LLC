# fix_migrations.py - NUCLEAR OPTION
import os
import django
from django.core.management import execute_from_command_line

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dict.settings')
django.setup()

def nuclear_fix():
    """Complete migration reset"""
    print("🚀 STARTING NUCLEAR MIGRATION FIX...")
    
    # 1. Delete all migration files
    migrations_dir = 'myapp/migrations'
    if os.path.exists(migrations_dir):
        for file in os.listdir(migrations_dir):
            if file != '__init__.py':
                file_path = os.path.join(migrations_dir, file)
                if os.path.isfile(file_path):
                    os.remove(file_path)
                    print(f"🗑️ Deleted: {file}")
    
    # 2. Create fresh migration
    print("📦 Creating fresh migration...")
    execute_from_command_line(['manage.py', 'makemigrations', 'myapp'])
    
    # 3. Apply migration with fake option
    print("🔧 Applying migrations...")
    execute_from_command_line(['manage.py', 'migrate', '--fake-initial'])
    
    print("✅ MIGRATION FIX COMPLETED!")

if __name__ == '__main__':
    nuclear_fix()