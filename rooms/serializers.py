import secrets
from rest_framework import serializers
from .models import Room, RoomVote

class RoomSerializer(serializers.ModelSerializer):
    creator_name = serializers.CharField(source='creator.username', read_only=True)
    member_count = serializers.SerializerMethodField()
    is_creator = serializers.SerializerMethodField()
    invite_link = serializers.SerializerMethodField()
    members = serializers.SerializerMethodField()

    class Meta:
        model = Room
        fields = ['id', 'code', 'creator', 'creator_name', 'invite_code', 'invite_link', 'member_count', 'is_creator', 'members', 'created_at', 'is_active']
        read_only_fields = ['id', 'creator', 'invite_code', 'created_at']

    def get_member_count(self, obj):
        return obj.members.count() + 1

    def get_is_creator(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return request.user.id == obj.creator_id
        return False

    def get_invite_link(self, obj):
        if not obj.invite_code:
            obj.invite_code = secrets.token_urlsafe(16)
            obj.save(update_fields=['invite_code'])
        return f"http://127.0.0.1:3000/?room={obj.invite_code}"

    def get_members(self, obj):
        return [{'id': u.id, 'username': u.username} for u in obj.members.all()]