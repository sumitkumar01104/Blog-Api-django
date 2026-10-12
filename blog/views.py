from rest_framework import generics, status
from django.shortcuts import render, get_object_or_404
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, AllowAny, SAFE_METHODS
from rest_framework.exceptions import PermissionDenied
from .models import Post, Comment, Like
from .serializers import PostSerializer, CommentSerializer
from django.contrib.auth.models import User
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.exceptions import ValidationError
from rest_framework import serializers
from drf_spectacular.utils import extend_schema, inline_serializer

def blog(req):
    return render(req, 'blog-frontend.html')


# ______________________POST & GET ______________________________!
class PostListCreateView(generics.ListCreateAPIView):
    queryset = (
        Post.objects.all()
        .select_related('author')
        .prefetch_related('comments__author', 'likes')
        .order_by('-created_at')
    )
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]  # GET sabke liye, POST login ke baad

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)


# _______________________DELETE UPDATE & PUT PATCH _________________!
class PostDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        if self.request.method in SAFE_METHODS:  # padhna sabke liye
            return Post.objects.all()
        return Post.objects.filter(author=self.request.user)  # edit/delete sirf apna


# ________________________________Register____________________!
class RegisterView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        request=inline_serializer('RegisterRequest', {
            'username': serializers.CharField(),
            'password': serializers.CharField(),
        }),
        responses={201: inline_serializer('RegisterResponse', {'message': serializers.CharField()})},
    )
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        if not username or not password:
            return Response({'error': 'Username and password are both required'}, status=400)

        if User.objects.filter(username=username).exists():
            return Response({'error': 'User already exists'}, status=400)

        try:
            validate_password(password, user=User(username=username))
        except ValidationError as e:
            return Response({'error': e.messages}, status=400)

        User.objects.create_user(username=username, password=password)
        return Response({'message': 'User created'}, status=status.HTTP_201_CREATED)


# ____________________________ Comment Views ______________________________!
class CommentCreateView(generics.CreateAPIView):
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        post = get_object_or_404(Post, pk=self.kwargs['pk'])
        serializer.save(author=self.request.user, post=post)


class CommentDeleteView(generics.DestroyAPIView):
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Comment.objects.filter(author=self.request.user)  # sirf apna comment delete


# ______________________________ Like View — toggle (like/unlike) ___________________!
class LikeToggleView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        request=None,
        responses={200: inline_serializer('LikeResponse', {'message': serializers.CharField()})},
    )
    def post(self, request, pk):
        post = get_object_or_404(Post, pk=pk)
        like, created = Like.objects.get_or_create(user=request.user, post=post)

        if not created:
            like.delete()  # already like tha → unlike
            return Response({'message': 'Unliked!'})

        return Response({'message': 'Liked!'})


# ___________________________self blog _______________________!
class UserPostListView(generics.ListAPIView):
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        username = self.kwargs['username']
        user = self.request.user

        # Superuser — sabki posts dekh sakta hai
        if user.is_superuser:
            return Post.objects.filter(author__username=username).order_by('-created_at')

        # Normal user — sirf apni posts dekh sakta hai
        if user.username == username:
            return Post.objects.filter(author=user).order_by('-created_at')

        # Koi aur ka profile — forbidden
        raise PermissionDenied("You can only view your own posts!")


# _____________________________Logout_____________________________________!
class LogoutView(APIView):
    @extend_schema(
        request=inline_serializer('LogoutRequest', {'refresh': serializers.CharField()}),
        responses={200: inline_serializer('LogoutResponse', {'message': serializers.CharField()})},
    )
    def post(self, request):
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response({'error': 'Refresh token is required'}, status=400)
        try:
            RefreshToken(refresh_token).blacklist()  # Token blacklist karo
        except Exception:
            return Response({'error': 'Invalid token'}, status=400)
        return Response({'message': 'Logged out!'})