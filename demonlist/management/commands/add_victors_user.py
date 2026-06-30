from django.core.management import BaseCommand
from demonlist.utils import add_victors
file = open('/app/demonlist/management/commands/all_players_dvsleerstvo', 'r')

a = set()

class Command(BaseCommand):
    def handle(self, *args, **options):
        for line in file.read().splitlines():
            a.add(line)
        add_victors(list(a))