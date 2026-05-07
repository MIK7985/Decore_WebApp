import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'decore_developers.settings')
django.setup()

from django.db import connection

def reset_ids():
    print("Resetting all ID sequences back to 1...")
    with connection.cursor() as cursor:
        cursor.execute("DELETE FROM sqlite_sequence;")
    print("✅ Sequences reset! New employees and records will now start at 1 (e.g. DC001).")

if __name__ == '__main__':
    reset_ids()
