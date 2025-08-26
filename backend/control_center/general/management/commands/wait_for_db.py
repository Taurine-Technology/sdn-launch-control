"""
Django command to pause execution until database is available.
"""
from django.core.management.base import BaseCommand
from django.db import OperationalError
import time
from psycopg2 import OperationalError as Psycopg2Error


class Command(BaseCommand):
    """Django command to pause execution until database is available."""
    def handle(self, *args, **options):
        """Entry point for Django management command."""
        self.stdout.write('Waiting for database...')
        db_up = False
        while not db_up:
            try:
                self.check(databases=['default'])
                db_up = True
            except (OperationalError, Psycopg2Error):
                self.stdout.write(self.style.ERROR('Database error..'))
                time.sleep(3)
        self.stdout.write(self.style.SUCCESS('Database available.'))