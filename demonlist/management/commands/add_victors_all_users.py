from django.core.management import BaseCommand

from demonlist.models import User
from demonlist.utils import add_victors

class Command(BaseCommand):
    def handle(self, *args, **options):
        username = User.objects.all()
        for user in username:
            usernames_list = [user.username]
            add_victors(usernames_list)
