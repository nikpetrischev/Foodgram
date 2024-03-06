
# Standard Library
import csv
import json
import os

# Django Library
from django.core.management.base import BaseCommand
from django.db import transaction

from foodgram_backend.settings import DATA_FOLDER
# Local Imports
from recipes.models import Ingredient

IMPORT_FILE = os.path.join(DATA_FOLDER, 'ingredients')


class Command(BaseCommand):
    """
    A Django management command for importing ingredients from a CSV or JSON file.

    This command provides functionality to import ingredients into the database
    from a specified CSV or JSON file. It supports atomic transactions to ensure
    data integrity during the import process.
    """
    help = 'Импорт списка ингредиентов из .csv или .json'
    requires_migrations_checks = True

    def add_arguments(self, parser):
        """
        Add command-line arguments to the parser.

        Parameters
        ----------
        parser : ArgumentParser
            The argument parser for the command.
        """
        parser.add_argument(
            '--json',
            action='store_true',
            help='Load from json instead of csv',
        )

    @transaction.atomic
    def import_csv(self):
        """
        Import ingredients from a CSV file.

        This method reads a CSV file containing ingredient data, creates
        Ingredient objects for each row, and saves them to the database.
        """
        with open(IMPORT_FILE + '.csv', encoding='UTF-8') as csv_file:
            csvreader = csv.reader(csv_file)
            _id: int = 0

            for row in csvreader:
                ingredient = {
                    'id': _id,
                    'name': row[0],
                    'measurement_unit': row[1],
                }
                Ingredient(**ingredient).save()
                _id += 1

    @transaction.atomic
    def import_json(self):
        """
         Import ingredients from a JSON file.

         This method reads a JSON file containing ingredient data, creates
         Ingredient objects for each item, and saves them to the database.
         """
        with open(IMPORT_FILE + '.json', encoding='UTF-8') as json_file:
            data = json.load(json_file)
            _id: int = 0

            for row in data:
                ingredient = {
                    'id': _id,
                    **row
                }
                Ingredient(**ingredient).save()
                _id += 1

    def handle(self, *args, **options):
        """
        Handle the command-line arguments and execute the import process.

        This method checks the command-line arguments to determine whether to
        import from a CSV or JSON file and then calls the appropriate import
        method.

        Parameters
        ----------
        *args : tuple
            Positional arguments passed to the command.
        **options : dict
            Keyword arguments passed to the command.
        """
        if options['json']:
            self.import_json()
        else:
            self.import_csv()
