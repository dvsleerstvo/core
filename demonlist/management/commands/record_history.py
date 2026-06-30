from django.core.management.base import BaseCommand
from demonlist.models import User, UserScoreHistory

class Command(BaseCommand):
    help = 'Takes a snapshot of all users scores and ranks'

    def handle(self, *args, **options):
        # PC Ranks
        users_pc = User.objects.filter(score_pc__gt=0).order_by('-score_pc')
        pc_ranks = {user.id: rank for rank, user in enumerate(users_pc, 1)}

        # Mobile Ranks
        users_mobile = User.objects.filter(score_mobile__gt=0).order_by('-score_mobile')
        mobile_ranks = {user.id: rank for rank, user in enumerate(users_mobile, 1)}

        # All users who have at least one score
        users = User.objects.filter(score_pc__gt=0) | User.objects.filter(score_mobile__gt=0)
        users = users.distinct()

        history_objects = []
        for user in users:
            history_objects.append(UserScoreHistory(
                user=user,
                score_pc=user.score_pc,
                score_mobile=user.score_mobile,
                rank_pc=pc_ranks.get(user.id),
                rank_mobile=mobile_ranks.get(user.id)
            ))

        UserScoreHistory.objects.bulk_create(history_objects)
        self.stdout.write(self.style.SUCCESS(f'Successfully recorded history for {len(history_objects)} users'))
