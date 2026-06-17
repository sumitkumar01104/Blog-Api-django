from rest_framework import serializers
from .models import Post, Comment, Like

class CommentSerializer(serializers.ModelSerializer):
    author = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'author', 'content', 'created_at']

class LikeSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Like
        fields = ['id', 'user']

class PostSerializer(serializers.ModelSerializer):
    author = serializers.StringRelatedField(read_only=True)
    comments = CommentSerializer(many=True, read_only=True)   # ← nested comments
    total_likes = serializers.SerializerMethodField()          # ← like count

    class Meta:
        model = Post
        fields = ['id', 'title', 'author', 'content', 'created_at', 'updated_at', 'comments', 'total_likes']

    def get_total_likes(self, obj):
        return obj.likes.count()