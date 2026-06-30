from rest_framework import serializers
from .models import Level, User, Victor, DiscordLink, RecordRequest

class LevelSerializer(serializers.ModelSerializer):
    embed_url = serializers.ReadOnlyField()

    class Meta:
        model = Level
        fields = '__all__'

class UserSerializer(serializers.ModelSerializer):
    is_online = serializers.ReadOnlyField()
    region_display = serializers.CharField(source='get_region_display', read_only=True)
    hardest_pc_name = serializers.CharField(source='hardest_pc.name', read_only=True)
    hardest_mobile_name = serializers.CharField(source='hardest_mobile.name', read_only=True)
    rank = serializers.IntegerField(required=False, read_only=True)

    class Meta:
        model = User
        fields = '__all__'

class VictorSerializer(serializers.ModelSerializer):
    username_detail = UserSerializer(source='username', read_only=True)
    level_detail = LevelSerializer(source='level', read_only=True)
    embed_url = serializers.ReadOnlyField()

    class Meta:
        model = Victor
        fields = [
            'id', 'username', 'level', 'progress', 'device', 'youtube', 
            'is_first_victor', 'created_at', 'username_detail', 'level_detail', 'embed_url'
        ]

class DiscordLinkSerializer(serializers.ModelSerializer):
    discord_id = serializers.SerializerMethodField()

    class Meta:
        model = DiscordLink
        fields = ['notifications_enabled', 'discord_id']

    def get_discord_id(self, obj):
        try:
            from allauth.socialaccount.models import SocialAccount
            return SocialAccount.objects.get(user=obj.auth_user, provider='discord').uid
        except Exception:
            return None

class RecordRequestSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    user_detail = UserSerializer(source='user', read_only=True)
    level_detail = LevelSerializer(source='level', read_only=True)

    class Meta:
        model = RecordRequest
        fields = ['id', 'user', 'level', 'progress', 'video', 'device', 'status', 'notes', 'created_at', 'status_display', 'user_detail', 'level_detail']
