# myapp/management/commands/check_tables.py
from django.core.management.base import BaseCommand
from django.db import connection

class Command(BaseCommand):
    help = 'Check existing tables in database'

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
            """)
            tables = cursor.fetchall()
            for table in tables:
                self.stdout.write(f"Table: {table[0]}")