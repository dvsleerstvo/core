from django.core.management.base import BaseCommand
from demonlist.utils import calculate_user_scores
from demonlist.models import User

class Command(BaseCommand):
    def handle(self, *args, **options):
        updated = 0
        for user in User.objects.all():
            calculate_user_scores(user)
            updated += 1
            print(user.score_pc)
            print(user.score_mobile)

        self.stdout.write(f'Обновлено {updated} пользователей.')
