# Standart Library
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
    help = 'Импорт списка ингредиентов из .csv или .json'
    requires_migrations_checks = True

    def add_arguments(self, parser):
        parser.add_argument(
            '--json',
            action='store_true',
            help='Load from json instead of csv',
        )

    @transaction.atomic
    def import_csv(self):
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
        if options['json']:
            self.import_json()
        else:
            self.import_csv()
