from rest_framework import generics
from django.shortcuts import render
from rest_framework.permissions import IsAuthenticated
from .models import Post,Comment, Like
from .serializers import PostSerializer, CommentSerializer
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.contrib.auth.password_validation import validate_password
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import serializers as drf_serializers

def blog(req):
    return render(req,'blog-frontend.html')
# ______________________POST & GET ______________________________!
class PostListCreateView(generics.ListCreateAPIView):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated]
    
    def perform_create(self, serializer):
        serializer.save(author=self.request.user)
        
        


# _______________________DELETE UPADTE & PUT PATCH _________________!
class PostDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated]
    def get_queryset(self):
        return Post.objects.filter(author=self.request.user)
    
    
    

# ________________________________Register____________________!
class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        if not username or not password:
            return Response({'error': 'Username aur password dono chahiye'}, status=400)

        if User.objects.filter(username=username).exists():
            return Response({'error': 'User already exists'}, status=400)

        try:
            validate_password(password)  # ← Django ka built-in validation
        except Exception as e:
            return Response({'error': list(e)}, status=400)

        user = User.objects.create_user(username=username, password=password)
        return Response({'message': 'User created!'}, status=201)

#____________________________ Comment Views ______________________________!
class CommentCreateView(generics.CreateAPIView):
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        post = Post.objects.get(pk=self.kwargs['pk'])
        serializer.save(author=self.request.user, post=post)

class CommentDeleteView(generics.DestroyAPIView):
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Comment.objects.filter(author=self.request.user)  # sirf apna comment delete


# ______________________________ Like View — toggle (like/unlike) ___________________!
class LikeToggleView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        post = Post.objects.get(pk=pk)
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
            return Post.objects.filter(author__username=username)
        
        # Normal user — sirf apni posts dekh sakta hai
        if user.username == username:
            return Post.objects.filter(author=user)
        
        # Koi aur ka profile — forbidden
        from rest_framework.exceptions import PermissionDenied
        raise PermissionDenied("Tum sirf apni posts dekh sakte ho!")
# _____________________________Logout_____________________________________!
class LogoutView(APIView):
    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            token = RefreshToken(refresh_token)
            token.blacklist()  # Token blacklist karo
            return Response({'message': 'Logged out!'})
        except Exception:
            return Response({'error': 'Invalid token'}, status=400)