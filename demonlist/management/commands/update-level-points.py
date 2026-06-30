from django.core.management.base import BaseCommand
from demonlist.utils import update_levels_from_api

class Command(BaseCommand):
    def handle(self, *args, **options):
        update_levels_from_api('PC')
        update_levels_from_api('Mobile')
        self.stdout.write(self.style.SUCCESS('Done'))